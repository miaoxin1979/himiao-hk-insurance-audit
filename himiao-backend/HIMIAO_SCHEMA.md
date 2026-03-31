# HiMiao 全局架构与字段字典
> 任何 Claude 窗口开始工作前先读此文件。最后更新：2026-03-07

---

## 项目概览
香港保险产品审计平台。前端展示独立精算数据，后台管理员录入/AI解析产品数据。

- Backend: FastAPI port 8888 | `/Volumes/docker/himiao-backend/`
- Frontend: nginx 静态 port 8080 | `/Volumes/docker/himiao-web/`
- NAS: YOUR_NAS_IP | Mac Mini (Ollama deepseek-r1:32b): YOUR_MAC_IP
- 数据库: SQLite，路径见 `app/db/session.py`

---

## 险种（3个，已冻结，不再新增）

| type_key         | 中文     | Admin Tab | 前端路由                        |
|------------------|----------|-----------|-------------------------------|
| `savings`        | 储蓄分红险 | 💰 储蓄险  | product-list.html?type=savings |
| `whole_life`     | 终身寿险   | 🛡️ 终身寿险 | product-list.html?type=whole_life |
| `critical_illness` | 重疾险  | ❤️ 重疾险  | product-list.html?type=critical_illness |

> medical / annuity 已从全栈删除（2026-03-07）

---

## API 路由

```
GET/POST   /api/v1/products/savings
PUT/PATCH/DELETE /api/v1/products/savings/{product_code}

GET/POST   /api/v1/products/whole_life
PUT/PATCH/DELETE /api/v1/products/whole_life/{product_code}

GET/POST   /api/v1/products/critical_illness  (endpoint文件名: products_critical.py)
PUT/PATCH/DELETE /api/v1/products/critical_illness/{product_code}
```

---

## 公共基础字段（所有险种共用）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product_code` | str | ✅ | 唯一代码，英文+下划线，创建后不可改 |
| `insurer` | str | ✅ | 保司简称，如 AIA / Prudential / Manulife |
| `insurer_full` | str | — | 保司全称（官方注册名）|
| `product_name_cn` | str | ✅ | 产品中文名称（简体）|
| `product_name_en` | str | — | 产品英文名称 |
| `currency` | str | — | USD（默认）/ HKD |
| `premium_years` | int | — | 缴费年期（1-100）|
| `premium_annual` | float | — | 示例年缴保费（原币）|
| `is_published` | bool | — | 默认 False，人工审核后改 True 才公开 |
| `data_source_url` | str | — | 保司官方披露文件 URL |
| `audit_note` | str | — | 精算观察备注（客观陈述）|

---

## 储蓄分红险 Savings — 专有字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `irr_20y` | float% | 20年 IRR，核心比较指标 |
| `irr_10y` | float% | 10年 IRR |
| `breakeven_year` | int | 保证回本年数（保证现金价值 ≥ 已缴保费）|
| `dividend_fulfillment_5y` | float% | 过去5年分红实现率（0-200%）|
| `non_guaranteed_ratio` | float% | 非保证收益占比 |
| `max_early_exit_loss_pct` | float% | 早期退保最大损失比例 |
| `policy_loan_ltv` | float% | 保单贷款成数上限 |
| `guaranteed_cash_value_10y` | float | 第10年保证现金价值（原币）|
| `total_cash_value_20y` | float | 第20年总现金价值（含非保证，中性情景，原币）|

**比较基准**：30岁女 / 5年缴 / USD 100k/年

---

## 终身寿险 Whole Life — 专有字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `irr_20y` | float% | 20年 IRR |
| `irr_30y` | float% | 30年 IRR |
| `breakeven_year` | int | 保证回本年数 |
| `dividend_fulfillment_5y` | float% | 过去5年分红实现率 |
| `non_guaranteed_ratio` | float% | 非保证收益占比 |
| `policy_loan_ltv` | float% | 保单贷款成数上限 |
| `death_benefit_guaranteed_pct` | float% | 保证身故赔付（% of 保额）|
| `death_benefit_total_20y_pct` | float% | 第20年总身故赔付（% of 保额，含非保证，中性）|
| `cash_value_10y` | float | 第10年现金价值（原币）|
| `cash_value_20y` | float | 第20年现金价值（原币）|
| `max_early_exit_loss_pct` | float% | 早期退保最大损失比例 |

**比较基准**：30岁女 / 10年缴 / USD 100万保额

---

## 重疾险 Critical Illness — 专有字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `covered_conditions` | int | 涵盖重疾病种总数 |
| `early_stage_conditions` | int | 涵盖早期/轻症病种数 |
| `multipay_max_pct` | float% | 多重赔付上限（% of 基本保额）|
| `multipay_times` | int | 最大理赔次数 |
| `cancer_relapse_covered` | bool | 癌症复发是否可独立再次理赔 |
| `premium_waiver_on_claim` | bool | 理赔后是否豁免后续保费 |
| `sum_assured_preserves` | bool | 多重赔付后寿险保额是否不减 |
| `sum_assured_example` | float | 示例保额（原币）|
| `premium_example_annual` | float | 对应示例保额年缴保费（原币）|
| `return_of_premium_year` | int | 保费返还年期（0=不返还）|

**比较基准**：30岁女 / 20年缴 / USD 100万保额

---

## 合规红线（V8.0，不可违反）

```
✗ 严禁字段：is_recommended / suitable_for / best_for / 性价比 / 推荐人群
✓ 仅允许：客观精算数值 + 公开披露事实
```

---

## 关键代码文件

| 文件 | 作用 |
|------|------|
| `app/models/product.py` | SQLAlchemy ORM 主表（ProductType 枚举）|
| `app/models/products_typed.py` | Pydantic 请求/响应模型（3险种）|
| `app/api/v1/router.py` | 路由总汇 |
| `app/api/v1/endpoints/products_savings.py` | 储蓄险 CRUD |
| `app/api/v1/endpoints/products_whole_life.py` | 终身寿险 CRUD |
| `app/api/v1/endpoints/products_critical.py` | 重疾险 CRUD |
| `app/services/ai_parser.py` | PDF → Ollama → JSON 解析服务 |
| `app/db/session.py` | SQLAlchemy Session / get_db 依赖 |

---

## 当前已知技术债

1. ~~**P0** — 三个 type endpoint 用内存字典~~ ✅ **已完成（2026-03-07）**
   - 三个 endpoint 均已接真实 DB（`get_db` + `require_admin`）
   - 字段映射：product_code→slug, insurer→company, policy_loan_ltv→loan_ltv，专有字段→specifications JSON

2. **P1** — AI 解析未闭环
   - `ai_parser.py` 解析结果还未自动写入对应险种 endpoint

3. **P2** — 新闻 spider 只覆盖 AIA，需扩展

---

## 产品数据参考

详见 `docs/PRODUCT_DATA_REFERENCE.md`：
- 储蓄险：24个产品，基准 30岁女/5年缴/USD 100k/yr
- 终身寿险：14个产品，基准 30岁女/10年缴/USD 100万
- 重疾险：11个产品，基准 30岁女/20年缴/USD 100万
