"""
app/services/ingest.py
──────────────────────
AI 解析结果 → 去重 → 入库

去重策略：
  1. 同险种 (product_type) 内匹配
  2. 保司名标准化比对（AIA / 友邦 / 友邦保险 → 同一 key）
  3. 产品名标准化后精确匹配，或前缀相似（应对版本号差异）
  4. 命中 → UPDATE；未命中 → INSERT 草稿（is_published=False）

Slug 生成：
  - 命中已有产品：保留原 slug（不改动）
  - 新产品：{company_key}_{md5(title_zh)[:8]}
"""
from __future__ import annotations

import re
import hashlib
import unicodedata
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.product import Product, ProductType

logger = logging.getLogger(__name__)


# ── 保司名标准化映射 ──────────────────────────────────────────────────
COMPANY_ALIASES: dict[str, list[str]] = {
    "aia":        ["aia", "友邦", "友邦保险", "友邦人寿", "美国友邦"],
    "prudential": ["保诚", "prudential", "英国保诚", "保诚人寿"],
    "manulife":   ["宏利", "manulife", "宏利人寿", "宏利金融"],
    "sunlife":    ["永明", "sunlife", "sun life", "永明金融"],
    "zurich":     ["苏黎世", "zurich", "苏黎世保险"],
    "hsbc":       ["汇丰", "hsbc", "汇丰人寿"],
    "fwd":        ["fwd", "富卫", "富卫人寿"],
    "bupa":       ["bupa", "保柏"],
    "metlife":    ["metlife", "大都会", "大都会人寿"],
    "chubb":      ["chubb", "安达", "ace"],
    "yftlife":    ["万通", "yf life", "yflife", "yf"],
    "bocomlife":  ["交银", "bocom", "交银人寿"],
}


def _normalize(text: str) -> str:
    """全角→半角、去空格、去标点、小写"""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower().strip()
    text = re.sub(r"[\s\-·•·\u00b7\u30fb]+", "", text)   # 去空格及各类中点
    text = re.sub(r"[（）()【】\[\]《》「」『』]", "", text)
    return text


def _company_key(company: str) -> str:
    """将保司名归一化到标准 key，未知保司返回标准化字符串"""
    norm = _normalize(company)
    for key, aliases in COMPANY_ALIASES.items():
        for alias in aliases:
            if _normalize(alias) in norm or norm in _normalize(alias):
                return key
    return norm


def _title_similar(a: str, b: str, prefix_len: int = 6) -> bool:
    """
    产品名相似性判断：
    1. 标准化后完全一致
    2. 前 prefix_len 字符相同（应对版本号/年份变化）
    """
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    # 中文产品名通常核心词在前，截取前N字符比较
    if len(na) >= prefix_len and len(nb) >= prefix_len:
        return na[:prefix_len] == nb[:prefix_len]
    return False


def find_duplicate(
    db: Session,
    product_type: ProductType,
    company: str,
    title_zh: str,
) -> Optional[Product]:
    """
    在 DB 中查找重复产品。返回第一个匹配的 Product，或 None。
    """
    ck = _company_key(company)
    existing = db.query(Product).filter(
        Product.product_type == product_type
    ).all()

    for p in existing:
        if _company_key(p.company or "") != ck:
            continue
        if _title_similar(p.title_zh or "", title_zh):
            logger.info(
                f"[ingest] 去重命中: {p.slug}  "
                f"({p.company}/{p.title_zh}) ← 输入({company}/{title_zh})"
            )
            return p

    return None


def _generate_slug(company: str, title_zh: str, db: Session) -> str:
    """生成唯一 slug：{company_key}_{title_hash8}"""
    ck = re.sub(r"[^a-z0-9]", "", _company_key(company))[:10]
    title_hash = hashlib.md5(_normalize(title_zh).encode()).hexdigest()[:8]
    base = f"{ck}_{title_hash}"
    candidate = base
    i = 2
    while db.query(Product).filter(Product.slug == candidate).first():
        candidate = f"{base}_{i}"
        i += 1
    return candidate


