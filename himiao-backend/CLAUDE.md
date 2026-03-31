# HiMiao 后端项目

## 读这一个文件就够了
`/Users/miao/.claude/projects/-Volumes-docker/memory/MEMORY.md` — HiMiao相关章节

## 关键速查
- FastAPI port 8888，路径 /Volumes/docker/himiao-backend/
- DB: /Volumes/docker/himiao-data/db/himiao.db（容器内 /app/data/himiao.db）
- 代码改完需重启容器（uvicorn无--reload），用户在UGREEN界面操作
- 险种：savings / whole_life / critical_illness（已冻结，不能新增）
- 核心文件：app/models/product.py / app/services/ai_parser.py
- Schema文档：HIMIAO_SCHEMA.md（本目录）

## 工作规则
- 不废话，直接干
- 方案级先说再动手，代码级直接写
- 完成后更新 memory/MEMORY.md 的 HiMiao 章节
