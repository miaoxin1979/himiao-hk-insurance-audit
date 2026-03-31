# scraper/Dockerfile
# 爬虫容器 — 独立于 API 容器，按需启动
FROM python:3.11-slim

WORKDIR /app

# 系统依赖（PaddleOCR + PDF 处理）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY scraper/requirements-scraper.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-scraper.txt

# 应用代码
COPY app/ ./app/
COPY scraper/ ./scraper/
COPY .env.example .env
RUN echo "[settings]\ndefault = scraper.settings\n\n[deploy]\nproject = scraper" > scrapy.cfg

# 数据目录
RUN mkdir -p /data/scraper_output /data/scraper_pdfs /data/logs

# 非 root 运行
RUN useradd -r -u 1002 scraper && chown -R scraper:scraper /app /data
USER scraper

# 默认：启动定时调度器
CMD ["python", "scraper/scheduler/run_scheduler.py"]
