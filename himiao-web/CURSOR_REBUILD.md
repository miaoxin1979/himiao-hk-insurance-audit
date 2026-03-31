# CURSOR 任务：手机版产品页面（经纪人工具版）

## 今日四件事（按顺序完成）
1. **index-v2.html** — 数据仪表盘首页
2. **product-list-v2.html** — 补搜索、保司筛选、经纪人收藏/分享
3. **product-detail-v2.html** — 手机版详情页
4. **manifest.json** — PWA 配置

---

## 全局约束
- Tailwind CDN：`<script src="https://cdn.tailwindcss.com"></script>`
- 不改原有文件（product-list.html / product-detail.html 保留）
- i18n：固定文字加 `data-i18n`，key 补进 `components/lang.js`
- API 基础地址：`/api/v1/`
- 底部 Tab 四项（所有页面统一）：🏠首页 · 💰储蓄险 · 🛡终身寿 · ❤️重疾险
- 品牌色：`#00a9e0`（蓝）/ `#0f172a`（深色顶栏背景）

---

## 任务一：index-v2.html（极简跳板页）

### 定位
干净的落地页，3秒内进入产品榜单。不调 API，纯静态。

### 布局
```
┌─────────────────────────┐
│                    CN▾  │  右上角语言切换
│                         │
│                         │
│      HiMiao             │
│      AUDIT              │  Logo，居中，大
│                         │
│  香港保险 独立精算        │  副标题，一行
│  不销售 · 不带货          │
│                         │
│  ┌───────────────────┐  │
│  │  查看储蓄险榜单 →  │  │  主 CTA，蓝色大按钮
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │  查看终身寿险    →  │  │  次 CTA
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │  查看重疾险      →  │  │  次 CTA
│  └───────────────────┘  │
│                         │
│  147款 · 12家保司        │  底部小字信任背书
│  数据来自官方演示文件     │
│                         │
└─────────────────────────┘
```

### 要求
- 全屏高度（min-height: 100dvh），垂直居中
- 深色背景（#0f172a），白字，蓝色按钮
- 三个按钮点击分别跳：`product-list-v2.html?type=savings` / `whole_life` / `critical_illness`
- 不需要底部 Tab（这是入口页）
- 加 PWA meta 标签

---

## 任务二：product-list-v2.html（已有，补功能）

### 新增：顶部搜索栏
顶部品牌栏下方加一行搜索：
```
┌─────────────────────────┐
│ 🔍 搜索产品名或保司…     │
└─────────────────────────┘
```
- 前端实时过滤（不调 API），匹配 `meta.name` / `meta.name_en` / `meta.company`
- 清空按钮（×）
- 搜索时隐藏 Tab 和排序栏，只显示匹配结果

### 新增：保司筛选
排序按钮旁边加「保司▾」下拉：
- 选项从已加载数据动态生成（不硬编码）
- 多选，选中保司名高亮
- 「全部」选项重置
- 保司包括：AIA / Prudential / Manulife / FWD / YFLife / SunLife / AXA / BOCLife / ChinaLife / CTFLife / TaipingLife / Generali / FTLife

### 新增：经纪人收藏 / 分享
每张产品卡右上角「＋」按钮：
- 点击加入清单，按钮变「✓」蓝色
- 最多选 3 款，超出时提示「最多选3款」
- 状态存 localStorage（key：`hm_shortlist`）

选了产品后，底部 Tab 上方浮出操作条：
```
┌──────────────────────────────────┐
│ 已选 2 款  [查看清单▾] [生成链接]│
└──────────────────────────────────┘
```
- 「查看清单」展开已选产品列表，可移除
- 「生成链接」生成 URL：
  `product-list-v2.html?share=slug1,slug2`
  弹出 sheet，显示链接 + 一键复制按钮

### 分享链接打开时的行为
URL 含 `?share=` 参数时：
- 只显示这几款产品
- 顶部横幅：「📋 为您精选了 N 款产品」
- 隐藏「＋」收藏按钮（客户模式）
- 隐藏搜索和筛选栏

---

## 任务三：product-detail-v2.html（全新）

### 布局
```
┌─────────────────────────┐
│ ←  AIA · 储蓄险    ＋  │  顶栏（←返回，＋加入清单）
├─────────────────────────┤
│ 盈御多元货币计划3        │  大字产品名
│ Global Wealth Adv. 3    │  小灰英文名
│ [精选][USD][缴5年]       │  标签
├─────────────────────────┤
│   5.1%    8年    103%   │  三核心指标，蓝色大字
│  20年IRR  回本年  分红率  │  小灰标签
├─────────────────────────┤
│ 精算结论                 │  始终展开
│ （content_zh 内容）      │
├─────────────────────────┤
│ ▶ 流动性分析             │  折叠
│ ▶ 收益曲线               │  折叠（含简化折线图）
│ ▶ 精算评分               │  折叠
│ ▶ 风险提示               │  折叠
├─────────────────────────┤
│ 数据来自保司官方演示文件  │  免责声明小字（必须保留）
│ 不构成个人投资建议        │
├─────────────────────────┤
│ [查看桌面完整版 →]       │  跳 product-detail.html?id=
└─────────────────────────┘
│ 🏠  💰  🛡  ❤️          │  底部 Tab
```

### 折叠交互
- CSS `max-height` transition，点标题展开/收起
- 收益曲线：Chart.js 折线图，只显示保证现值 + 乐观总值，20年数据
- `audit_data.timeline` 提供年度数据

### 「加入清单」（顶栏右上角 ＋）
- 同 product-list-v2.html 的 localStorage 逻辑
- 已在清单 → 显示「✓」

### API
- `GET /api/v1/products/{slug}`
- 字段：`meta.name` / `meta.name_en` / `meta.company` / `meta.currency`
- `actuarial.irr_20y` / `actuarial.breakeven_year` / `actuarial.premium_years` / `actuarial.dividend_fulfillment_5y`
- `content_zh`（精算结论）
- `audit_data.timeline`（折线图数据）
- `tags` / `highlight`

---

## 任务四：manifest.json（PWA）

新建 `/Volumes/docker/himiao-web/manifest.json`：
```json
{
  "name": "HiMiao Audit",
  "short_name": "嗨喵",
  "description": "香港保险独立精算审计",
  "start_url": "/index-v2.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#00a9e0",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

所有 v2 页面 `<head>` 加：
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#00a9e0">
<link rel="manifest" href="/manifest.json">
```

---

## 验证清单
- [ ] iPhone 14 Pro（390px）三个页面无横向滚动
- [ ] 搜索「AIA」→ 只显示 AIA 产品
- [ ] 保司筛选「Prudential」→ 只显示保诚
- [ ] 选 2 款 → 生成链接 → 新标签打开 → 只显示 2 款 + 客户横幅
- [ ] 详情页折叠展开流畅
- [ ] 底部 Tab 四页切换正常
- [ ] 语言切换 CN/HK/EN 有效

## 文件输出
- `/Volumes/docker/himiao-web/index-v2.html`（新建）
- `/Volumes/docker/himiao-web/product-list-v2.html`（已有，补功能）
- `/Volumes/docker/himiao-web/product-detail-v2.html`（新建）
- `/Volumes/docker/himiao-web/manifest.json`（新建）
