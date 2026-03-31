# scraper/spiders/insurer_news_spiders.py
"""
港险新闻爬虫 — Google News RSS 方案
──────────────────────────────────
直连保司/监管局网站均有防爬，改用 Google News RSS 聚合新闻。

RSS 端点：
  https://news.google.com/rss/search?q={query}&hl=zh-HK&gl=HK&ceid=HK:zh-Hant
  https://news.google.com/rss/search?q={query}&hl=en-HK&gl=HK&ceid=HK:en

覆盖保司（对应 COMPANY_ALIASES 标准 key）：
  aia / prudential / manulife / fwd / hsbc / sunlife / zurich / yftlife / bocomlife

Spider 名称：google_news_hk_insurance（单一 spider，覆盖全部保司）
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlencode, quote_plus

import scrapy
from scraper.items import NewsArticleItem


# ── 查询关键词配置 ──────────────────────────────────────────────────
# 格式：(source_name, [zh_query, en_query])
INSURER_QUERIES: list[tuple[str, str, list[str]]] = [
    # (source_name,  company_key,  query_terms)
    ("AIA香港",       "aia",        ["AIA 友邦 香港保险", "AIA Hong Kong insurance"]),
    ("保诚香港",      "prudential", ["保诚 香港 保险", "Prudential Hong Kong insurance"]),
    ("宏利香港",      "manulife",   ["宏利 香港 保险", "Manulife Hong Kong insurance"]),
    ("富卫香港",      "fwd",        ["富卫 香港 保险", "FWD Hong Kong insurance"]),
    ("汇丰人寿",      "hsbc",       ["汇丰 香港 保险 人寿", "HSBC Life Hong Kong"]),
    ("永明香港",      "sunlife",    ["永明 香港 保险", "Sun Life Hong Kong insurance"]),
    ("万通保险",      "yftlife",    ["万通 保险 香港", "YF Life Hong Kong"]),
]

# 监管/市场通用关键词（补充行业动态）
MARKET_QUERIES: list[tuple[str, str, list[str]]] = [
    ("香港保监局", "hkia", ["香港保险业监管局 保险", "HKIA Hong Kong insurance authority"]),
    ("港险市场",   "market", ["香港储蓄险 分红险", "Hong Kong savings insurance dividends"]),
]


def _google_rss_url(query: str, lang: str = "zh-HK") -> str:
    """构造 Google News RSS URL"""
    if lang == "en":
        params = {"q": query, "hl": "en-HK", "gl": "HK", "ceid": "HK:en"}
    else:
        params = {"q": query, "hl": "zh-HK", "gl": "HK", "ceid": "HK:zh-Hant"}
    return f"https://news.google.com/rss/search?{urlencode(params)}"


def _parse_pub_date(date_str: str) -> str:
    """把 RSS pubDate（RFC 2822）转成 ISO 8601"""
    if not date_str:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str).isoformat()
    except Exception:
        return date_str


class GoogleNewsHKInsuranceSpider(scrapy.Spider):
    """
    Google News RSS → 港险新闻聚合
    单 spider 覆盖所有保司 + 监管关键词
    """
    name = "google_news_hk_insurance"
    allowed_domains = ["news.google.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "USER_AGENT": (
            "Mozilla/5.0 (compatible; HiMiaoBot/1.0; "
            "+https://himiao.hk)"
        ),
        "ROBOTSTXT_OBEY": False,   # Google RSS 无 robots 限制
    }

    def start_requests(self):
        now = datetime.now(timezone.utc).isoformat()
        all_queries = INSURER_QUERIES + MARKET_QUERIES

        for source_name, company_key, queries in all_queries:
            for i, q in enumerate(queries):
                lang = "en" if i % 2 == 1 else "zh"   # 奇数索引为英文查询
                url = _google_rss_url(q, lang)
                yield scrapy.Request(
                    url,
                    callback=self.parse_rss,
                    meta={
                        "source_name": source_name,
                        "company_key": company_key,
                        "lang": lang,
                        "now": now,
                    },
                    errback=self.errback,
                )

    def parse_rss(self, response):
        source_name = response.meta["source_name"]
        company_key = response.meta["company_key"]
        lang        = response.meta["lang"]
        now         = response.meta["now"]

        # Scrapy 默认把 XML 当 HTML 解析，用 response.xpath 访问 RSS
        items = response.xpath("//item")
        self.logger.info(
            f"[google_rss] {source_name} ({lang}) → {len(items)} 条"
        )

        for item in items:
            title     = item.xpath("title/text()").get("").strip()
            link      = item.xpath("link/text()").get("").strip()
            pub_date  = item.xpath("pubDate/text()").get("").strip()
            desc      = item.xpath("description/text()").get("").strip()
            source    = item.xpath("source/text()").get("").strip()  # 来源媒体名

            if not title or len(title) < 5:
                continue

            # 去除 HTML 标签（description 里有时含 <a>）
            clean_desc = re.sub(r"<[^>]+>", "", desc).strip()

            published_at = _parse_pub_date(pub_date)

            # 按语言分配标题字段
            if lang == "zh":
                yield NewsArticleItem(
                    source_url   = link,
                    source_name  = f"{source_name}·{source}" if source else source_name,
                    scraped_at   = now,
                    title_zh     = title,
                    title_tw     = title,   # Google HK RSS 返回繁体
                    excerpt      = clean_desc[:200],
                    category     = self._classify(title),
                    published_at = published_at,
                    tags         = self._tags(title, company_key),
                )
            else:
                yield NewsArticleItem(
                    source_url   = link,
                    source_name  = f"{source_name}·{source}" if source else source_name,
                    scraped_at   = now,
                    title_en     = title,
                    excerpt      = clean_desc[:200],
                    category     = self._classify(title),
                    published_at = published_at,
                    tags         = self._tags(title, company_key),
                )

    def _classify(self, title: str) -> str:
        tl = title.lower()
        if any(k in tl for k in ["监管", "规定", "指引", "circular", "regulation", "authority", "policy"]):
            return "policy"
        if any(k in tl for k in ["警告", "诈骗", "fraud", "scam", "warning", "alert"]):
            return "alert"
        return "market"

    def _tags(self, title: str, company_key: str) -> list[str]:
        # 公司标签
        company_tag_map = {
            "aia":        ["AIA", "友邦"],
            "prudential": ["保诚", "Prudential"],
            "manulife":   ["宏利", "Manulife"],
            "fwd":        ["富卫", "FWD"],
            "hsbc":       ["汇丰", "HSBC"],
            "sunlife":    ["永明", "Sun Life"],
            "yftlife":    ["万通", "YF Life"],
            "hkia":       ["保监局", "HKIA"],
            "market":     ["港险市场"],
        }
        tags = list(company_tag_map.get(company_key, [company_key]))

        # 险种标签
        tl = title.lower()
        if any(k in tl for k in ["储蓄", "savings", "分红", "dividend"]):
            tags.append("储蓄险")
        if any(k in tl for k in ["重疾", "危疾", "critical illness"]):
            tags.append("重疾险")
        if any(k in tl for k in ["医疗", "medical"]):
            tags.append("医疗险")
        if any(k in tl for k in ["irr", "收益", "回报", "return"]):
            tags.append("精算数据")
        return tags[:6]

    def errback(self, failure):
        self.logger.warning(f"[google_news] RSS 请求失败: {failure.request.url}")
