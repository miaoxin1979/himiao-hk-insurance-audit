# scraper/settings.py
# Scrapy 配置 — NAS 友好，低内存占用

BOT_NAME = "himiao_scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# ── 礼貌爬取（避免被封）──
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2.5          # 每次请求间隔 2.5 秒
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 1       # NAS 单线程，省内存
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# ── 浏览器伪装 ──
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# ── Pipeline 顺序 ──
ITEM_PIPELINES = {
    "scraper.pipelines.validate.ValidationPipeline": 100,
    # "scraper.pipelines.translation.TranslationPipeline": 150,
    "scraper.pipelines.database.DatabasePipeline":   200,
    "scraper.pipelines.json_export.JsonExportPipeline": 300,
}

# ── 输出 ──
FEEDS = {}  # 由 JsonExportPipeline 控制
LOG_LEVEL = "INFO"

# ── 重试 ──
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ── 代理（VPN/出口代理）──────────────────────────────────────
# 在 .env 里配置 SCRAPER_PROXY 即可启用，例如：
#   SCRAPER_PROXY=socks5://YOUR_MAC_IP:1080   (Mac Mini 跑的 socks5 代理)
#   SCRAPER_PROXY=http://127.0.0.1:7890          (clash/v2ray HTTP 代理)
# 留空则不走代理
import os as _os
_proxy = _os.getenv("SCRAPER_PROXY", "")
if _proxy:
    DOWNLOADER_MIDDLEWARES = {
        "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 750,
    }
    HTTPPROXY_ENABLED = True
    HTTP_PROXY  = _proxy
    HTTPS_PROXY = _proxy

# ── 缓存（开发时省流量）──
HTTPCACHE_ENABLED = False     # 生产关闭，开发时改 True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "/tmp/scrapy_cache"
