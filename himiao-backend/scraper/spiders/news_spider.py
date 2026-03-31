# scraper/spiders/news_spider.py
"""
港险市场资讯爬虫
来源：HKIA（保险业监管局）、HKMA、MPF 官方公告
合规新闻源，无版权风险
"""
import re
import scrapy
from datetime import datetime, timezone
from scraper.items import NewsArticleItem


class HKIANewsSpider(scrapy.Spider):
    """香港保险业监管局 — 最新通告/指引"""
    name = "hkia_news"
    allowed_domains = ["ia.org.hk"]
    start_urls = [
        "https://www.ia.org.hk/en/legislative_framework/circulars/life_insurance.html",
        "https://www.ia.org.hk/tc/legislative_framework/circulars/life_insurance.html",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 4.0}

    def parse(self, response):
        is_tc = "/tc/" in response.url
        lang = "hk" if is_tc else "en"
        now = datetime.now(timezone.utc).isoformat()

        rows = response.css("table tr, .circular-item, li.list-item")
        for row in rows:
            title = row.css("a::text, td:nth-child(2)::text").get("").strip()
            link  = row.css("a::attr(href)").get("")
            date  = row.css("td:first-child::text, .date::text").get("").strip()

            if not title or len(title) < 5:
                continue

            full_url = response.urljoin(link) if link else response.url

            item = NewsArticleItem(
                source_url   = full_url,
                source_name  = "HKIA",
                scraped_at   = now,
                title        = title if lang == "hk" else None,
                title_en     = title if lang == "en" else None,
                category     = "policy",
                published_at = date,
                tags         = ["HKIA", "监管", "寿险"],
            )

            # 跟进详情页获取正文后再 yield
            if link and link.endswith(".html"):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_detail,
                    meta={"item": item, "lang": lang},
                )
            else:
                # 没有详情页，直接 yield（无正文）
                yield item

    def parse_detail(self, response):
        item = response.meta["item"]
        lang = response.meta["lang"]
        body = " ".join(response.css(
            ".content p::text, article p::text, .main-content p::text"
        ).getall()).strip()
        if lang == "hk":
            item["content_tw"] = body[:3000] if body else ""
        else:
            item["content_en"] = body[:3000] if body else ""
        item["excerpt"] = body[:200] if body else ""
        yield item


class MPFNewsSpider(scrapy.Spider):
    """强积金管理局 — 市场资讯（与香港保险相关）"""
    name = "mpf_news"
    allowed_domains = ["mpfa.org.hk"]
    start_urls = [
        "https://www.mpfa.org.hk/en/information-centre/news-and-events",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 3.5}

    def parse(self, response):
        now = datetime.now(timezone.utc).isoformat()
        articles = response.css(".news-item, .event-item, article")

        for a in articles:
            title    = a.css("h2::text, h3::text, .title::text").get("").strip()
            link     = a.css("a::attr(href)").get("")
            date_str = a.css(".date::text, time::attr(datetime)").get("").strip()
            excerpt  = a.css("p::text").get("").strip()

            if not title:
                continue

            yield NewsArticleItem(
                source_url   = response.urljoin(link),
                source_name  = "MPFA",
                scraped_at   = now,
                title_en     = title,
                excerpt      = excerpt[:200],
                category     = "market",
                published_at = date_str,
                tags         = ["MPF", "强积金", "市场资讯"],
            )

        # 翻页
        next_pg = response.css("a[rel='next']::attr(href), .pagination .next::attr(href)").get()
        if next_pg:
            yield response.follow(next_pg, self.parse)


class AIAHKNewsSpider(scrapy.Spider):
    """AIA 香港 — 官方新闻稿（产品发布 / 市场动态）"""
    name = "aia_hk"
    allowed_domains = ["aia.com.hk"]
    start_urls = [
        "https://www.aia.com.hk/en/about-aia/about-us/media-centre/press-releases",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 4.0}

    def parse(self, response):
        now = datetime.now(timezone.utc).isoformat()

        # AIA 新闻稿链接格式：/en/about-aia/.../press-releases/YYYY/aia-press-release-YYYYMMDD
        links = response.css("a::attr(href)").getall()
        seen = set()
        for href in links:
            if "press-release" not in href or href in seen:
                continue
            seen.add(href)
            full_url = response.urljoin(href)

            # 从 URL 提取日期
            date_match = re.search(r"(\d{8})$", href)
            date_str = date_match.group(1) if date_match else ""

            yield scrapy.Request(
                full_url,
                callback=self.parse_detail,
                meta={"url": full_url, "date": date_str, "now": now},
            )

    def parse_detail(self, response):
        now = response.meta["now"]
        date_str = response.meta["date"]

        # 提取标题
        title_en = (
            response.css("h1.page-title::text, h1.title::text, h1::text").get("").strip()
            or response.css("title::text").get("").strip().split("|")[0].strip()
        )
        if not title_en or len(title_en) < 5:
            return

        # 提取正文段落
        paragraphs = response.css(
            ".press-release-content p::text, "
            ".article-body p::text, "
            ".content-area p::text, "
            "article p::text"
        ).getall()
        body = " ".join(p.strip() for p in paragraphs if p.strip())

        # 自动分类：根据标题关键词判断
        category = _classify_aia_article(title_en)

        yield NewsArticleItem(
            source_url   = response.meta["url"],
            source_name  = "AIA 香港",
            scraped_at   = now,
            title_en     = title_en,
            excerpt      = body[:200] if body else title_en[:200],
            content_en   = body[:3000] if body else "",
            category     = category,
            published_at = date_str,
            tags         = _extract_aia_tags(title_en),
        )


def _classify_aia_article(title: str) -> str:
    """根据标题关键词自动分类"""
    title_lower = title.lower()
    if any(k in title_lower for k in ["regulat", "authority", "policy", "guideline", "circular"]):
        return "policy"
    if any(k in title_lower for k in ["launch", "new plan", "new product", "introduce", "unveil", "savings", "critical illness", "medical"]):
        return "market"
    if any(k in title_lower for k in ["award", "rank", "no.1", "number one", "leading"]):
        return "market"
    if any(k in title_lower for k in ["warning", "fraud", "scam", "alert", "caution"]):
        return "alert"
    return "market"  # AIA 新闻稿默认归 market


def _extract_aia_tags(title: str) -> list:
    """从标题提取标签"""
    tags = ["AIA", "AIA香港"]
    title_lower = title.lower()
    keyword_map = {
        "savings": "储蓄险",
        "critical illness": "重疾险",
        "medical": "医疗险",
        "annuity": "年金险",
        "mpf": "强积金",
        "award": "获奖",
        "market": "市场数据",
    }
    for en, zh in keyword_map.items():
        if en in title_lower:
            tags.append(zh)
    return tags[:5]
