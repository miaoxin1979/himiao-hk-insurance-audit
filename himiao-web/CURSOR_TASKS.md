# Cursor 待办任务清单

## 1. CJK 标点位置 bug
**文件**：全站 CSS（可能在 `css/` 目录或各页面 `<style>` 标签）
**问题**：中文逗号（，）、句号（。）渲染在字符格正中间，而非左下角
**修法**：检查字体 font-feature-settings，或对中文文本块加 `font-feature-settings: "halt" 1` / `"chws" 1`；或换用正确支持 CJK 标点的字体栈

---

## 2. product-detail.html — 动态化 `<title>` 和 meta
**文件**：`product-detail.html` 第 6-11 行
**问题**：`<title>` 和 og:title/description 都 hardcoded 为 "AIA 充裕未来 III"
**修法**：在 `renderMeta()` 里用 JS 更新：
```js
document.title = p1.meta.name + ' 精算备注 | HiMiao';
document.querySelector('meta[property="og:title"]').content = p1.meta.name + ' | HiMiao';
```

---

## 3. product-detail.html — 清除 hardcoded AIA 静态内容
**文件**：`product-detail.html`
**问题**：页面内有大量针对"AIA 充裕未来 III"的静态分析文字（风险分析段落、情景测算说明、压测文字等），对其他产品显示时内容完全错误
**修法**：
- 搜索页面内所有出现"充裕未来"、"AIA"的 hardcoded 文字节点，删除或替换为通用描述
- "简单模式"里的静态描述句（如"年化收益率约 5.82%，优于定期存款..."）改为由 JS 动态填入
- 压测/情景分析相关的静态表格和段落：暂时用"数据完善中"占位，或直接隐藏

---

## 4. product-detail.html — 评分圆环动态化
**文件**：`product-detail.html` 第 1364-1374 行
**问题**：SVG 评分圆环的 stroke-dashoffset（决定填充比例）和中间数字"80"均为 hardcoded
**修法**：在 `renderMeta()` 中根据 `sc.total` 动态更新：
```js
var scoreEl = document.querySelector('.score-center span:first-child');
if (scoreEl && sc) scoreEl.textContent = sc.total;
// SVG圆周 = 175.9，offset = 175.9 * (1 - sc.total/100)
var circle = document.querySelector('.score-ring circle:last-child');
if (circle && sc) circle.setAttribute('stroke-dashoffset', (175.9 * (1 - sc.total/100)).toFixed(1));
```

---

## 优先级
1 > 3 > 2 > 4
