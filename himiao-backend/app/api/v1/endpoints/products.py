"""
app/api/v1/endpoints/products.py — v14 前台适配
- 从主表+子表（savings_products/wholelife_products/ci_products）读取真实数据
- 储蓄险：合并子表构建 timeline（IRR 图表）、breakeven_year
- 支持 whole_life 险种过滤
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor, require_staff
from app.models.product import Product, ProductType
from app.models.product_sub import SavingsProduct, WholelifeProduct, CiProduct
from app.models.insurer_rating import InsurerRating
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

# Mac Mini Ollama（可用环境变量 MAC_IP 覆盖）
_OLLAMA_BASE = f"http://{os.getenv('MAC_IP', 'YOUR_MAC_IP')}:11434"

# 保司名 → InsurerRating.company 映射（用于合规评级 lookup）
_COMPANY_TO_RATING_KEY = {
    "aia": "AIA", "友邦": "AIA", "友邦保险": "AIA", "美国友邦": "AIA",
    "prudential": "Prudential", "保诚": "Prudential", "保诚保险": "Prudential", "英国保诚": "Prudential",
    "manulife": "Manulife", "宏利": "Manulife", "宏利人寿": "Manulife", "宏利金融": "Manulife",
    "sunlife": "Sun Life", "sun life": "Sun Life", "永明": "Sun Life", "永明金融": "Sun Life",
    "zurich": "Zurich", "苏黎世": "Zurich", "苏黎世保险": "Zurich",
    "hsbc": "HSBC", "汇丰": "HSBC", "汇丰人寿": "HSBC",
    "fwd": "FWD", "富卫": "FWD", "富卫人寿": "FWD",
    "yf life": "YF Life", "yflife": "YF Life", "万通": "YF Life", "万通人寿": "YF Life",
    "china life": "China Life", "chinalife": "China Life", "中国人寿": "China Life", "中国人寿海外": "China Life",
    "boc life": "BOC Life", "boclife": "BOC Life", "中银人寿": "BOC Life",
    "axa": "AXA", "安盛": "AXA", "安盛保险": "AXA",
    "ctflife": "CTFLife", "ctf life": "CTFLife", "周大福人寿": "CTFLife",
}


def _get_insurer_rating(db: Session, company: Optional[str]) -> Optional[dict]:
    """从 InsurerRating 表获取合规评级，返回 {rating, agency, source_url}"""
    if not company or not company.strip():
        return None
    key = _COMPANY_TO_RATING_KEY.get(company.strip().lower()) or company.strip()
    r = db.query(InsurerRating).filter(InsurerRating.company == key).first()
    if not r:
        return None
    return {"rating": r.rating, "agency": r.agency, "source_url": r.source_url}


router = APIRouter(
    prefix="/products",
    tags=["📋 产品管理"],
)


def _resolve_i18n_tags(raw: list, lang: str = "cn") -> list:
    """
    解析 tags/features，支持两种格式：
    - 旧：["管理权益户口", "含人民币"] → 返回按 lang 选取
    - 新：[{"zh":"x","en":"y","hk":"z"}] → 返回按 lang 选取的字符串数组
    lang: cn|hk|en
    """
    if not raw:
        return []
    key = "zh" if lang in ("cn", "zh") else "hk" if lang == "hk" else "en"
    out = []
    for item in raw:
        if isinstance(item, dict):
            v = item.get(key) or item.get("zh") or item.get("en") or item.get("hk")
            if v:
                out.append(str(v))
        elif isinstance(item, str):
            out.append(item)  # 旧格式：直接返回，前端有 fallback
    return out


def _pick_content(content_zh=None, content_en=None, content_tw=None, lang: str = "cn"):
    """按语言选取 content"""
    if lang == "en" and content_en:
        return content_en
    if lang == "hk" and content_tw:
        return content_tw
    return content_zh


def check_geo_block(request: Request) -> None:
    """
    Geo 拦截检查（NAS MVP 阶段跳过）
    上云后取消注释 MAINLAND_BLOCK 逻辑
    """
    pass


def _build_timeline_from_savings(s: SavingsProduct) -> dict:
    """从 savings_products 子表构建 audit_data.timeline（前端 IRR 图表用）"""
    timeline: dict[str, dict[str, float]] = {}

    def _gcv(yr: int) -> float:
        if yr <= 4:
            return 0.0
        if yr == 5:
            return s.gcv_y5 or 0
        if yr <= 10:
            g5, g10 = s.gcv_y5 or 0, s.gcv_y10 or 0
            return g5 + (g10 - g5) * (yr - 5) / 5
        if yr <= 20:
            g10, g20 = s.gcv_y10 or 0, s.gcv_y20 or 0
            return g10 + (g20 - g10) * (yr - 10) / 10
        if yr <= 30:
            g20, g30 = s.gcv_y20 or 0, s.gcv_y30 or 0
            return g20 + (g30 - g20) * (yr - 20) / 10
        return s.gcv_y30 or 0

    sv_map = {
        1: s.sv_y1, 2: s.sv_y2, 3: s.sv_y3, 4: s.sv_y4, 5: s.sv_y5,
        6: s.sv_y6, 7: s.sv_y7, 8: s.sv_y8, 9: s.sv_y9, 10: s.sv_y10,
        15: s.sv_y15, 20: s.sv_y20, 25: s.sv_y25, 30: s.sv_y30,
    }
    for yr, sv in sv_map.items():
        if sv is not None:
            gcv = _gcv(yr)
            div_opt = max(0, sv - gcv)
            timeline[str(yr)] = {"gcv": gcv, "div_opt": div_opt}
    return timeline


def _calc_breakeven_from_savings(s: SavingsProduct) -> Optional[int]:
    """从 sv_y* 计算保证回本年（首个 sv >= 总保费 的年份）"""
    total = s.illustration_total_premium or 500000
    for yr in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30]:
        sv = getattr(s, f"sv_y{yr}", None)
        if sv is not None and sv >= total:
            return yr
    return None


def to_public(
    p: Product,
    savings: Optional[SavingsProduct] = None,
    wholelife: Optional[WholelifeProduct] = None,
    ci: Optional[CiProduct] = None,
    lang: str = "cn",
    rating_info: Optional[dict] = None,
) -> dict:
    """ORM → 前端兼容格式（主表 + 子表合并）"""
    pt = p.product_type.value if p.product_type else "savings"

    breakeven = p.breakeven_year
    timeline: dict = p.timeline_json or {}
    specifications: dict = dict(p.specifications or {})

    if savings:
        breakeven = breakeven or _calc_breakeven_from_savings(savings)
        timeline = _build_timeline_from_savings(savings)
        if savings.gcv_y10 is not None:
            specifications.setdefault("guaranteed_cash_value_10y", savings.gcv_y10)

    if wholelife:
        wl_timeline: dict[str, dict[str, float]] = {}
        for yr in [10, 15, 20, 25, 30, 35, 40, 50, 60, 70]:
            csv = getattr(wholelife, f"y{yr}_csv", None)
            gcv = getattr(wholelife, f"y{yr}_gcv", None)
            if csv is not None:
                g = gcv or 0
                wl_timeline[str(yr)] = {"gcv": g, "div_opt": max(0, csv - g)}
        if wl_timeline:
            timeline = wl_timeline

    # tags/features：优先子表 special_features_json，否则 Product.specifications（AI 入库）
    _raw_tags = (
        (savings.special_features_json or []) if savings else
        (wholelife.special_features_json or []) if wholelife else
        (ci.special_features_json or []) if ci else []
    ) or specifications.get("tags") or specifications.get("features") or []

    return {
        "id":             p.slug,
        "product_type":   pt,
        "is_published":   p.is_published,
        "is_available":   getattr(p, "is_available", None),
        "launch_year":    p.launch_year if hasattr(p, "launch_year") else None,
        "highlight":      p.highlight,
        "ai_extracted":   p.ai_extracted,
        "source_pdf_url": p.source_pdf_url,
        "meta": {
            "name":         p.title_zh,
            "name_en":      p.title_en,
            "company":      p.company,
            "company_full": p.company_full,
            "logo":         p.logo_url,
            "currency":     p.currency,
            "rating":       (rating_info.get("rating") if rating_info else None) or p.rating,
            "rating_agency":   (rating_info.get("agency") if rating_info else None),
            "rating_source_url": (rating_info.get("source_url") if rating_info else None),
            "version":      p.version,
        },
        "actuarial": {
            "premium_years":             p.premium_years or (wholelife.illustration_payment_term if wholelife else None) or (ci.illustration_payment_term if ci else None),
            "premium_annual":            p.premium_annual or (wholelife.illustration_annual_premium if wholelife else None) or (ci.illustration_annual_premium if ci else None),
            "breakeven_year":            breakeven,
            "irr_20y":                   p.irr_20y,
            "loan_ltv":                  p.loan_ltv,
            "dividend_fulfillment_5y":   p.dividend_fulfillment_5y,
            "max_early_exit_loss_pct":   p.max_early_exit_loss_pct,
            "scenarios":                 p.scenarios_json or {},
            "annual_limit_hkd":          p.annual_limit_hkd,
            "deductible_min":            p.deductible_min,
            "covered_conditions_count":  p.covered_conditions_count or (ci.severe_ci_count if ci else None),
            "multi_pay":                 p.multi_pay if p.multi_pay is not None else (
                ((ci.cancer_multi_pay is not None and ci.cancer_multi_pay > 1) or
                 (ci.heart_stroke_multi_pay is not None and ci.heart_stroke_multi_pay > 1))
                if ci else None
            ),
        },
        "audit_data": {"timeline": timeline},
        "scores":         p.scores_json or {},
        "specifications": specifications,
        "content_zh":     p.content_zh,
        "content_en":     getattr(p, "content_en", None),
        "content_tw":     getattr(p, "content_tw", None),
        "content":        _pick_content(p.content_zh, getattr(p, "content_en", None), getattr(p, "content_tw", None), lang),
        "tags":           _resolve_i18n_tags(_raw_tags, lang),
        "tags_raw":       _raw_tags,
        "features":       _resolve_i18n_tags(_raw_tags, lang),
    }


@router.get(
    "",
    summary="获取产品列表",
    description="""
