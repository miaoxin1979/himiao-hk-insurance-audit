#!/usr/bin/env python3
# scraper/scheduler/run_scheduler.py
"""
定时任务调度器 — NAS 部署版
使用 APScheduler，每天凌晨 3 点运行爬虫
不依赖 Celery/Redis，NAS 友好

用法：
  python scraper/scheduler/run_scheduler.py
  # 或通过 Docker 容器启动（见 docker-compose.yml）
"""
import logging
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/data/logs/scheduler.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# 把项目根目录加入 path
ROOT = str(Path(__file__).parent.parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_spider(spider_name: str):
    """运行单个 Scrapy Spider"""
    logger.info(f"▶ Starting spider: {spider_name}")
    start = datetime.now()

    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "--set", f"SCRAPY_SETTINGS_MODULE=scraper.settings",
    ]

    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 分钟超时
    )

    elapsed = (datetime.now() - start).seconds
    if result.returncode == 0:
        logger.info(f"✅ {spider_name} done in {elapsed}s")
    else:
        logger.error(f"❌ {spider_name} failed in {elapsed}s:\n{result.stderr[-500:]}")


def daily_crawl():
    """每日爬取任务"""
    logger.info("=" * 50)
    logger.info(f"Daily crawl started: {datetime.now().isoformat()}")

    # 按顺序运行，避免并发占用 NAS 资源
    spiders = [
        # 大陆可访问（无需VPN，优先跑）
        "securities_times",         # 证券时报，港险关键词过滤
        "zhitong_caijing",          # 智通财经，港股公司新闻
        "xueqiu_insurance",         # 雪球，AIA/保诚/宏利股票讨论
        "sina_insurance",           # 新浪财经保险频道
        # 监管公告（可访问性不稳定，排后）
        "hkia_news",
        "mpf_news",
        # Google News RSS（需VPN时才有效）
        "google_news_hk_insurance",
    ]
    for spider in spiders:
        try:
            run_spider(spider)
        except Exception as e:
            logger.error(f"Spider {spider} crashed: {e}")

    logger.info(f"Daily crawl finished: {datetime.now().isoformat()}")
    logger.info("=" * 50)


def main():
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("APScheduler not installed: pip install apscheduler")
        sys.exit(1)

    # 确保日志目录存在
    Path("/data/logs").mkdir(parents=True, exist_ok=True)

    scheduler = BlockingScheduler(timezone="Asia/Hong_Kong")

    # 每天 03:00 HKT 运行（NAS 低负载时段）
    scheduler.add_job(
        daily_crawl,
        CronTrigger(hour=3, minute=0),
        id="daily_crawl",
        name="HiMiao Daily Scraper",
        max_instances=1,  # 防止重叠运行
        misfire_grace_time=3600,
    )

    # 每周一 04:00 额外运行一次完整爬取
    scheduler.add_job(
        daily_crawl,
        CronTrigger(day_of_week="mon", hour=4, minute=0),
        id="weekly_full_crawl",
        name="HiMiao Weekly Full Scraper",
        max_instances=1,
    )

    logger.info("Scheduler started. Next run: daily at 03:00 HKT")
    logger.info("Press Ctrl+C to stop")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    # 支持立即运行模式（调试用）
    if "--now" in sys.argv:
        logger.info("Running immediately (--now flag)")
        daily_crawl()
    else:
        main()
