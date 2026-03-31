#!/usr/bin/env python3
"""
scripts/migrate_json.py
一次性迁移脚本：将 data/products.json + data/articles.json 导入 SQLite

用法：
  cd himiao-backend
  python scripts/migrate_json.py \
    --products ../data/products.json \
    --articles ../data/articles.json

成功后可删除此脚本，前端改为从 API 拉取数据。
"""
import sys
import json
import argparse
import logging
from pathlib import Path

# 把项目根目录加入 path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def migrate_products(products_json_path: str, db):
    from app.models.product import Product

    with open(products_json_path, encoding="utf-8") as f:
        raw = json.load(f)

    # products.json 顶层可以是数组，也可以是 {"products": [...]}
    items = raw if isinstance(raw, list) else raw.get("products", [])

    created = 0
    skipped = 0
    for item in items:
        slug = item.get("id") or item.get("slug")
        if not slug:
            log.warning(f"跳过无 id 的产品: {item}")
            continue

        # 检查重复
        if db.query(Product).filter(Product.slug == slug).first():
            log.info(f"已存在，跳过: {slug}")
            skipped += 1
            continue

        meta      = item.get("meta", {})
        actuarial = item.get("actuarial", {})
        audit     = item.get("audit_data", {})
        scores    = item.get("scores", {})

        p = Product(
            slug            = slug,
            name            = meta.get("name", slug),
            name_en         = meta.get("name_en"),
            company         = meta.get("company", ""),
            company_full    = meta.get("company_full"),
            logo_url        = meta.get("logo"),
            currency        = meta.get("currency", "USD"),
            rating          = meta.get("rating"),
            product_type    = meta.get("product_type"),
            version         = meta.get("version"),
            highlight       = item.get("highlight", False),

            premium_years            = actuarial.get("premium_years"),
            premium_annual           = actuarial.get("premium_annual"),
            breakeven_year           = actuarial.get("breakeven_year"),
            irr_20y                  = actuarial.get("irr_20y"),
            loan_ltv                 = actuarial.get("loan_ltv"),
            dividend_fulfillment_5y  = actuarial.get("dividend_fulfillment_5y"),
            max_early_exit_loss_pct  = actuarial.get("max_early_exit_loss_pct"),
            scenarios_json           = actuarial.get("scenarios"),

            # audit_data.timeline → timeline_json
            timeline_json   = audit.get("timeline") or audit.get("timeline_anchors"),
            scores_json     = scores if scores else None,

            review          = item.get("review"),
        )
        db.add(p)
        created += 1
        log.info(f"  ✅ 导入产品: {slug} — {meta.get('name')}")

    db.commit()
    log.info(f"\n产品迁移完成：新增 {created}，跳过 {skipped}")


def migrate_articles(articles_json_path: str, db):
    from app.models.article import Article

    with open(articles_json_path, encoding="utf-8") as f:
        raw = json.load(f)

    items = raw if isinstance(raw, list) else raw.get("articles", [])

    created = 0
    for item in items:
        slug = item.get("id") or item.get("slug")
        if not slug:
            continue
        if db.query(Article).filter(Article.slug == slug).first():
            log.info(f"已存在，跳过: {slug}")
            continue

        a = Article(
            slug        = slug,
            title       = item.get("title", slug),
            title_hk    = item.get("title_hk"),
            title_en    = item.get("title_en"),
            excerpt     = item.get("excerpt") or item.get("desc"),
            body        = item.get("body"),
            cover_url   = item.get("cover") or item.get("cover_url"),
            category    = item.get("cat") or item.get("category"),
            tags        = item.get("tags", []),
            author      = item.get("author", "HiMiao 精算团队"),
            read_min    = item.get("read_min", 5),
            is_hot      = item.get("is_hot", False),
            is_published = item.get("is_published", True),
        )
        db.add(a)
        created += 1
        log.info(f"  ✅ 导入文章: {slug}")

    db.commit()
    log.info(f"\n文章迁移完成：新增 {created}")


def main():
    parser = argparse.ArgumentParser(description="HiMiao JSON → SQLite 迁移")
    parser.add_argument("--products", default="data/products.json")
    parser.add_argument("--articles", default="data/articles.json")
    parser.add_argument("--env",      default=".env")
    args = parser.parse_args()

    # 加载配置（确保 DATABASE_URL 生效）
    from dotenv import load_dotenv
    load_dotenv(args.env)

    from app.db.base import Base
    from app.db.session import engine, SessionLocal

    log.info("📦 初始化数据库...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if Path(args.products).exists():
            log.info(f"\n📂 迁移产品: {args.products}")
            migrate_products(args.products, db)
        else:
            log.warning(f"products.json 不存在: {args.products}")

        if Path(args.articles).exists():
            log.info(f"\n📂 迁移文章: {args.articles}")
            migrate_articles(args.articles, db)
        else:
            log.warning(f"articles.json 不存在: {args.articles}")

    except Exception as e:
        db.rollback()
        log.error(f"❌ 迁移失败: {e}")
        raise
    finally:
        db.close()

    log.info("\n✅ 全部迁移完成！")
    log.info("下一步：修改前端 fetch('data/products.json') → fetch('/api/v1/products')")


if __name__ == "__main__":
    main()
