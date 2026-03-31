# HiMiao Hong Kong Insurance Audit Platform

![HiMiao Platform Screenshot](2026-03-31%2021.44.15.png)

HiMiao 是一个面向香港保险产品的信息审计与展示平台，包含：

- 公开前台：保险产品展示、审计指标、内容资讯页
- 管理后台：产品录入、审核发布、基础内容管理
- API 后端：统一数据接口、鉴权、产品与内容服务

该仓库为可公开发布版本，已完成敏感信息清理，适合用于演示、二次开发与部署参考。

## 这个网站是做什么的

HiMiao 的核心目标是提供相对中立的保险产品信息展示能力，重点围绕：

- 产品基础信息和结构化字段展示
- 精算相关字段的管理与输出
- 后台审核后发布（草稿与已发布分离）
- 多语言内容（中/英/繁）支持框架

> 说明：本项目定位为信息平台与管理系统，不构成任何销售邀约或投资建议。

## 功能概览

- 前台站点（`himiao-web`）
  - 首页、产品列表、产品详情、文章内容页
  - 导航与多语言组件
  - 统一 API 客户端调用后端接口
- 后台管理（`himiao-web/admin.html`）
  - 登录鉴权
  - 产品管理与发布状态控制
  - 部分 AI 解析能力入口（依赖本地模型服务）
- 后端服务（`himiao-backend`）
  - FastAPI REST API
  - JWT 鉴权
  - SQLite / 可扩展数据库配置
  - 产品、用户、配置等模块

## 技术栈

- Frontend: HTML / CSS / JavaScript（静态站点）
- Backend: Python + FastAPI + SQLAlchemy
- Database: SQLite（默认，可按配置切换）
- AI integration: Ollama（通过环境变量配置地址与模型）
- Deployment: Docker / docker-compose

## 仓库结构

- `himiao-web/`：前端静态页面与前端脚本
- `himiao-backend/`：后端 API、数据模型、脚本与部署配置
- `LICENSE`：许可证文件
- 其他说明文档：部署、导出、上传说明

## 安全与导出说明

本公开包已移除或替换以下内容：

- 真实环境配置与密钥（如 `.env`、token、私钥）
- 运行期数据文件（如数据库、上传文件、缓存、打包产物）
- 内网地址与个人联系方式等敏感标识（已占位符化）

仓库中保留 `.env.example` 作为配置模板，请在部署前自行填写真实参数。

## 快速开始

1. 克隆仓库
2. 配置后端环境变量
   - 复制 `himiao-backend/.env.example` 为 `himiao-backend/.env`
   - 填写 JWT、数据库、邮件、模型服务等配置
3. 启动服务（示例）
   - 在 `himiao-backend/` 按 `docker-compose.yml` 启动后端
   - 前端静态目录由 Nginx 或任意静态服务器托管
4. 访问前台与后台页面，联调 API

> 注意：仓库不包含生产数据库与用户数据。首次运行需自行初始化数据。

## 发布建议

- 将该仓库设置为私有后先完成联调，再决定是否公开
- 启用 GitHub Secret Scanning / Dependabot
- 发布前再次运行敏感信息扫描（key/token/密码/私钥/数据库文件）

## License

本项目采用 [MIT License](LICENSE)。
