# CURSOR 验证任务 — 3项待测功能

请用浏览器工具逐项验证，发现问题直接修代码。

---

## 环境信息
- 前台地址：http://YOUR_NAS_IP:8080
- 后台地址：http://YOUR_NAS_IP:8080/admin.html
- 后台账号：<请本地配置>
- 后台密码：<请本地配置>

---

## 任务 1：后台「站点设置」页面不再空白

### 步骤
1. 打开 http://YOUR_NAS_IP:8080/admin.html
2. 输入账号密码登录
3. 点击左侧菜单「⚙️ 站点设置」
4. 页面应显示一个表单（网站名称、SEO描述等字段），不能是空白

### 预期结果
- 表单加载，至少有输入框，不报 JS 错误

### 已做的修复（待验证）
- `admin.html` 中 `loadSettings()` 改为用 `API.adminFetch('/settings')` 而非不存在的 `API.fetch`

### 如果仍然空白，排查方向
- 打开浏览器控制台，看报什么错
- 查找 `loadSettings` 函数在 admin.html 中的实现
- 检查 `/api/v1/settings` 接口是否存在（curl http://YOUR_NAS_IP:8888/api/v1/settings）

---

## 任务 2：后台 PDF 上传后自动触发 AI 解析

### 步骤
1. 登录后台
2. 点击左侧「📦 产品管理」→ 切换到「AI 解析」tab（顶部有 tab 切换）
3. 点击文件选择区域，选择任意一个 PDF 文件
4. 选完后不要手动点任何按钮，观察是否自动开始解析（label 文字变成「✅ 文件名 — 解析中…」）

### 预期结果
- 选文件后自动触发解析，不需要手动点「AI 填入」按钮
- label 文字更新为 `✅ xxx.pdf — 解析中…`
- 解析完成后表单字段自动填入

### 已做的修复（待验证）
- `onAiFileChange()` 末尾加了 `pm3AiParse()` 自动调用

### 如果没有自动触发，排查方向
- 找到 admin.html 里的 `onAiFileChange` 函数，确认末尾有调用 `pm3AiParse()`
- 找到 `pm3AiParse` 函数，确认逻辑正确

---

## 任务 3：文章详情页展示原文来源栏

### 背景
爬虫抓取的文章可能只有摘要（content < 300字），需要展示「原文来源」链接引导用户去读全文。

### 当前限制
现有数据库里的文章 `source_url` 字段都是 NULL（旧数据），所以无法直接测试。

### 验证方法（需手动插入测试数据）

在 Mac 上运行：
```bash
cp /Volumes/docker/himiao-data/db/himiao.db /tmp/himiao_test.db
sqlite3 /tmp/himiao_test.db "
  UPDATE articles
  SET source_url = 'https://finance.sina.com.cn/test',
      is_published = 1,
      content_zh = '这是一段很短的测试内容。'
  WHERE id = (SELECT id FROM articles WHERE is_published = 1 LIMIT 1);
"
cp /tmp/himiao_test.db /Volumes/docker/himiao-data/db/himiao.db
```

然后访问对应文章的详情页，查看是否出现「原文来源」栏。

### 预期结果
- content < 300字 且 source_url 不为空时，显示橙色警告「当前仅显示摘要…」
- 显示「📰 原文来源：[保司名称]（可点击链接）」

### 已做的修复（待验证）
- `article.html` 中 `renderArticle()` 末尾加了 `article-source-bar` div 逻辑

---

## 注意事项
- 后台 JS 错误通常被 try/catch 吞掉，**必须打开浏览器控制台**才能看到
- 改完代码后前端无需重启，直接 Cmd+Shift+R 强刷即可
- 后端代码 `/Volumes/docker/himiao-backend/app/` 也是 volume 挂载，改完直接生效