def _apply_parsed(p: Product, parsed: dict) -> None:
    """将 ai_parser 返回的字段写入 Product ORM 对象（只覆盖非 None 值）"""
    scalar_map = {
        "title_zh":                "title_zh",
        "title_en":                "title_en",
        "company":                 "company",
        "company_full":            "company_full",
        "currency":                "currency",
        "rating":                  "rating",
        "premium_years":           "premium_years",
        "irr_20y":                 "irr_20y",
        "breakeven_year":          "breakeven_year",
        "loan_ltv":                "loan_ltv",
        "dividend_fulfillment_5y": "dividend_fulfillment_5y",
        "max_early_exit_loss_pct": "max_early_exit_loss_pct",
        "source_pdf_url":          "source_pdf_url",
        "content_zh":              "content_zh",
        "content_en":              "content_en",
        "content_tw":              "content_tw",
        "ai_extracted":            "ai_extracted",
        # 重疾险专有
        "covered_conditions_count": "covered_conditions_count",
        "multi_pay":                "multi_pay",
    }
    for src, dst in scalar_map.items():
        val = parsed.get(src)
        if val is not None:
            setattr(p, dst, val)

    # specifications：merge，不覆盖已有非 None 值（防止 AI 乱写 null）
    specs_in = parsed.get("specifications") or {}
    existing_specs = p.specifications or {}
    merged = dict(existing_specs)
    for k, v in specs_in.items():
        if v is not None:
            merged[k] = v
    # 也把 top-level 中属于 specs 的字段合并进去
    for k in ["irr_10y", "non_guaranteed_ratio",
              "guaranteed_cash_value_10y", "total_cash_value_20y",
              "audit_note"]:
        if parsed.get(k) is not None:
            merged[k] = parsed[k]

    # tags/features：AI 若返回新格式 [{"zh":"x","en":"y","hk":"z"}] 直接使用；旧格式则翻译
    tags_in = specs_in.get("tags") or merged.get("tags") or parsed.get("tags")
    features_in = specs_in.get("features") or merged.get("features") or parsed.get("features")
    tags_final = tags_in or features_in
    if tags_final and len(tags_final) > 0:
        if isinstance(tags_final[0], dict):
            merged["tags"] = tags_final
            merged["features"] = (features_in if features_in and len(features_in) > 0 and isinstance(features_in[0], dict) else tags_final)
        else:
            try:
                from app.services.translator import tags_to_i18n
                merged["tags"] = tags_to_i18n([str(t) for t in tags_final])
                merged["features"] = merged["tags"]  # 同源
            except Exception as e:
                logger.warning(f"[ingest] 标签翻译失败，保留原格式: {e}")
                merged["tags"] = tags_final
                merged["features"] = features_in if features_in else tags_final
    elif features_in:
        if features_in and isinstance(features_in[0], dict):
            merged["features"] = features_in
            merged.setdefault("tags", features_in)
        else:
            try:
                from app.services.translator import tags_to_i18n
                merged["features"] = tags_to_i18n([str(t) for t in features_in])
                merged["tags"] = merged["features"]
            except Exception as e:
                logger.warning(f"[ingest] 标签翻译失败: {e}")
                merged["features"] = features_in
                merged.setdefault("tags", features_in)

    p.specifications = merged


def ingest_parsed_product(db: Session, parsed: dict) -> dict:
    """
    主入口：去重 + INSERT/UPDATE

    Args:
        db:     SQLAlchemy Session
        parsed: ai_parser.parse_product_with_ollama() 的返回值（含 product_type）

    Returns:
        {
          "action":       "created" | "updated",
          "product_code": str,   # slug
          "id":           int,
        }
    """
    product_type_str = parsed.get("product_type", "savings")
    try:
        product_type = ProductType(product_type_str)
    except ValueError:
        raise ValueError(
            f"无效险种类型: {product_type_str!r}，"
            f"有效值: savings / whole_life / critical_illness"
        )

    company  = parsed.get("company") or parsed.get("insurer") or ""
    title_zh = parsed.get("title_zh") or ""

    if not company or not title_zh:
        raise ValueError("parsed 数据缺少 company 或 title_zh，无法入库")

    existing = find_duplicate(db, product_type, company, title_zh)

    if existing:
        _apply_parsed(existing, parsed)
        db.commit()
        db.refresh(existing)
        logger.info(f"[ingest] UPDATE {existing.slug} ({product_type_str})")
        return {"action": "updated", "product_code": existing.slug, "id": existing.id}
    else:
        slug = _generate_slug(company, title_zh, db)
        p = Product(product_type=product_type, slug=slug)
        _apply_parsed(p, parsed)
        p.is_published = False   # 草稿，需人工审核后发布
        db.add(p)
        db.commit()
        db.refresh(p)
        logger.info(f"[ingest] INSERT {p.slug} ({product_type_str}) as draft")
        return {"action": "created", "product_code": p.slug, "id": p.id}