获取所有已发布的保险产品（公开接口，无需登录）。

**支持过滤参数：**
- `type`：险种类型，可选 `savings`（储蓄险）/ `whole_life`（终身寿险）/ `medical`（医疗险）/ `critical_illness`（重疾险）/ `annuity`（年金险）
- `company`：保司名称过滤，如 `AIA`、`Prudential`
- `currency`：币种过滤，如 `USD`、`HKD`
- `highlight`：仅显示编辑精选产品
- `sort`：排序方式，`name`（产品名 A-Z，默认）或 `created`（最新创建）

**注意：** 不提供按 IRR 等收益指标默认排序（监管合规要求），如需排序请前端处理。
    """,
)
def list_products(
    request: Request,
    type:         Optional[str]  = Query(None, description="险种: savings|whole_life|medical|critical_illness|annuity"),
    company:      Optional[str]  = Query(None, description="保司名称，如 AIA"),
    currency:     Optional[str]  = Query(None, description="币种：USD 或 HKD"),
    highlight:    Optional[bool] = Query(None, description="仅返回编辑精选"),
    sort:         Optional[str]  = Query(None, description="排序：name（默认）或 created"),
    is_published: Optional[bool] = Query(None, description="发布状态过滤（管理后台用）：true=已发布 false=草稿 不传=已发布"),
    lang:         Optional[str]  = Query("cn", description="语言：cn(简体)|hk(繁体)|en(英文)，影响 tags/content"),
    db: Session = Depends(get_db),
):
    # ── 判断请求方是否为管理员（带有效 Bearer Token）──────────
    # 管理员可通过 is_published 参数查看草稿；C端公开接口默认只返回已发布
    import logging
    auth_header = request.headers.get("Authorization", "")
    is_admin_request = auth_header.startswith("Bearer ") and len(auth_header) > 10

    # 只查询当前 enum 支持的险种，防止 DB 里的历史数据（如 medical）导致 enum 反序列化失败
    valid_types = list(ProductType)

    if is_admin_request:
        if is_published is not None:
            q = db.query(Product).filter(
                Product.is_published == is_published,
                Product.product_type.in_(valid_types),
            )
        else:
            q = db.query(Product).filter(Product.product_type.in_(valid_types))
    else:
        q = db.query(Product).filter(
            Product.is_published == True,
            Product.product_type.in_(valid_types),
        )

    if type:
        try:
            pt = ProductType(type)
            q = q.filter(Product.product_type == pt)
        except ValueError:
            raise HTTPException(400, f"无效的险种类型: {type}，可选值: {[e.value for e in ProductType]}")

    if company:
        q = q.filter(Product.company == company)
    if currency:
        q = q.filter(Product.currency == currency)
    if highlight is not None:
        q = q.filter(Product.highlight == highlight)

    # 铁律：默认按产品名称排序（禁止默认按收益指标排序）
    allowed_sorts = {"created": Product.id}
    sort_col = allowed_sorts.get(sort or "created", Product.id)
    products = q.order_by(sort_col).all()

    # 批量拉取子表数据（savings / wholelife / ci）
    savings_map: dict[int, SavingsProduct] = {}
    wholelife_map: dict[int, WholelifeProduct] = {}
    ci_map: dict[int, CiProduct] = {}
    savings_ids = [p.id for p in products if p.product_type == ProductType.SAVINGS]
    wholelife_ids = [p.id for p in products if p.product_type == ProductType.WHOLE_LIFE]
    ci_ids = [p.id for p in products if p.product_type == ProductType.CRITICAL_ILLNESS]
    if savings_ids:
        for r in db.query(SavingsProduct).filter(SavingsProduct.product_id.in_(savings_ids)).all():
            savings_map[r.product_id] = r
    if wholelife_ids:
        for r in db.query(WholelifeProduct).filter(WholelifeProduct.product_id.in_(wholelife_ids)).all():
            wholelife_map[r.product_id] = r
    if ci_ids:
        for r in db.query(CiProduct).filter(CiProduct.product_id.in_(ci_ids)).all():
            ci_map[r.product_id] = r

    _lang = "cn" if not lang or lang not in ("cn", "hk", "en") else lang
    # 批量解析保司评级（合规：来自 InsurerRating 官方披露）
    rating_cache: dict[str, dict] = {}
    for p in products:
        c = (p.company or "").strip()
        if c and c not in rating_cache:
            rating_cache[c] = _get_insurer_rating(db, c) or {}
    return [
        to_public(
            p,
            savings=savings_map.get(p.id),
            wholelife=wholelife_map.get(p.id),
            ci=ci_map.get(p.id),
            lang=_lang,
            rating_info=rating_cache.get((p.company or "").strip()) or None,
        )
        for p in products
    ]


@router.get(
    "/ai-health",
    summary="[管理] 检查Ollama状态",
)
def ai_health(_: User = Depends(require_staff)):
    """检查本地Ollama服务是否在线"""
    import httpx
    try:
        resp = httpx.get(f"{_OLLAMA_BASE}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            has_deepseek = any("deepseek" in m.get("name","") for m in models)
            return {
                "status": "ok",
                "model_ready": has_deepseek,
                "models": [m.get("name") for m in models],
                "message": "Ollama在线" if has_deepseek else "Ollama在线但未找到deepseek模型"
            }
    except Exception as e:
        return {"status": "error", "model_ready": False, "message": f"无法连接Ollama: {str(e)}"}


@router.post(
    "/ai-parse",
    summary="[管理] AI智能填入产品数据",
)
def ai_parse(
    body: dict,
    _: User = Depends(require_editor),
):
    """调用本地Ollama deepseek模型解析保险产品精算数据"""
    import httpx, json, re

    insurer      = body.get("insurer", "")
    product_name = body.get("product_name", "")
    product_type = body.get("product_type", "savings")

    type_hints = {
        "savings": "储蓄分红险，重点字段：irr_20y(20年内部回报率%)、breakeven_year(保证回本年)、dividend_fulfillment_5y(近5年分红实现率%)、loan_ltv(保单贷款成数%)、max_early_exit_loss_pct(第3年退保损失%)",
        "medical": "医疗险，重点字段：annual_limit_hkd(年度赔付上限HKD)、deductible_min(免赔额HKD)、coverage_region(保障地域)、network_size(直付医院数量)",
        "critical": "重疾险，重点字段：covered_conditions_count(涵盖重疾病种数)、early_stage_conditions(早期/轻症病种数)、multipay_times(最大理赔次数)",
        "annuity": "年金险，重点字段：annuity_start_age(起领年龄)、guaranteed_period_years(保证领取期年数)、irr_20y(20年IRR%)",
    }
    hint = type_hints.get(product_type, type_hints["savings"])

    prompt = f"""你是香港保险精算专家，熟悉香港市场所有主流保险产品的公开披露数据。

