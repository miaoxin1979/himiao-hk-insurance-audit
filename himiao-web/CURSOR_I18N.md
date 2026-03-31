# CURSOR 任务：全站三语言（简体/繁体/英文）彻底修复

## 背景
HiMiao 支持三种语言：`cn`（简体）/ `hk`（繁体）/ `en`（英文），通过 localStorage `himiao-lang` 切换。

核心文件：
- 字典：`/Volumes/docker/himiao-web/components/lang.js`（HM_DICT）
- 引擎：`/Volumes/docker/himiao-web/components/i18n-engine.js`
- 页面：index.html / product-list.html / product-detail.html / compare.html / news.html / article.html / about.html

---

## 任务：找出并修复所有 i18n 问题

### Step 1：修复 lang.js 缺失的 key
以下 key 在 HTML 的 `data-i18n=""` 中被引用，但在 lang.js 中不存在，切换语言时会显示 key 名而非文字：

```
filter_launch_year   (product-list.html)
tab_wholelife        (product-list.html)
latest_label         (news.html)
lbl_compare_hint     (product-detail.html)
lbl_compare_peer     (product-detail.html)
```

请在 lang.js 的 cn / hk / en 三个块里都补上这 5 个 key，翻译合理即可。

---

### Step 2：清理 lang.js 孤儿 key（年金险/医疗险已下线）
以下 key 在任何 HTML 中都不再使用，是已删除的年金险/医疗险遗留的死代码，全部删除：

```
an1_* an2_* an3_* an_btn_list annuity_h2 annuity_sub
m1_* m2_* m3_* m_btn_list medical_h2 medical_sub
tab_annuity tab_medical
```

---

### Step 3：修复 JS 中硬编码的中文（切语言后不变）
各页面 `<script>` 里有大量直接写死的中文字符串，切换到 HK/EN 后这些文字不会变。

**处理方式**：
- 对于短 label（如按钮文字、状态文字）：从 HM_DICT 读取，或在 JS 里写 `{cn:'…', hk:'…', en:'…'}` 对象按当前语言取值
- 工具函数：`window.HM_I18N?.t(key)` 或 `HM_DICT[currentLang][key]`

**重点文件（问题最多）**：

1. **product-detail.html**（133 处）
   - 微信咨询弹窗文字（"微信咨询"、"添加微信，免费咨询"等）
   - 表格表头（"核心数据对比"、"已缴保费"等）
   - KPI 单位（"年"、"港元"、"美元"）
   - 险种标签 `{ savings:'储蓄险', whole_life:'终身寿险', critical_illness:'重疾险' }`
   - 页面 title/description 动态拼接（含"精算审计报告"）

2. **compare.html**（97 处）
   - tag 翻译字典写在 JS 里（硬编码 cn→hk/en 映射），应整合进 lang.js
   - 表头文字（"险种"、"公司"、"货币"等列名）

3. **news.html**（31 处）
   - 分类名 `CAT_FB = { market:'市场情报', alert:'避雷预警', ... }` 硬编码
   - 加载中、加载失败提示文字

4. **article.html**（18 处）
   - 分类名同上
   - "暂无正文内容"、"请输入有效邮箱"、"提交中…"、"订阅成功"等

5. **index.html**（34 处）
   - 英雄区新闻链接文字（已有三语言判断但写成 if/else 而非字典）
   - 计算器结果文字（"未达回本"、"已回本"等）

6. **product-list.html**（46 处）
   - "数据更新"标签
   - "筛选"/"关闭"按钮文字
   - 保司名称映射对象

7. **about.html**（1 处）
   - 区域提示 banner 硬编码中文

---

### Step 4：验证方法
每修一个页面，在浏览器 Console 执行以下切换，检查没有遗漏的中文：
```js
// 切英文
localStorage.setItem('himiao-lang','en'); location.reload();
// 切繁体
localStorage.setItem('himiao-lang','hk'); location.reload();
// 切回简体
localStorage.setItem('himiao-lang','cn'); location.reload();
```

---

## 约束
- **lang.js 是唯一字典**，不允许在其他文件另建翻译对象，JS 里的 `{cn,hk,en}` 临时对象也要最终合并进 lang.js
- admin.html 不需要 i18n，跳过
- 改完前端无需重启容器，Cmd+Shift+R 强刷即可
- 前端文件路径：`/Volumes/docker/himiao-web/`
