# HiMiao（开源导出包）

本目录是从你 NAS 上的 `himiao` 备份裁剪导出的 **GitHub 可公开代码包**。

## 本次导出已排除（避免泄露/过大）
- `himiao-backend/.env`（密钥/配置）
- `himiao-backend/himiao.db`（SQLite 数据库）
- `himiao-backend/himiao-api.tar`、以及所有 `*.tar*` 打包产物
- `himiao-data/`（含上传文件、OCR 输出、日志等业务数据）

## 目录结构
- `himiao-web/`：静态前端（HTML/JS/CSS）
- `himiao-backend/`：FastAPI 后端代码与 Docker 配置（已保留 `.env.example`）

## 本地运行（概念说明）
1. 进入 `himiao-backend/`，复制 `.env.example` 为 `.env`，按需填写：
   - 数据库连接、Ollama/LLM 配置等
2. 使用 `docker-compose.yml` 启动（根据你现场的网络环境调整）。

> 注意：此仓库未包含真实数据库与上传文件；你需要自行初始化数据库并配置运行参数。

## 许可证
本项目采用 [MIT License](LICENSE)（Copyright (c) 2026 Beijing Changyou Medical Technology Co., Ltd.）。发布到 GitHub 时请在仓库设置里选择 **MIT** 与根目录 `LICENSE` 一致。