请根据你的知识，提取以下香港保险产品的客观精算数据：
保司：{insurer}
产品名称：{product_name}
险种：{product_type}（{hint}）

重要说明：
- 只填写你确定知道的数据，不确定的填null
- 数据必须来自保司官方披露，不得捏造
- 所有百分比填数字（如5.82，不是5.82%）
- 这是{insurer}在香港销售的正式保险产品

只返回JSON，不要任何解释或思考过程：
{{
  "title_zh": "{product_name}的中文全称",
  "title_en": "{product_name}的英文全称",
  "company": "{insurer}简称",
  "company_full": "{insurer}香港法定全称",
  "currency": "USD或HKD",
  "premium_years": 缴费年期数字或null,
  "irr_20y": 20年IRR百分比数字或null,
  "breakeven_year": 保证回本年数字或null,
  "dividend_fulfillment_5y": 近5年分红实现率百分比或null,
  "loan_ltv": 保单贷款成数百分比或null,
  "max_early_exit_loss_pct": 早期退保最大损失百分比或null,
  "annual_limit_hkd": 医疗险年度赔付上限或null,
  "covered_conditions_count": 重疾险病种数或null,
  "annuity_start_age": 年金起领年龄或null,
  "launch_year": 产品在香港上市年份数字如2023或null,
  "is_available": true如果目前仍在售否则false,
  "content_zh": "基于官方披露的客观精算说明，2-3句话"
}}"""

    try:
        resp = httpx.post(
            f"{_OLLAMA_BASE}/api/generate",
            json={
                "model": "deepseek-r1:14b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                }
            },
            timeout=120,
        )
        if resp.status_code != 200:
            raise Exception(f"Ollama返回错误: {resp.status_code}")

        raw = resp.json().get("response", "")

        # 去掉deepseek-r1的思考过程<think>...</think>
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

        # 提取JSON
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not match:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise Exception("AI返回格式无法解析")

        data = json.loads(match.group())
        return {"ok": True, "data": data}

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"AI返回JSON解析失败: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"AI解析失败: {str(e)}")


@router.post(
    "/ai-parse-pdf",
    summary="[管理] AI智能填入（上传PDF，base64编码）",
)
def ai_parse_pdf(
    body: dict,
    _: User = Depends(require_editor),
):
    """
    接收 base64 编码的 PDF 文件 → 提取文字 → 调用Ollama解析精算数据
    body: {insurer, product_name, product_type, pdf_base64}
    insurer/product_name 可留空：有 PDF 时 AI 会从文本中自动识别保司和产品（支持综合 PDF 多保司场景）
    """
    import httpx, json, re, io, base64

    insurer      = body.get("insurer", "")
    product_name = body.get("product_name", "")
    product_type = body.get("product_type", "savings")
    pdf_b64      = body.get("pdf_base64", "")

    if not pdf_b64:
        raise HTTPException(400, "pdf_base64 不能为空")

    try:
        pdf_bytes = base64.b64decode(pdf_b64)
    except Exception:
        raise HTTPException(400, "pdf_base64 格式不正确")

    if len(pdf_bytes) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(400, "PDF 文件不能超过 20MB")

    # 提取 PDF 文字
    pdf_text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            parts = [p.extract_text() for p in pdf.pages[:20] if p.extract_text()]
            pdf_text = "\n".join(parts)
    except ImportError:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages[:20])
        except ImportError:
            raise HTTPException(500, "服务器未安装 pdfplumber / pypdf，无法解析 PDF")

    if not pdf_text.strip():
        raise HTTPException(422, "PDF 无法提取文字（可能是扫描图片格式），请尝试提供 URL 方式")

    type_hints = {
        "savings": "储蓄分红险（IRR、回本年、非保证比例、分红实现率）",
        "critical_illness": "重疾险（病种数、轻症数、多重赔付次数、保费豁免）",
        "whole_life": "终身寿险（保额、现金价值、分红实现率）",
    }
    hint = type_hints.get(product_type, "保险产品")

    # 用户未填保司/产品时：让 AI 从 PDF 文本中自动识别（支持综合 PDF 多保司）
    auto_detect = not insurer or not product_name
    if auto_detect:
        prompt = f"""你是香港保险精算数据提取专家。以下是一份保险产品说明书文字（可能包含多个保司/产品，请识别第一个出现的主要产品）。

