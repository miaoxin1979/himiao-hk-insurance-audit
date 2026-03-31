# GitHub 上传注意事项（总汇）

本文件用于汇总：本导出包包含/排除哪些内容、上传到 GitHub 前需要做哪些自检、以及标准的上传步骤。

## 1. 本包包含（允许上传）
- `himiao-web/`：前端静态资源与页面（HTML/JS/CSS、组件、资产等）
- `himiao-backend/`：后端代码与运行示例（已保留 `.env.example`，不含真实密钥）
- 根目录说明文件：`README.md`、`.gitignore`、`LICENSE`

## 2. 本包已排除（禁止上传）
- `himiao-backend/.env`（真实密钥/私有配置）
- `himiao-backend/himiao.db`（SQLite 数据库）
- `himiao-backend/himiao-api.tar`、以及所有 `*.tar*` 打包产物
- `himiao-data/`（上传文件、OCR 输出、日志、业务数据等）
- 任何可能泄露敏感信息的文件（如你自行新增的 secret、token、key、private 数据）

## 3. 上传前自检（强烈建议）
请在你本机导出目录执行一次，确保没有误提交：
- `git status`（确认没有异常改动/未忽略文件）
- `git grep -n "OPENAI|DEEPSEEK|API_KEY|SECRET|PRIVATE|TOKEN" || true`（检查是否包含疑似密钥）
- `git ls-files | rg -n "(/\\.env$|himiao\\.db|\\.tar$|\\.tar\\.gz$|^himiao-data/)" || true`（检查是否包含被排除目录/文件）
- 确认根目录存在 `LICENSE`，并且仓库设置里的 License 选择与 `MIT` 一致

如果以上任意一项发现问题：先停止上传，回到导出目录修正/重新裁剪导出包，再执行自检通过后再上传。

## 4. 标准上传步骤（命令可直接照抄）
1. 进入本导出目录：
   - `cd "$EXPORT_DIR"`（把 `EXPORT_DIR` 替换成你的导出目录路径）
2. 初始化 git（如目录不是 git 仓库）：
   - `git init`
3. 添加远程仓库：
   - `git remote add origin <YOUR_GITHUB_REPO_URL>`
4. 提交：
   - `git add .`
   - `git commit -m "Export: himiao web+backend (sanitized)"`
5. 推送到 `main`：
   - `git branch -M main`
   - `git push -u origin main`

## 5. 关于“能否直接运行”
本导出包是脱敏/裁剪后的公开代码包，缺少真实数据库与上传文件。
你本地要跑起来时，通常需要：
- 在 `himiao-backend/` 里复制 `.env.example` 为 `.env` 并按环境填写
- 自行初始化数据库并准备必要的运行依赖数据

## 6. 许可证（MIT）
根目录 `LICENSE` 使用 MIT 协议。
你在 GitHub 创建仓库时建议：
- 仓库设置的 License 选择为 `MIT`
- 与根目录 `LICENSE` 保持一致

## 7. 常见误提交（再次提醒）
- 意外提交了 `*.env`、token/key、私钥、配置文件
- 意外提交了 `himiao.db`（SQLite 数据库）
- 意外提交了 `*.tar*`（打包产物）
- 意外提交了 `himiao-data/`（上传文件、日志、OCR 输出、业务数据等）
- 有新增敏感文件但没更新 `.gitignore`

