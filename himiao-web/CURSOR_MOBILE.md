# CURSOR 任务：全站手机端适配

## 目标
所有页面在 375px（iPhone SE）～ 430px（iPhone 15 Pro Max）宽度下正常使用，不出现横向滚动条，文字可读，按钮可点击。

## 验证环境
Chrome DevTools → 切换到 iPhone 14 Pro 设备（390×844），每改一个页面在这里预览。

---

## 紧急问题（先修）

### P0-1：product-detail.html 缺少 viewport meta
`product-detail.html` 的 `<head>` 里**没有** viewport meta，手机端会以桌面宽度渲染，字极小。
立即在 `<head>` 加：
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### P0-2：Nav 汉堡菜单（components/nav.js）
当前导航在手机上挤成一排或溢出。需要：
- ≤768px 时，隐藏桌面导航链接
- 显示右上角汉堡图标（☰）
- 点击弹出全屏或侧滑菜单（保持语言切换功能）
- 菜单项和桌面版一致（首页、产品榜单、对比、情报站、关于）
- 点击遮罩/关闭按钮收起
nav.js 是注入到所有页面的共享组件，**改一处全站生效**。

---

## 逐页适配

### 1. index.html（首页）
当前：完全无 @media，手机全坏
需要修复：
- 英雄区文字（标题/副标题）：手机端字号缩小，padding 收紧
- 三栏产品轮播卡片：手机端改为单栏或横向滑动
- 计算器区块：输入框/按钮全宽，结果数字不要溢出
- Ticker 跑马灯：保留，字号适当
- Footer：多栏改单栏堆叠
- CTA 按钮：宽度 100%

### 2. product-list.html（产品榜单）
当前：已有基础响应式，问题最少
需要修复：
- 左侧筛选面板（Sidebar）：手机端收起为底部抽屉（已有部分实现，确认能用）
- 产品卡片：确保 375px 下不溢出
- 排序/筛选 toolbar：手机端紧凑化

### 3. product-detail.html（产品详情）
当前：有部分 @media 但不完整，且缺 viewport
需要修复：
- KPI 数字区：4格 → 手机端 2×2 网格
- Tab 切换（概览/DNA/档案）：Tab 文字缩短或改图标，可横向滑动
- 情景对比按钮组（乐观/中性/悲观）：手机全宽排列
- 精算数据表格：横向可滚动（`overflow-x: auto` 包裹）
- 微信咨询浮动按钮：确保不遮挡内容
- 底部对比栏：手机端贴底固定，按钮可点

### 4. compare.html（产品对比）
当前：完全无 @media，是最难适配的页面
需要修复：
- 对比表格（多列）：横向滚动容器（`overflow-x: auto`），固定第一列（行标签）
- 顶部产品选择区：手机端竖排
- 筛选/重置按钮：全宽
- 数值行：数字不换行（`white-space: nowrap`）

### 5. news.html（情报站）
当前：有 @media 768px，基本可用
需要修复：
- 顶部大图新闻卡：手机端高度压缩，文字左对齐
- 文章列表卡片：确认间距在 375px 下合适
- 分类 Tab 筛选：横向可滑动，不折行

### 6. article.html（文章详情）
当前：有基础响应式
需要修复：
- 正文内容宽度：375px 下 padding 不能太小（至少 16px 左右各）
- 图片：`max-width: 100%`
- 代码块：横向可滚动
- 底部订阅区：表单全宽

### 7. about.html（关于）
当前：有 @media 768px，最简单
需要修复：
- 团队/数据展示区：多列改单列
- 区域提示 Banner：字号缩小，不溢出

---

## 通用原则（适用所有页面）

```css
/* 加在每个页面的全局 CSS 里 */
*, *::before, *::after { box-sizing: border-box; }
img, video { max-width: 100%; height: auto; }
table { width: 100%; }

@media (max-width: 768px) {
  /* 字号 */
  body { font-size: 14px; }
  h1 { font-size: 24px; }
  h2 { font-size: 20px; }

  /* 容器 */
  .container, [class*="container"] { padding-left: 16px; padding-right: 16px; }

  /* 多栏变单栏 */
  [class*="grid"], [class*="cols"] { grid-template-columns: 1fr !important; }
  [class*="flex-row"] { flex-direction: column !important; }
}
```

---

## 触摸体验优化
- 所有可点击元素：最小 44×44px 点击区域（iOS HIG 标准）
- 按钮 padding：至少 `12px 20px`
- 链接之间间距：至少 8px
- 禁止 `user-select: none` 在正文区

---

## 不需要做的
- admin.html（后台不考虑手机）
- PWA / 离线缓存（超出范围）
- 专门的手机版 APP（纯响应式即可）

---

## 文件路径
所有前端文件在 `/Volumes/docker/himiao-web/`，改完 Cmd+Shift+R 强刷，无需重启容器。
