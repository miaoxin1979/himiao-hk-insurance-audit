# HiMiao 架构决策记录 V1.0
> 状态：冻结。所有变更必须通过变更提案，不可口头修改。

---

## 一、数据库结构

**决策：主表 + 子表 + product_metrics 独立计算表，软关联**

- SQLite 环境下软关联优于复杂外键（外键约束性能一般、complex join 会慢、migration 成本高）
- `product_metrics` 独立表存衍生结果，带 `calculated_at` 时间戳，可控刷新
- 应用层保证一致性（非数据库外键）
- **必须实现**：删除主表 product 时，应用层自动清理所有子表；定期一致性扫描脚本

---

## 二、险种范围

**当前险种：3个（已从4个精简，移除医疗险和年金险）**

| 险种 | product_type | 状态 |
|------|-------------|------|
| 储蓄分红险 | savings | ✅ 保留 |
| 终身寿险 | whole_life | ✅ 保留 |
| 重疾险 | critical_illness | ✅ 保留 |
| 高端医疗险 | medical | ❌ 已裁减 |
| 年金险 | annuity | ❌ 已裁减 |

> 代码里 medical / annuity 相关 endpoint、admin 表单、前端 tab 均需清理。

---

## 三、Phase 1 字段原则

**只存"可验证的原始数据"，不存"函数结果"**

Phase 1 排除（全部推迟到 Phase 2）：
- `participating_fund_equity_ratio`
- `mortality_table_reference`
- `investment_return_assumption_pct`
- 所有评分字段
- IRR 曲线 / cash_value_curve / volatility / liquidity / sensitivity

Phase 1 保留（高信噪比，真实可录入可验证）：
- `surrender_charge_schedule`
- `historical_dividend_array`

---

## 四、JSON 字段强制规范

- 强制结构定义（见数据字典）
- Admin 前端必须有格式校验
- 每个 JSON 字段必须含 `json_schema_version`（为未来升级预留）
- 数据字典写明格式、枚举值、示例

---

## 五、计算引擎分层

**实时计算（API 层）：**
- 比例类
- 简单派生函数

**Nightly 批量（写入 product_metrics）：**
- 波动率
- 敏感度
- 流动性评分
- 底层数据更新触发重算

---

## 六、合规三道闸（必须实现，非可选）

1. `eligible_residency` + `application_location_requirement` → 前端居住地判断
2. `product_status: Withdrawn / Suspended` → 自动标记并屏蔽展示
3. `verification_status: outdated` → 前端显示中性披露提示（非删除，非推介）

---

## 七、已知三年风险（已接受）

- SQLite 并发瓶颈：Phase 3 问题，现阶段单机 NAS + 有限 API，不过度设计
- 软关联脏数据风险：通过应用层删除触发器 + 定期扫描脚本缓解

---

## 八、项目部署环境

- NAS：Synology，IP `YOUR_NAS_IP`
- Backend：FastAPI，port `8888`，路径 `/Volumes/docker/himiao-backend/`
- Frontend：nginx 静态，port `8080`，路径 `/Volumes/docker/himiao-web/`
- Mac Mini M4 Pro：IP `YOUR_MAC_IP`，跑 Ollama（deepseek-r1:32b）
- AI pipeline：PDF URL → pdfplumber 提取文字 → Ollama 内网推理 → 写库（`ai_extracted=True`, `is_published=False`）
