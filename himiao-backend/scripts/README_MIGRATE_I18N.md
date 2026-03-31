# 标签+精算辣评三语迁移

## 何时跑

- 首次：把旧格式标签改为 `[{"zh","en","hk"}]`，并补齐 `content_en` / `content_tw`。
- 之后：若曾因连不上 Ollama 导致 en/hk 仍是中文，可再跑一次做「修补」。

## 方式一：本机 Mac 跑（推荐，Ollama 在本机）

**先停掉 himiao-api，再跑迁移，避免数据库被锁。**

```bash
cd /Volumes/docker/himiao-backend

# 1. 停 API
docker stop himiao-api

# 2. 一次性容器跑迁移（连本机 Ollama）
docker run --rm \
  --env-file .env \
  -v "$(pwd)/../himiao-data/db:/app/data" \
  -v "$(pwd)/scripts/migrate_i18n_tags_content.py:/app/scripts/migrate_i18n_tags_content.py" \
  -v "$(pwd)/app/services/translator.py:/app/app/services/translator.py" \
  -e DATABASE_URL=sqlite:////app/data/himiao.db \
  -e MAC_IP=host.docker.internal \
  --entrypoint python \
  himiao-backend-himiao-api:latest \
  scripts/migrate_i18n_tags_content.py

# 3. 再开 API
docker start himiao-api
```

## 方式二：在 himiao-api 容器内跑（NAS 须能访问 Mac Ollama）

NAS 上需能访问 `MAC_IP:11434`（Mac 已设 `OLLAMA_HOST=0.0.0.0` 且防火墙放行）：

```bash
docker exec himiao-api python scripts/migrate_i18n_tags_content.py
```

## 试跑（不写库）

加 `--dry-run`：

```bash
docker run --rm ... scripts/migrate_i18n_tags_content.py --dry-run
# 或
docker exec himiao-api python scripts/migrate_i18n_tags_content.py --dry-run
```