请：1) 从文本中识别保险公司名称（company）和法定全称（company_full）；2) 识别产品名称；3) 提取精算核心数据。
险种类型：{hint}

以下是产品说明书文字：
---
{pdf_text[:8000]}
---

请严格按以下JSON格式输出，只输出JSON，禁止其他内容。若文本中有多个保司，取第一个主要产品的信息：
{{
  "title_zh": "产品中文全名",
  "title_en": "Product English Name",
  "company": "保司英文简称（如 AIA/Prudential）",
  "company_full": "保司法定全称",
  "currency": "USD",
  "premium_years": 5,
  "irr_20y": 5.82,
  "breakeven_year": 7,
  "loan_ltv": 90.0,
  "dividend_fulfillment_5y": 91.0,
  "max_early_exit_loss_pct": 21.0,
  "covered_conditions_count": null,
  "launch_year": 2023,
  "is_available": true,
  "content_zh": "客观精算摘要，2-3句话，只写数字事实，禁止含推介语言"
}}

规则：
1. 数字必须是数字类型，不是字符串
2. 不确定的字段填 null，不要猜测或编造
3. irr_20y 是百分比，如 5.82（不是 0.0582）
4. 只输出JSON，禁止输出任何解释文字"""
    else:
        prompt = f"""你是香港保险精算数据提取专家。请从以下产品说明书文字中提取精算核心数据。

