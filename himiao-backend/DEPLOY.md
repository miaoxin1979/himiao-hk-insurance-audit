# HiMiao 一键部署（NAS / 本机）

在 **`himiao-backend`** 目录执行：

```bash
cd /path/to/himiao-backend
docker compose up -d --build
```

- **前端静态**：`http://<IP>:8080`（`himiao-web` 挂载 `../himiao-web`）
- **API**：`http://<IP>:8888`（健康检查 `/health`）
- **NPM 管理界面**：`:8181`（若已启用 compose 中的 `npm` 服务）

`nginx-web.conf` 已配置：

- `/api/` → `himiao-api:8888`
- `/uploads/` → 后端图片（讲堂富文本插图）

修改前端文件后**无需重建镜像**（卷挂载）；修改 `nginx-web.conf` 后需重启 `himiao-web`：

```bash
docker compose restart himiao-web
```
