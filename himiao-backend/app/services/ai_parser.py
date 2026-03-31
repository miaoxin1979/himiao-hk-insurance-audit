"""
app/services/ai_parser.py
─────────────────────────
本地 Ollama AI 解析服务 — 无外网搜索依赖版

架构说明：
  - 完全内网闭环，无外网搜索依赖
  - 有 PDF 链接 → 下载解析 → 喂给模型（更准确）
  - 无 PDF 链接 → 直接问 deepseek 知识库（主流产品基本都知道）
  - Ollama 跑在 Mac Mini M4 Pro 上，NAS 通过内网 IP 调用

环境变量（已在 .env 配置好）：
  MAC_IP=YOUR_MAC_IP
  OLLAMA_MODEL_NAME=deepseek-r1:32b
"""
import os
import json
import re
import logging
import httpx

logger = logging.getLogger(__name__)

MAC_IP          = os.getenv("MAC_IP", "YOUR_MAC_IP")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL_NAME", "deepseek-r1:32b")
OLLAMA_BASE_URL = f"http://{MAC_IP}:11434"
OLLAMA_TIMEOUT  = 180  # 32B模型推理较慢


def _build_prompt(insurer: str, product_name: str, product_type: str, pdf_text: str = "") -> str:
    type_hints = {
        "savings":          "储蓄分红险（IRR、回本年、非保证比例、分红实现率）",
        "medical":          "高端医疗险（年度保障上限、免赔额、保障地域、含美国与否）",
        "critical_illness": "重疾险（病种数、轻症数、多重赔付次数、保费豁免）",
        "annuity":          "年金险（起领年龄、月领金额、保证领取期、通胀挂钩）",
    }
    type_hint = type_hints.get(product_type, "保险产品")
    pdf_section = f"\n\n以下是产品说明书文字，请优先从中提取数据：\n---\n{pdf_text[:6000]}\n---" if pdf_text else ""

    return f"""你是香港保险精算数据提取专家。请提取以下产品的精算核心数据。

产品信息：
- 保险公司：{insurer}
- 产品名称：{product_name}
- 险种类型：{type_hint}{pdf_section}

请严格按以下JSON格式输出，不要输出任何其他内容：

{{
  "title_zh": "产品中文全名",
  "title_en": "Product English Name",
  "company": "{insurer}",
  "company_full": "保司法定全称",
  "currency": "USD",
  "premium_years": 5,
  "irr_20y": 5.82,
  "breakeven_year": 7,
  "loan_ltv": 90.0,
  "dividend_fulfillment_5y": 91.0,
  "max_early_exit_loss_pct": 21.0,
  "rating": "AA+",
  "content_zh": "客观精算摘要，120字以内，只写数字事实，禁止含推介语言",
  "content_en": "Same summary in English, facts only",
  "content_tw": "同内容繁体中文",
  "source_pdf_url": null,
  "specifications": {{
    "irr_10y": 3.5,
    "non_guaranteed_ratio": 62.0,
    "guaranteed_cash_value_10y": 48000,
    "total_cash_value_20y": 120000,
    "tags": [{{"zh":"储蓄险","en":"Savings","hk":"儲蓄險"}}, {{"zh":"分红型","en":"Participating","hk":"分紅型"}}],
    "features": [{{"zh":"管理权益户口","en":"Managed Equity Account","hk":"管理權益戶口"}}]
  }}
}}

规则：
1. 数字必须是数字类型，不是字符串
2. 不确定的字段填 null，不要猜测或编造
3. irr_20y 是百分比，如 5.82（不是 0.0582）
4. content_zh/content_en/content_tw 禁止出现推荐、优秀、出色等主观词汇
5. tags 和 features 必须为 [{"zh":"x","en":"y","hk":"z"}] 三语格式，hk 为繁体中文
6. 只输出JSON，禁止输出任何解释文字或```标记"""


async def parse_product_with_ollama(
    insurer: str,
    product_name: str,
    product_type: str = "savings",
    pdf_url: str = None,
) -> dict:
    # Step 1: 如有PDF链接，尝试提取文字（NAS能访问保司官网，不需要翻墙）
    pdf_text = ""
    if pdf_url:
        try:
            pdf_text = await _extract_pdf_text(pdf_url)
            logger.info(f"PDF提取成功，字符数: {len(pdf_text)}")
        except Exception as e:
            logger.warning(f"PDF提取失败，降级为纯知识库模式: {e}")

    # Step 2: 构建提示词并调用Ollama
    prompt = _build_prompt(insurer, product_name, product_type, pdf_text)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9},
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"无法连接到 Ollama（{OLLAMA_BASE_URL}）\n"
            f"请确认：① Mac Mini 已开机 ② 已运行 ollama serve ③ NAS与Mac在同一局域网"
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            f"Ollama 响应超时（{OLLAMA_TIMEOUT}秒）\n"
            f"32B模型首次推理较慢，请稍后重试。持续超时可在.env改用 deepseek-r1:14b"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Ollama 返回错误: HTTP {e.response.status_code}")

    # Step 3: 解析响应
    raw = resp.json().get("response", "")
    # deepseek-r1 有 <think>...</think> 推理过程，去掉
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.DOTALL).strip()
    json_match = re.search(r"\{[\s\S]*\}", cleaned)
    if not json_match:
        logger.error(f"无法从Ollama响应中提取JSON:\n{raw[:600]}")
        raise RuntimeError("AI 返回格式异常，请重试")

    try:
        parsed = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"AI 返回 JSON 格式有误: {e}")

    parsed = _sanitize_fields(parsed)
    parsed["ai_extracted"] = True
    parsed["is_published"] = False
    parsed["product_type"] = product_type
    return parsed


def _sanitize_fields(data: dict) -> dict:
    for f in ["irr_20y", "loan_ltv", "dividend_fulfillment_5y", "max_early_exit_loss_pct"]:
        if f in data and data[f] is not None:
            try: data[f] = float(data[f])
            except: data[f] = None
    for f in ["breakeven_year", "premium_years"]:
        if f in data and data[f] is not None:
            try: data[f] = int(float(data[f]))
            except: data[f] = None
    if isinstance(data.get("specifications"), dict):
        spec = data["specifications"]
        for k in ["irr_10y", "non_guaranteed_ratio", "guaranteed_cash_value_10y", "total_cash_value_20y"]:
            if k in spec and spec[k] is not None:
                try: spec[k] = float(spec[k])
                except: spec[k] = None
    return data


async def _extract_pdf_text(pdf_url: str) -> str:
    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HiMiaoBot/1.0)"},
    ) as client:
        resp = await client.get(pdf_url)
        resp.raise_for_status()
        pdf_bytes = resp.content

    try:
        import pdfplumber, io
        parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:20]:
                text = page.extract_text()
                if text: parts.append(text)
        return "\n".join(parts)
    except ImportError:
        pass

    try:
        import pypdf, io
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages[:20])
    except ImportError:
        pass

    return ""


async def check_ollama_health() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            model_ok = any(OLLAMA_MODEL.split(":")[0] in m for m in models)
            return {
                "status": "ok",
                "ollama_url": OLLAMA_BASE_URL,
                "available_models": models,
                "target_model": OLLAMA_MODEL,
                "model_ready": model_ok,
                "message": "Ollama 在线" if model_ok else f"请先运行: ollama pull {OLLAMA_MODEL}",
            }
    except Exception as e:
        return {
            "status": "error",
            "ollama_url": OLLAMA_BASE_URL,
            "model_ready": False,
            "message": f"无法连接到 Ollama: {e}",
        }
