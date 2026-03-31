# scraper/pipelines/database.py
"""
Database Pipeline：将爬取结果写入 SQLite（复用 FastAPI 的 ORM）
爬虫和后端共用同一个数据库，产品数据直接可被 API 读取
"""
import logging
import sys
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DatabasePipeline:

    def open_spider(self, spider):
        # 把项目根目录加入 path，复用 app/ 的 ORM 模型
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if root not in sys.path:
            sys.path.insert(0, root)

        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(root, ".env"))

            from app.db.base import Base
            from app.db.session import engine, SessionLocal
            Base.metadata.create_all(bind=engine)
            self.SessionLocal = SessionLocal
            self.enabled = True
            logger.info("DatabasePipeline: connected to DB")
        except Exception as e:
            logger.warning(f"DatabasePipeline disabled (DB not available): {e}")
            self.enabled = False

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        if not self.enabled:
            return item

        from scraper.items import InsuranceProductItem, NewsArticleItem

        if isinstance(item, InsuranceProductItem):
            self._save_product(item)
        elif isinstance(item, NewsArticleItem):
            self._save_article(item)

        return item

    def _save_product(self, item):
        from app.models.product import Product
        db = self.SessionLocal()
        try:
            # slug = 保司简称_产品名缩写
            slug = self._make_slug(item.get("insurer", ""), item.get("product_name", ""))

            existing = db.query(Product).filter(Product.slug == slug).first()
            if existing:
                # 更新爬取到的新数据（不覆盖人工精算数据）
                if item.get("pdf_urls"):
                    existing.logo_url = existing.logo_url  # 保持不变
                logger.info(f"Product already exists, skipping: {slug}")
                return

            p = Product(
                slug         = slug,
                name         = item.get("product_name", ""),
                company      = item.get("insurer", ""),
                currency     = item.get("currency", "HKD"),
                product_type = item.get("product_type", "whole_life"),
                is_published = True,  # 爬取的先不发布，等人工审核
            )
            db.add(p)
            db.commit()
            logger.info(f"Saved new product (unpublished): {slug}")

        except Exception as e:
            db.rollback()
            logger.error(f"DB error saving product: {e}")
        finally:
            db.close()

    def _save_article(self, item):
        from app.models.article import Article
        db = self.SessionLocal()
        try:
            title_zh = item.get("title_zh") or item.get("title_zh") or ""
            slug = self._make_slug(item.get("source_name", "news"), title_zh)

            if db.query(Article).filter(Article.slug == slug).first():
                return  # 已存在

            a = Article(
                slug         = slug,
                title_zh     = title_zh,
                title_tw     = item.get("title_tw"),
                title_en     = item.get("title_en"),
                excerpt      = item.get("excerpt", "")[:200],
                content_zh   = item.get("content_zh", ""),
                content_tw   = item.get("content_tw", ""),
                content_en   = item.get("content_en", ""),
                source_url   = item.get("source_url"),
                cover_url    = item.get("cover_url"),
                category     = item.get("category", "market"),
                tags         = item.get("tags", []),
                author       = item.get("source_name", "HiMiao 精算团队"),
                is_published = False,  # 进后台待审核队列，人工确认后发布
            )
            db.add(a)
            db.commit()
            logger.info(f"Saved article: {slug}")

        except Exception as e:
            db.rollback()
            logger.error(f"DB error saving article: {e}")
        finally:
            db.close()

    def _make_slug(self, prefix: str, name: str) -> str:
        import re
        combined = f"{prefix}_{name}".lower()
        slug = re.sub(r"[^\w\-]", "_", combined)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug[:64]
