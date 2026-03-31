# scraper/spiders/aia_spider.py
"""
AIA Hong Kong 产品页爬虫
目标：抓取储蓄分红险产品列表 + 计划书 PDF 链接
"""
import re
import scrapy
from datetime import datetime, timezone
from scraper.items import InsuranceProductItem, PDFDocumentItem


class AIASpider(scrapy.Spider):
    name = "aia_hk"
    allowed_domains = ["aia.com.hk"]
    start_urls = [
        "https://www.aia.com.hk/zh-hk/individual/savings-and-investments.html",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3.0,
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    def parse(self, response):
        """解析产品列表页，提取每个产品的详情链接"""
        self.logger.info(f"Parsing AIA product list: {response.url}")

        # AIA 产品卡片选择器（根据实际页面结构调整）
        product_links = response.css(
            "a[href*='/individual/savings']::attr(href), "
            "a[href*='/individual/life-protection']::attr(href), "
            ".product-card a::attr(href), "
            ".product-item a::attr(href)"
        ).getall()

        seen = set()
        for link in product_links:
            full_url = response.urljoin(link)
            if full_url not in seen:
                seen.add(full_url)
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_product,
                    meta={"insurer": "AIA"},
                )

        # 翻页
        next_page = response.css("a.pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        """解析单个产品详情页"""
        insurer = response.meta.get("insurer", "AIA")
        now = datetime.now(timezone.utc).isoformat()

        # 产品名称
        name = (
            response.css("h1.product-title::text, h1.hero__title::text, h1::text").get("").strip()
            or response.css("title::text").get("").split("|")[0].strip()
        )

        # 货币
        currency = "HKD"
        if re.search(r"USD|美元|美金", response.text):
            currency = "USD"

        # 查找 PDF 链接（计划书）
        pdf_links = response.css(
            "a[href$='.pdf']::attr(href), "
            "a[href*='download']::attr(href), "
            "a[href*='brochure']::attr(href), "
            "a[href*='plan']::attr(href)"
        ).getall()
        pdf_urls = [response.urljoin(u) for u in pdf_links if ".pdf" in u.lower()]

        item = InsuranceProductItem(
            source_url   = response.url,
            insurer      = insurer,
            scraped_at   = now,
            product_name = name,
            currency     = currency,
            pdf_urls     = pdf_urls,
            product_type = self._detect_type(response.text),
            raw_html     = response.css("main, .product-content").get(""),
        )
        yield item

        # 对每个 PDF 单独发出下载任务
        for pdf_url in pdf_urls[:2]:  # 最多取前2个
            yield PDFDocumentItem(
                pdf_url      = pdf_url,
                insurer      = insurer,
                product_name = name,
                scraped_at   = now,
            )

    def _detect_type(self, text: str) -> str:
        if re.search(r"重疾|危疾|Critical Illness", text):
            return "ci"
        if re.search(r"定期|Term", text):
            return "term"
        return "whole_life"
