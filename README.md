# HiMiao Hong Kong Insurance Audit Platform
# HiMiao 香港保险审计平台

![HiMiao Platform Screenshot](2026-03-31%2021.44.15.png)


**Languages / 语言：** [简体中文](#简体中文) · [English](#english)

---

## 简体中文

HiMiao 是一个面向**香港保险产品**的信息审计与展示平台，包含：

- **公开前台**：产品展示、审计相关字段、资讯内容
- **管理后台**：录入、审核发布、基础内容管理
- **API 后端**：统一接口、鉴权、产品与内容服务

本仓库为可公开发布版本，已做敏感信息清理，适用于演示、二次开发与部署参考。

### 网站定位

提供相对中立的保险产品信息展示，重点包括：

- 产品基础信息与结构化字段
- 精算相关字段的管理与对外输出
- 草稿 / 已发布分离的审核流程
- 中 / 英 / 繁等多语言内容框架

> **声明**：本项目为信息平台与管理系统，**不构成**任何销售邀约、投保建议或投资建议。

### 功能概览

| 模块 | 说明 |
|------|------|
| `himiao-web` | 首页、产品列表/详情、文章页；导航与多语言；统一 API 客户端 |
| `himiao-web/admin.html` | 登录鉴权；产品与发布状态；部分 AI 解析入口（依赖本地模型） |
| `himiao-backend` | FastAPI、JWT、SQLite（可扩展）、产品与用户等模块 |

### 技术栈

- 前端：HTML / CSS / JavaScript（静态站点）
- 后端：Python · FastAPI · SQLAlchemy
- 数据库：默认 SQLite，可按配置调整
- AI：Ollama（通过环境变量配置地址与模型）
- 部署：Docker / docker-compose

### 仓库结构

- `himiao-web/` — 静态页面与前端脚本
- `himiao-backend/` — API、数据模型、脚本与部署配置
- `LICENSE` — 许可证

### 安全与导出说明

公开包中已移除或替换：

- 真实 `.env`、密钥、token、私钥等
- 生产数据库、上传文件、缓存与大型打包产物
- 内网地址及个人联系信息等（已占位符化）

部署前请复制 `himiao-backend/.env.example` 为 `.env` 并填写真实配置。

### 快速开始

1. 克隆本仓库  
2. 复制 `himiao-backend/.env.example` → `himiao-backend/.env`，填写 JWT、数据库、邮件、模型服务等  
3. 在 `himiao-backend/` 使用 `docker-compose.yml` 启动后端；前端由 Nginx 或任意静态服务器托管  
4. 打开前台与后台页面，与 API 联调  

> **注意**：仓库不含生产数据库与用户数据，首次运行需自行初始化数据。

### 发布建议

- 可先设为**私有仓库**联调，再决定是否公开  
- 建议开启 GitHub Secret Scanning、Dependabot  
- 发布前再次扫描密钥、数据库文件与误传的敏感内容  

### 许可证

本项目采用 [MIT License](LICENSE)。

---

## English

HiMiao is an **information audit and presentation** platform for Hong Kong insurance products. It includes:

- **Public site**: product pages, audit-related fields, editorial content
- **Admin console**: data entry, review & publish, basic CMS workflows
- **API backend**: unified endpoints, authentication, product & content services

This repository is a **sanitized, public-ready** export suitable for demos, forks, and deployment reference.

### What this project is

HiMiao aims to present insurance product information in a relatively neutral way:

- Structured product metadata and disclosures-oriented fields
- Management and export of actuarial-style metrics where applicable
- Draft vs. published workflow
- Framework for Chinese / English / Traditional Chinese content

> **Disclaimer**: This is an information platform and admin system. It is **not** an offer to sell insurance, nor financial or investment advice.

### Feature overview

| Area | Notes |
|------|--------|
| `himiao-web` | Home, product list/detail, articles; i18n; shared API client |
| `himiao-web/admin.html` | Auth; product CRUD & publish flags; optional AI parsing (local model) |
| `himiao-backend` | FastAPI, JWT, SQLite by default (pluggable), users & products |

### Tech stack

- Frontend: static HTML / CSS / JavaScript  
- Backend: Python, FastAPI, SQLAlchemy  
- Database: SQLite default; can be reconfigured  
- AI: Ollama (host & model via env vars)  
- Ops: Docker / docker-compose  

### Repository layout

- `himiao-web/` — static frontend  
- `himiao-backend/` — API, models, scripts, deploy configs  
- `LICENSE` — license text  

### Security & export notes

This public bundle **excludes or redacts**:

- Real `.env` secrets, tokens, private keys  
- Production DBs, uploads, build artifacts  
- Internal IPs and personal contact details (replaced with placeholders)  

Copy `himiao-backend/.env.example` to `.env` and fill in real values before running in production.

### Quick start

1. Clone the repository.  
2. Copy `himiao-backend/.env.example` → `himiao-backend/.env` (JWT, DB, email, LLM/Ollama, etc.).  
3. Start the backend from `himiao-backend/` using `docker-compose.yml`; serve `himiao-web/` with Nginx or any static host.  
4. Open the public pages and admin UI; verify API integration.  

> **Note**: No production database or user data is shipped; you must bootstrap data on first run.

### Release checklist (recommended)

- Start as a **private** repo for integration testing, then go public if appropriate.  
- Enable Secret Scanning and Dependabot where available.  
- Re-scan for leaked keys, DB dumps, and accidental PII before tagging a release.  

### License

This project is licensed under the [MIT License](LICENSE).
