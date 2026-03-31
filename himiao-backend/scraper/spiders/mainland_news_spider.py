# scraper/spiders/mainland_news_spider.py
"""
大陆可访问的港险相关资讯爬虫
──────────────────────────────
核心修复：每条新闻都跟进详情页抓取全文，解决"有标题没内容"问题。

来源：
1. 证券时报 (stcn.com)         JSON API → 跟进详情页
2. 智通财经 (zhitongcaijing.com) 搜索API → 跟进详情页
3. 雪球 (xueqiu.com)            股票新闻API → 跟进详情页
4. 新浪财经 (finance.sina.com.cn) Roll API → 跟进详情页
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import scrapy
from scraper.items import NewsArticleItem


# ── 工具函数 ────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_to_iso(ts_ms) -> str:
    try:
        return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return _now()


def _clean(text: str) -> str:
    """去除 HTML 标签和多余空白"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_body(response, *selectors) -> str:
    """按优先级提取正文（最多3000字）
    1. 先尝试 JSON-LD structured data（跨站点最可靠）
    2. 再按传入的 CSS selectors 逐一匹配
    """
    # JSON-LD: 很多正规新闻站点都有 articleBody 字段
    for raw in response.css('script[type="application/ld+json"]').getall():
        try:
            text = re.sub(r"<[^>]+>", "", raw)
            data = json.loads(text)
            # 可能是 list 或 dict
            items = data if isinstance(data, list) else [data]
            for item in items:
                body = item.get("articleBody") or item.get("description") or ""
                body = _clean(body)
                if len(body) > 100:
                    return body[:3000]
        except Exception:
            pass

    # CSS selectors fallback
    for sel in selectors:
        parts = response.css(sel).getall()
        body = " ".join(_clean(p) for p in parts if _clean(p))
        if len(body) > 100:
            return body[:3000]
    return ""


# ── 港险关键词过滤 ──────────────────────────────────────────────

HK_INSURANCE_KEYWORDS = [
    "友邦", "AIA", "保诚", "Prudential", "宏利", "Manulife",
    "富卫", "FWD", "汇丰人寿", "HSBC Life", "永明金融", "万通保险",
    "香港保险", "港险", "储蓄险", "重疾险", "分红险",
    "1299", "2378", "945",
]

def _is_hk_insurance(text: str) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in HK_INSURANCE_KEYWORDS)


# ─────────────────────────────────────────────
# 1. 证券时报
# ─────────────────────────────────────────────

