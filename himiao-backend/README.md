# HiMiao Phase 2 — NAS 部署手册

## 目录结构（NAS 上）

```
/Docker/
├── himiao-web/          # 前端静态文件（HTML/JS/CSS）
├── himiao-data/
│   ├── db/              # SQLite 数据库文件持久化
│   └── uploads/         # 用户上传文件
├── npm-data/            # NPM 配置持久化
├── npm-letsencrypt/     # SSL 证书
└── ddns-go/             # DDNS-GO 配置
```

---

## 一、首次部署步骤

### 1. 准备 NAS 目录
```bash
mkdir -p /Docker/himiao-web
mkdir -p /Docker/himiao-data/db
mkdir -p /Docker/himiao-data/uploads
mkdir -p /Docker/npm-data
mkdir -p /Docker/npm-letsencrypt
mkdir -p /Docker/ddns-go
```

### 2. 上传前端文件
将 index.html / product-list.html / product-detail.html / news.html / about.html / compare.html 
以及 components/ data/ 目录全部上传到 /Docker/himiao-web/

### 3. 配置 .env
```bash
cd /Docker/himiao-backend   # 你存放后端代码的位置
cp .env.example .env
nano .env                   # 填入 JWT_SECRET_KEY 和 ADMIN_PASSWORD
```

生成 JWT_SECRET_KEY：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. 启动所有服务
```bash
docker-compose up -d
```

### 5. 数据迁移（一次性）
```bash
docker exec -it himiao-api python scripts/migrate_json.py \
  --products /Docker/himiao-web/data/products.json \
  --articles /Docker/himiao-web/data/articles.json
```

### 6. 验证
- API 文档：http://NAS_IP:8888/docs
- 健康检查：http://NAS_IP:8888/health
- 前端：http://NAS_IP:8080

---

## 二、NPM 配置（管理界面 http://NAS_IP:8181）

首次登录：admin@example.com / changeme

配置两个代理主机：

| 域名              | 转发到             | SSL               |
|-------------------|--------------------|-------------------|
| himiao.hk         | himiao-web:80      | Let's Encrypt     |
| api.himiao.hk     | himiao-api:8888    | Let's Encrypt     |

**注意端口**：由于运营商封锁 80/443，在路由器做端口映射：
- 外网 8443 → NAS 8443（NPM HTTPS 端口）
- 域名 DNS 记录指向公网 IP

---

## 三、前端对接 API（替换 fetch 路径）

改动只需一处，在每个页面的 fetch 调用：
```javascript
// 旧（静态 JSON）
const res = await fetch('data/products.json');

// 新（后端 API，格式完全兼容）
const res = await fetch('https://api.himiao.hk/api/v1/products');
```

邮件订阅表单：
```javascript
// 旧（无后端，假订阅）
// 新
await fetch('https://api.himiao.hk/api/v1/subscribers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: emailValue })
});
```

---

## 四、上云迁移（一键切换）

只需修改 .env 一行：
```bash
# 改这一行
DATABASE_URL=postgresql://himiao:password@rds-endpoint:5432/himiao
# 其余代码零修改
```

然后：
```bash
docker-compose down
docker-compose up -d
```

---

## 五、API 接口速查

| 方法   | 路径                          | 说明              | 需要 JWT |
|--------|-------------------------------|-------------------|----------|
| POST   | /api/v1/auth/login            | 获取 Token        | ✗        |
| GET    | /api/v1/products              | 产品列表          | ✗        |
| GET    | /api/v1/products/{slug}       | 产品详情          | ✗        |
| POST   | /api/v1/products              | 新建产品          | ✓        |
| PATCH  | /api/v1/products/{slug}       | 更新产品          | ✓        |
| DELETE | /api/v1/products/{slug}       | 删除产品          | ✓        |
| GET    | /api/v1/articles              | 文章列表          | ✗        |
| POST   | /api/v1/articles              | 发布文章          | ✓        |
| POST   | /api/v1/subscribers           | 订阅              | ✗        |
| GET    | /api/v1/subscribers           | 订阅者列表        | ✓        |
| GET    | /api/v1/brokers               | 经纪人列表        | ✗        |
| POST   | /api/v1/brokers               | 新增经纪人        | ✓        |
| PATCH  | /api/v1/ads/{slot_key}        | 更新广告位        | ✓        |
| GET    | /health                       | 健康检查          | ✗        |

完整文档：http://NAS_IP:8888/docs（Swagger UI，可直接在线测试）
