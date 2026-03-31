# GitHub 上传指南（已脱敏裁剪版）

本目录是从 NAS 备份裁剪导出的 **GitHub 可公开代码包**。

## 1. 已确认可上传
- `himiao-web/`：前端静态资源（HTML/JS/CSS、页面、组件等）
- `himiao-backend/`：后端代码与运行配置示例（保留 `.env.example`，不含真实密钥）
- 根目录说明：`README.md`、`.gitignore`

## 2. 已排除（不在本包内）
- `himiao-backend/.env`（密钥/私有配置）
- `himiao-backend/himiao.db`（SQLite 数据库）
- `himiao-backend/himiao-api.tar` / `*.tar*`（打包产物）
- `himiao-data/`（上传文件、日志、OCR 输出等业务数据）

`.gitignore` 也已配置了常见敏感文件规则，避免误提交。

## 3. 上传到 GitHub（你本机执行）
1) 进到该目录：
   `cd "$EXPORT_DIR"`
2) 初始化 git（若目录已是 git 仓库可跳过）：
   `git init`
3) 创建/编辑远程仓库后设置 remote：
   `git remote add origin <YOUR_GITHUB_REPO_URL>`
4) 提交：
   `git add .`
   `git commit -m "Export: himiao web+backend (sanitized)"`
5) 推送：
   `git branch -M main`
   `git push -u origin main`

## 4. 推送前自检（强烈建议）
- 运行：`git status`
- 再运行：`git grep -n "OPENAI|DEEPSEEK|API_KEY|SECRET|PRIVATE" || true`
- 确认没有 `.env` / `.db` / `tar` 被加入。