产品信息：
- 保险公司：{insurer}
- 产品名称：{product_name}
- 险种类型：{hint}

以下是产品说明书文字，请优先从中提取数据：
---
{pdf_text[:6000]}
---

请严格按以下JSON格式输出，不要输出任何其他内容：
{{
  "title_zh": "产品中文全名",
  "title_en": "Product English Name",
  "company": "{insurer}简称",
  "company_full": "保司法定全称",
  "currency": "USD",
  "premium_years": 5,
  "irr_20y": 5.82,
  "breakeven_year": 7,
  "loan_ltv": 90.0,
  "dividend_fulfillment_5y": 91.0,
  "max_early_exit_loss_pct": 21.0,
  "covered_conditions_count": null,
  "launch_year": 2023,
  "is_available": true,
  "content_zh": "客观精算摘要，2-3句话，只写数字事实，禁止含推介语言"
}}

规则：
1. 数字必须是数字类型，不是字符串
2. 不确定的字段填 null，不要猜测或编造
3. irr_20y 是百分比，如 5.82（不是 0.0582）
4. 只输出JSON，禁止输出任何解释文字"""

    try:
        resp = httpx.post(
            f"{_OLLAMA_BASE}/api/generate",
            json={
                "model": "deepseek-r1:14b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9},
            },
            timeout=180,
        )
        if resp.status_code != 200:
            raise Exception(f"Ollama返回错误: {resp.status_code}")

        raw = resp.json().get("response", "")
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL) or re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise Exception("AI返回格式无法解析")

        data = json.loads(match.group())
        return {"ok": True, "data": data, "pdf_chars": len(pdf_text)}

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"AI返回JSON解析失败: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"AI解析失败: {str(e)}")


@router.get(
    "/{slug}",
    summary="获取单个产品详情",
    description="根据产品 slug（唯一标识符）获取完整的产品详情，包含精算数据、审计评语和评分。",
)
def get_product(
    slug: str,
    request: Request,
    lang: Optional[str] = Query("cn", description="语言：cn|hk|en，影响 tags/content"),
    db: Session = Depends(get_db),
):
    auth_header = request.headers.get("Authorization", "")
    is_admin = auth_header.startswith("Bearer ") and len(auth_header) > 10
    q = db.query(Product).filter(Product.slug == slug)
    if not is_admin:
        q = q.filter(Product.is_published == True)
    p = q.first()
    if not p:
        raise HTTPException(404, "产品不存在或未发布")

    savings = wholelife = ci = None
    if p.product_type == ProductType.SAVINGS:
        savings = db.query(SavingsProduct).filter(SavingsProduct.product_id == p.id).first()
    elif p.product_type == ProductType.WHOLE_LIFE:
        wholelife = db.query(WholelifeProduct).filter(WholelifeProduct.product_id == p.id).first()
    elif p.product_type == ProductType.CRITICAL_ILLNESS:
        ci = db.query(CiProduct).filter(CiProduct.product_id == p.id).first()

    _lang = "cn" if not lang or lang not in ("cn", "hk", "en") else lang
    rating_info = _get_insurer_rating(db, p.company)
    return to_public(p, savings=savings, wholelife=wholelife, ci=ci, lang=_lang, rating_info=rating_info)


@router.post(
    "",
    response_model=ProductOut,
    status_code=201,
    summary="[管理] 新建产品",
    description="创建新的保险产品条目。需要管理员 JWT Token。新建产品默认为未发布状态，需要手动审核发布。",
)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Product).filter(Product.slug == body.slug).first():
        raise HTTPException(400, f"slug 已存在: {body.slug}")
    p = Product(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put(
    "/{slug}",
    response_model=ProductOut,
    summary="[管理] 全量更新产品",
    description="覆盖更新产品所有字段。需要管理员 JWT Token。",
)
def update_product(
    slug: str,
    body: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(Product.slug == slug).first()
    if not p:
        raise HTTPException(404, "产品不存在")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.patch(
    "/{slug}",
    response_model=ProductOut,
    summary="[管理] 部分更新产品（含审核发布）",
    description="""
部分更新产品字段。常用于：
- 审核通过后将 `is_published` 改为 `true` 以上线产品
- 修改单个精算数据字段（如更新 IRR）
- AI 填表后人工校正数据

需要管理员 JWT Token。
    """,
)
def patch_product(
    slug: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(Product.slug == slug).first()
    if not p:
        raise HTTPException(404, "产品不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete(
    "/{slug}",
    status_code=204,
    summary="[管理] 删除产品",
    description="永久删除产品。此操作不可撤销，请谨慎操作。需要管理员 JWT Token。",
)
def delete_product(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(Product.slug == slug).first()
    if not p:
        raise HTTPException(404, "产品不存在")
    db.delete(p)
    db.commit()


@router.post(
    "/bulk-publish",
    status_code=200,
    summary="[管理] 批量审核发布",
    description="一次性将多个产品设为已发布状态。适用于 AI 批量填表 + 人工审核完成后的批量上线操作。需要管理员 JWT Token。",
)
def bulk_publish(
    slugs: list[str],
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    updated = db.query(Product).filter(Product.slug.in_(slugs)).all()
    for p in updated:
        p.is_published = True
    db.commit()
    return {"published": len(updated), "slugs": [p.slug for p in updated]}

