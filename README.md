# HiMiao Hong Kong Insurance Audit Platform
# HiMiao 香港保险审计平台

![HiMiao Platform Screenshot](2026-03-31%2021.44.15.png)

HiMiao is an information auditing and display platform for Hong Kong insurance products, including:
HiMiao 是一个面向香港保险产品的信息审计与展示平台，包含：
Public frontend: insurance product display, auditing indicators, content information pages
公开前台：保险产品展示、审计指标、内容资讯页
Admin backend: product entry, review and release, basic content management
管理后台：产品录入、审核发布、基础内容管理
API backend: unified data interface, authentication, product and content services
API 后端：统一数据接口、鉴权、产品与内容服务
This repository is a publicly releasable version with sensitive information cleaned up, suitable for demonstration, secondary development and deployment reference.
该仓库为可公开发布版本，已完成敏感信息清理，适合用于演示、二次开发与部署参考。
网站定位
What does this website do?
这个网站是做什么的
HiMiao's core goal is to provide relatively neutral insurance product information display capabilities, focusing on:
HiMiao 的核心目标是提供相对中立的保险产品信息展示能力，重点围绕：
Display of basic product information and structured fields
产品基础信息和结构化字段展示
Management and output of actuarial-related fields
精算相关字段的管理与输出
Release after backend review (separation of draft and published status)
后台审核后发布（草稿与已发布分离）
Multi-language content support framework (Chinese / English / Traditional Chinese)
多语言内容（中 / 英 / 繁）支持框架
Note: This project is positioned as an information platform and management system, and does not constitute any sales solicitation or investment advice.
说明：本项目定位为信息平台与管理系统，不构成任何销售邀约或投资建议。
Function Overview
功能概览
Frontend Site (himiao-web)
前台站点（himiao-web）
Homepage, product list, product details, article content pages
首页、产品列表、产品详情、文章内容页
Navigation and multi-language components
导航与多语言组件
Unified API client to call backend interfaces
统一 API 客户端调用后端接口
Admin Management (himiao-web/admin.html)
后台管理（himiao-web/admin.html）
Login authentication
登录鉴权
Product management and release status control
产品管理与发布状态控制
Entrance for partial AI parsing capabilities (depends on local model services)
部分 AI 解析能力入口（依赖本地模型服务）
Backend Service (himiao-backend)
后端服务（himiao-backend）
FastAPI REST API
FastAPI REST API
JWT authentication
JWT 鉴权
SQLite /extensible database configuration
SQLite / 可扩展数据库配置
Modules for products, users, configurations, etc.
产品、用户、配置等模块
Tech Stack
技术栈
Frontend: HTML / CSS / JavaScript (static site)
前端：HTML / CSS / JavaScript（静态站点）
Backend: Python + FastAPI + SQLAlchemy
后端：Python + FastAPI + SQLAlchemy
Database: SQLite (default, configurable switch)
数据库：SQLite（默认，可按配置切换）
AI integration: Ollama (configure address and model via environment variables)
AI 集成：Ollama（通过环境变量配置地址与模型）
Deployment: Docker /docker-compose
部署：Docker /docker-compose
Repository Structure
仓库结构
himiao-web/: Frontend static pages and scripts
himiao-web/：前端静态页面与前端脚本
himiao-backend/: Backend API, data models, scripts and deployment configurations
himiao-backend/：后端 API、数据模型、脚本与部署配置
LICENSE: License file
LICENSE：许可证文件
Other documentation: deployment, export, upload instructions
其他说明文档：部署、导出、上传说明
Security & Export Notes
安全与导出说明
This public package has removed or replaced the following content:
本公开包已移除或替换以下内容：
Real environment configurations and keys (e.g. .env, token, private keys)
真实环境配置与密钥（如 .env、token、私钥）
Runtime data files (e.g. databases, uploaded files, caches, packaged artifacts)
运行期数据文件（如数据库、上传文件、缓存、打包产物）
Sensitive identifiers such as intranet addresses and personal contact information (placeholderized)
内网地址与个人联系方式等敏感标识（已占位符化）
A .env.example is retained in the repository as a configuration template. Please fill in the actual parameters before deployment.
仓库中保留 .env.example 作为配置模板，请在部署前自行填写真实参数。
Quick Start
快速开始
Clone the repository
克隆仓库
Configure backend environment variables
配置后端环境变量
Copy himiao-backend/.env.example to himiao-backend/.env
复制 himiao-backend/.env.example 为 himiao-backend/.env
Fill in configurations for JWT, database, email, model service, etc.
填写 JWT、数据库、邮件、模型服务等配置
Start services (example)
启动服务（示例）
Start the backend via docker-compose.yml in himiao-backend/
在 himiao-backend/ 按 docker-compose.yml 启动后端
Host the frontend static directory with Nginx or any static server
前端静态目录由 Nginx 或任意静态服务器托管
Access frontend and backend pages, debug API integration
访问前台与后台页面，联调 API
Note: The repository does not contain production databases or user data. Initialize data yourself on first run.
注意：仓库不包含生产数据库与用户数据。首次运行需自行初始化数据。
Release Recommendations
发布建议
Set the repository to private first for debugging, then decide whether to make it public
将该仓库设置为私有后先完成联调，再决定是否公开
Enable GitHub Secret Scanning / Dependabot
启用 GitHub Secret Scanning / Dependabot
Run sensitive information scanning again before release (keys, tokens, passwords, private keys, database files)
发布前再次运行敏感信息扫描（key/token/ 密码 / 私钥 / 数据库文件）
License
许可证
This project is licensed under the MIT License.
本项目采用 MIT License。



