# ── 构建阶段 ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --prefix=/install -r requirements.txt

# ── 运行阶段（最小镜像）────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY reset_admin.py ./

# 创建上传目录（NAS 阶段本地存储，云阶段挂载 S3）
RUN mkdir -p /data/uploads

# 非 root 用户运行（安全最佳实践）
RUN useradd -r -u 1001 himiao && chown -R himiao:himiao /app /data
USER himiao

EXPOSE 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "2"]
