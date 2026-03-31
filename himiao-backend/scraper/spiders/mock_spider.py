import scrapy
from datetime import datetime, timezone
from scraper.items import NewsArticleItem

class MockSpider(scrapy.Spider):
    name = "mock_spider"
    start_urls = ["data:,"]

    def parse(self, response):
        yield NewsArticleItem(
            source_url="http://example.com/mock-news-2026-v6-success",
            source_name="HKIA (Mock)",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            title_zh="重磅：香港保险业发布 2026 分红险指引 (V6 最终验证)",
            content_zh="香港保险业监管局今日正式发布了关于分红险的最新指导方针，要求所有保险公司在披露分红实现率时必须更加透明。此项规定旨在保护投保人利益，并促进香港保险市场的长期稳健发展。业内人士普遍认为，这将大幅减少销售误导现象。",
            category="policy",
            published_at="2026-02-23",
            tags=["HKIA", "监管", "分红险", "指引"],
        )