class SecuritiesTimesSpider(scrapy.Spider):
    """证券时报 — JSON API 列表 + 跟进详情页抓全文"""
    name = "securities_times"
    CHANNELS = [("kx", "快讯"), ("gs", "公司")]
    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    def start_requests(self):
        for ch_type, ch_name in self.CHANNELS:
            yield scrapy.Request(
                url=f"https://www.stcn.com/article/list.html?type={ch_type}&page_time=1",
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, */*",
                    "Referer": f"https://www.stcn.com/article/list/{ch_type}.html",
                },
                callback=self.parse_api,
                meta={"ch_name": ch_name},
            )

    def parse_api(self, response):
        ch_name = response.meta["ch_name"]
        try:
            data = json.loads(response.text)
        except Exception:
            return
        if data.get("state") != 1:
            return

        for art in data.get("data", []):
            if not isinstance(art, dict):
                continue
            title = art.get("title", "").strip()
            url   = art.get("url", "")
            if not title or not url:
                continue
            if not _is_hk_insurance(title):
                continue

            full_url = "https://www.stcn.com" + url if url.startswith("/") else url
            yield scrapy.Request(
                full_url,
                callback=self.parse_detail,
                meta={
                    "title": title,
                    "source": art.get("source", "证券时报"),
                    "pub_ts": art.get("time", 0),
                    "ch_name": ch_name,
                },
                errback=self.errback,
            )

    def parse_detail(self, response):
        title  = response.meta["title"]
        source = response.meta["source"]
        pub_ts = response.meta["pub_ts"]
        ch_name = response.meta["ch_name"]

        body = _extract_body(
            response,
            "div.article-content p::text",
            "div.article-content ::text",
            "div.content p::text",
            "div.content ::text",
            ".detail-content p::text",
            ".article-body p::text",
            "article p::text",
            "article ::text",
        )

        yield NewsArticleItem(
            title_zh     = title,
            content_zh   = body,
            excerpt      = body[:200] if body else title[:200],
            source_url   = response.url,
            source_name  = source or "证券时报",
            published_at = _ts_to_iso(pub_ts) if pub_ts else _now(),
            scraped_at   = _now(),
            category     = "market",
            tags         = ["证券时报", "港险", ch_name],
        )

    def errback(self, failure):
        self.logger.warning(f"[stcn] 请求失败: {failure.request.url}")


# ─────────────────────────────────────────────
# 2. 智通财经
# ─────────────────────────────────────────────

class ZhitongCaijingSpider(scrapy.Spider):
    """智通财经 — 港险公司搜索 + 跟进详情页抓全文"""
    name = "zhitong_caijing"
    allowed_domains = ["zhitongcaijing.com"]
    HK_INSURER_STOCKS = {
        "1299": "AIA友邦",
        "2378": "保诚",
        "945":  "宏利",
        "6060": "众安在线",
        "966":  "中国太平",
    }
    custom_settings = {
        "DOWNLOAD_DELAY": 2.5,
        "USER_AGENT": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
        ),
    }

    def start_requests(self):
        for code, name in self.HK_INSURER_STOCKS.items():
            url = (
                f"https://www.zhitongcaijing.com/api/v1/content/list"
                f"?keyword={code}&page=1&pagesize=20"
            )
            yield scrapy.Request(
                url,
                callback=self.parse_list,
                meta={"code": code, "name": name},
                headers={"Accept": "application/json"},
                errback=self.errback,
            )

    def parse_list(self, response):
        name = response.meta["name"]
        code = response.meta["code"]
        try:
            data = json.loads(response.text)
        except Exception:
            return

        articles = (
            data.get("data", {}).get("list", [])
            or data.get("data", [])
            or data.get("list", [])
        )

        for art in articles:
            if not isinstance(art, dict):
                continue
            title = _clean(art.get("title", "") or art.get("name", ""))
            url   = art.get("url", "") or art.get("link", "")
            ts    = art.get("publish_time", 0) or art.get("time", 0)

            if not title or len(title) < 5 or not url:
                continue

            full_url = (
                "https://www.zhitongcaijing.com" + url
                if url.startswith("/") else url
            )
            yield scrapy.Request(
                full_url,
                callback=self.parse_detail,
                meta={"title": title, "name": name, "code": code, "ts": ts},
                errback=self.errback,
            )

    def parse_detail(self, response):
        title = response.meta["title"]
        name  = response.meta["name"]
        code  = response.meta["code"]
        ts    = response.meta["ts"]

        body = _extract_body(
            response,
            "div.article-detail p::text",
            "div.article-detail ::text",
            "div.content-detail p::text",
            ".news-content p::text",
            ".news-content ::text",
            "article p::text",
            "article ::text",
        )

        yield NewsArticleItem(
            title_zh     = title,
            content_zh   = body,
            excerpt      = body[:200] if body else title[:200],
            source_url   = response.url,
            source_name  = "智通财经",
            published_at = _ts_to_iso(ts) if ts else _now(),
            scraped_at   = _now(),
            category     = "market",
            tags         = [name, f"{code}.HK", "港险", "港股"],
        )

    def errback(self, failure):
        self.logger.warning(f"[zhitong] 请求失败: {failure.request.url}")


# ─────────────────────────────────────────────
# 3. 雪球
# ─────────────────────────────────────────────

class XueqiuInsuranceSpider(scrapy.Spider):
    """雪球 — 港险股票新闻 + 跟进详情页抓全文"""
    name = "xueqiu_insurance"
    allowed_domains = ["xueqiu.com", "stock.xueqiu.com"]
    HK_SYMBOLS = {
        "HK01299": "AIA友邦",
        "HK02378": "保诚",
        "HK00945": "宏利",
    }
    custom_settings = {
        "DOWNLOAD_DELAY": 3.0,
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
        ),
        "COOKIES_ENABLED": True,
    }

    def start_requests(self):
        # 先拿 cookie
        yield scrapy.Request(
            "https://xueqiu.com",
            callback=self.after_cookie,
            errback=self.errback,
        )

    def after_cookie(self, response):
        for symbol, name in self.HK_SYMBOLS.items():
            url = (
                f"https://stock.xueqiu.com/v5/stock/search/news.json"
                f"?symbol={symbol}&count=20&source=all"
            )
            yield scrapy.Request(
                url,
                callback=self.parse_news,
                meta={"symbol": symbol, "name": name},
                headers={
                    "Accept": "application/json",
                    "Referer": f"https://xueqiu.com/S/{symbol}",
                },
                errback=self.errback,
            )

    def parse_news(self, response):
        symbol = response.meta["symbol"]
        name   = response.meta["name"]
        try:
            data = json.loads(response.text)
        except Exception:
            return

        items = data.get("data", {}).get("items", [])

        for item in items:
            if not isinstance(item, dict):
                continue
            title = _clean(item.get("title", "") or item.get("text", "")[:80])
            url   = item.get("target", "") or item.get("share_url", "")
            ts    = item.get("created_at", 0)
            desc  = _clean(item.get("description", "") or item.get("text", ""))
            src   = item.get("source", "雪球")

            if not title or len(title) < 5:
                continue
            # 雪球站内 URL 可以跟进；外部链接（无 VPN 可能不可达）先用摘要
            if url and "xueqiu.com" in url:
                yield scrapy.Request(
                    url,
                    callback=self.parse_detail,
                    meta={"title": title, "symbol": symbol, "name": name,
                          "ts": ts, "source": src, "desc": desc},
                    errback=self.errback,
                )
            else:
                # 外部链接：仅保存摘要
                yield NewsArticleItem(
                    title_zh     = title,
                    excerpt      = desc[:200] if desc else title[:200],
                    content_zh   = desc,
                    source_url   = url,
                    source_name  = f"雪球·{src}" if src != "雪球" else "雪球",
                    published_at = _ts_to_iso(ts) if ts else _now(),
                    scraped_at   = _now(),
                    category     = "market",
                    tags         = [name, symbol, "港险", "雪球"],
                )

    def parse_detail(self, response):
        title  = response.meta["title"]
        name   = response.meta["name"]
        symbol = response.meta["symbol"]
        ts     = response.meta["ts"]
        src    = response.meta["source"]
        desc   = response.meta["desc"]

        body = _extract_body(
            response,
            "div.article__bd p::text",
            ".note-inner p::text",
            ".content-list p::text",
            "article p::text",
        ) or desc  # 抓不到正文时退回到摘要

        yield NewsArticleItem(
            title_zh     = title,
            content_zh   = body,
            excerpt      = body[:200] if body else title[:200],
            source_url   = response.url,
            source_name  = f"雪球·{src}" if src != "雪球" else "雪球",
            published_at = _ts_to_iso(ts) if ts else _now(),
            scraped_at   = _now(),
            category     = "market",
            tags         = [name, symbol, "港险", "雪球"],
        )

    def errback(self, failure):
        self.logger.warning(f"[xueqiu] 请求失败: {failure.request.url}")


# ─────────────────────────────────────────────
# 4. 新浪财经保险频道
# ─────────────────────────────────────────────

class SinaInsuranceSpider(scrapy.Spider):
    """新浪财经 — Roll API 列表 + 跟进详情页抓全文"""
    name = "sina_insurance"
    allowed_domains = ["feed.mix.sina.com.cn", "finance.sina.com.cn", "sina.com.cn"]
    START_URLS = [
        "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&k=&num=50&page=1",
        "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2636&k=&num=50&page=1",
    ]
    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    def start_requests(self):
        for url in self.START_URLS:
            yield scrapy.Request(
                url, callback=self.parse_roll,
                headers={"Referer": "https://finance.sina.com.cn/insurance/"},
                errback=self.errback,
            )

    def parse_roll(self, response):
        try:
            data = json.loads(response.text)
        except Exception:
            return

        articles = data.get("result", {}).get("data", [])
        for art in articles:
            if not isinstance(art, dict):
                continue
            title = art.get("title", "").strip()
            url   = art.get("url", "")
            intro = _clean(art.get("intro", ""))
            media = art.get("media_name", "新浪财经")
            ctime = art.get("ctime", "")

            if not title or not url:
                continue
            if not _is_hk_insurance(title + intro):
                continue

            yield scrapy.Request(
                url,
                callback=self.parse_detail,
                meta={"title": title, "media": media,
                      "ctime": ctime, "intro": intro},
                errback=self.errback,
            )

    def parse_detail(self, response):
        title = response.meta["title"]
        media = response.meta["media"]
        ctime = response.meta["ctime"]
        intro = response.meta["intro"]

        body = _extract_body(
            response,
            "div.article-content-left p::text",  # news.sina.com.cn 新格式
            "div#artibody p::text",               # news.sina.com.cn 老格式
            "div#artibody ::text",
            "div.article-content p::text",
            "div.art_detail p::text",
            "div.article p::text",
            ".blk_container p::text",             # finance.sina.com.cn 新格式
            ".finance-article p::text",
            ".content p::text",
            "article p::text",
            "article ::text",
        ) or intro  # 退回摘要

        yield NewsArticleItem(
            title_zh     = title,
            content_zh   = body,
            excerpt      = body[:200] if body else title[:200],
            source_url   = response.url,
            source_name  = media or "新浪财经",
            published_at = ctime,
            scraped_at   = _now(),
            category     = "market",
            tags         = ["新浪财经", "港险"],
        )

    def errback(self, failure):
        self.logger.warning(f"[sina] 请求失败: {failure.request.url}")
