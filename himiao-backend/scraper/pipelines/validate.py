# scraper/pipelines/validate.py
"""验证 Pipeline：过滤无效数据"""
import logging
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class ValidationPipeline:
    def process_item(self, item, spider):
        from scraper.items import InsuranceProductItem, NewsArticleItem, PDFDocumentItem

        if isinstance(item, InsuranceProductItem):
            if not item.get("product_name") or len(item["product_name"]) < 2:
                raise DropItem(f"Missing product_name: {item.get('source_url')}")
            if not item.get("insurer"):
                raise DropItem(f"Missing insurer: {item.get('source_url')}")

        elif isinstance(item, NewsArticleItem):
            title = item.get("title_zh") or item.get("title_en") or ""
            if len(title) < 5:
                raise DropItem(f"Title too short: {title!r}")

        elif isinstance(item, PDFDocumentItem):
            url = item.get("pdf_url", "")
            if not url or not url.lower().endswith(".pdf"):
                raise DropItem(f"Invalid PDF URL: {url}")

        return item
