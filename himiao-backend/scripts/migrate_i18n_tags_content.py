#!/usr/bin/env python3
"""
scripts/migrate_i18n_tags_content.py
──────────────────────────────────
一次性迁移：将现有产品的 标签 和 精算辣评 统一为 zh/en/hk 三语

1. 标签：special_features_json / Product.specifications.tags|features
   - 旧格式 ["管理权益户口", "含人民币"] → 新格式 [{"zh":"x","en":"y","hk":"z"}]

2. 精算辣评：content_zh → 补齐 content_en、content_tw（通过 Ollama 翻译）

用法：
  cd himiao-backend
  python scripts/migrate_i18n_tags_content.py [--dry-run]

需要 Ollama 在线（MAC_IP 指向的 Mac Mini）
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _is_old_format_tags(arr) -> bool:
    """判断是否为旧格式（纯字符串数组）"""
    if not arr or not isinstance(arr, list):
        return False
    return len(arr) > 0 and isinstance(arr[0], str)


def _has_cjk(s: str) -> bool:
    """是否包含中日韩字符"""
    if not s or not isinstance(s, str):
        return False
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def fix_i18n_tags(raw: list, translator, dry_run: bool) -> tuple[list, bool]:
    """
    已是 [{"zh","en","hk"}] 格式但 en/hk 仍为中文时，重新翻译填充。
    返回 (新列表, 是否有改动)。
    """
    if not raw or not isinstance(raw, list) or not isinstance(raw[0], dict):
        return raw, False
    out = []
    changed = False
    for item in raw:
        if not isinstance(item, dict):
            out.append(item)
            continue
        zh = (item.get("zh") or "").strip()
        en = (item.get("en") or "").strip()
        hk = (item.get("hk") or "").strip()
        need_en = zh and _has_cjk(en)
        need_hk = zh and _has_cjk(hk)
        if need_en:
            t = translator.translate_text(zh, "en")
            if t:
                en = t
                changed = True
        if need_hk:
            t = translator.translate_text(zh, "hk")
            if t:
                hk = t
                changed = True
        out.append({"zh": zh or en or hk, "en": en or zh, "hk": hk or zh})
    return out, changed


def migrate_content(p, translator, dry_run: bool) -> int:
    """补齐 content_en、content_tw，返回更新数"""
    updated = 0
    zh = (p.content_zh or "").strip()
    if not zh:
        return 0
    if not (p.content_en or "").strip():
        en = translator.translate_text(zh, "en")
        if en:
            if not dry_run:
                p.content_en = en
            updated += 1
            log.info(f"    content_en: {en[:50]}...")
    if not (p.content_tw or "").strip():
        hk = translator.translate_text(zh, "hk")
        if hk:
            if not dry_run:
                p.content_tw = hk
            updated += 1
            log.info(f"    content_tw: {hk[:50]}...")
    return updated


def migrate_tags_in_sub(record, translator, dry_run: bool) -> int:
    """子表 special_features_json 迁移"""
    raw = record.special_features_json
    if not raw or not isinstance(raw, list) or not raw:
        return 0
    if not _is_old_format_tags(raw):
        # 已是新格式：若 en/hk 仍为中文则修补
        fixed, changed = fix_i18n_tags(raw, translator, dry_run)
        if changed and not dry_run:
            record.special_features_json = fixed
        if changed:
            log.info(f"    子表 special_features: 修补 en/hk 翻译")
        return 1 if changed else 0
    zh_list = [str(x).strip() for x in raw if x]
    if not zh_list:
        return 0
    i18n = translator.tags_to_i18n(zh_list)
    if not i18n:
        return 0
    if not dry_run:
        record.special_features_json = i18n
    log.info(f"    子表 special_features: {len(zh_list)} 条 → i18n 格式")
    return 1


def migrate_tags_in_specs(p, translator, dry_run: bool) -> int:
    """Product.specifications 中的 tags/features 迁移"""
    specs = p.specifications or {}
    tags = specs.get("tags") or specs.get("features")
    if not tags or not isinstance(tags, list) or not tags:
        return 0
    if not _is_old_format_tags(tags):
        fixed, changed = fix_i18n_tags(tags, translator, dry_run)
        if changed and not dry_run:
            merged = dict(specs)
            merged["tags"] = fixed
            merged["features"] = fixed
            p.specifications = merged
        if changed:
            log.info(f"    specifications.tags: 修补 en/hk 翻译")
        return 1 if changed else 0
    zh_list = [str(x).strip() for x in tags if x]
    if not zh_list:
        return 0
    i18n = translator.tags_to_i18n(zh_list)
    if not i18n:
        return 0
    merged = dict(specs)
    merged["tags"] = i18n
    merged["features"] = i18n
    if not dry_run:
        p.specifications = merged
    log.info(f"    specifications.tags: {len(zh_list)} 条 → i18n 格式")
    return 1


def main():
    parser = argparse.ArgumentParser(description="标签+精算辣评统一为 zh/en/hk 三语")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写库")
    args = parser.parse_args()

    from app.db.session import SessionLocal
    from app.models.product import Product, ProductType
    from app.models.product_sub import SavingsProduct, WholelifeProduct, CiProduct
    from app.services import translator as trans_mod

    trans = trans_mod
    db = SessionLocal()

    stats = {"products": 0, "content": 0, "sub_tags": 0, "spec_tags": 0}

    try:
        valid_types = [ProductType.SAVINGS, ProductType.WHOLE_LIFE, ProductType.CRITICAL_ILLNESS]
        products = db.query(Product).filter(Product.product_type.in_(valid_types)).all()
        log.info(f"共 {len(products)} 个产品，开始迁移...")

        for p in products:
            changed = False
            log.info(f"\n[{p.slug}] {p.title_zh}")

            # 1. 精算辣评
            if (p.content_zh or "").strip():
                if not p.content_en or not p.content_tw:
                    n = migrate_content(p, trans, args.dry_run)
                    if n > 0:
                        stats["content"] += n
                        changed = True

            # 2. 子表 special_features_json
            if p.product_type == ProductType.SAVINGS:
                sub = db.query(SavingsProduct).filter(SavingsProduct.product_id == p.id).first()
            elif p.product_type == ProductType.WHOLE_LIFE:
                sub = db.query(WholelifeProduct).filter(WholelifeProduct.product_id == p.id).first()
            elif p.product_type == ProductType.CRITICAL_ILLNESS:
                sub = db.query(CiProduct).filter(CiProduct.product_id == p.id).first()
            else:
                sub = None

            if sub:
                n = migrate_tags_in_sub(sub, trans, args.dry_run)
                if n > 0:
                    stats["sub_tags"] += n
                    changed = True

            # 3. Product.specifications（无子表或子表无 tags 时，AI 入库产品）
            n = migrate_tags_in_specs(p, trans, args.dry_run)
            if n > 0:
                stats["spec_tags"] += n
                changed = True

            if changed:
                stats["products"] += 1

        if not args.dry_run and (stats["content"] > 0 or stats["sub_tags"] > 0 or stats["spec_tags"] > 0):
            db.commit()
            log.info("\n✅ 已提交到数据库")
        elif args.dry_run:
            log.info("\n🔍 [dry-run] 未写入数据库")

        log.info(f"\n统计：影响 {stats['products']} 个产品 | content 补齐 {stats['content']} 次 | 子表 tags {stats['sub_tags']} 处 | specifications tags {stats['spec_tags']} 处")
    except Exception as e:
        db.rollback()
        log.error(f"❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
