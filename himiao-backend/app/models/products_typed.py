"""
app/models/products_typed.py
────────────────────────────
三大险种的 Pydantic 请求/响应模型：储蓄险 / 终身寿险 / 重疾险

⚠️  V8.0 合规红线（最高警告）
    所有字段只允许客观精算数据与公开披露事实。
    严禁出现任何主观推介字段，例如：
      ✗ is_recommended / suitable_for / best_for
      ✗ 性价比 / 推荐人群 / 适合年龄
      ✗ 任何含"最优/推荐/建议"语义的字段名或描述
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════
#  公共基础字段（四大险种共用）
# ══════════════════════════════════════════════════════════════

class _ProductBase(BaseModel):
    """所有险种共用的元信息字段。"""
    product_code:    str            = Field(...,  description="产品唯一代码，英文+下划线，创建后不可修改")
    insurer:         str            = Field(...,  description="保司简称，如 AIA / Prudential / Manulife")
    insurer_full:    Optional[str]  = Field(None, description="保司全称（官方注册名）")
    product_name_cn: str            = Field(...,  description="产品中文名称（简体）")
    product_name_en: Optional[str]  = Field(None, description="产品英文名称")
    currency:        str            = Field("USD", description="保单货币：USD / HKD")
    premium_years:   Optional[int]  = Field(None, description="缴费年期（整数年）", ge=1, le=100)
    premium_annual:  Optional[float]= Field(None, description="示例年缴保费（原币）", ge=0)
    is_published:    bool           = Field(False, description="是否在前端公开展示")
    data_source_url: Optional[str]  = Field(None, description="数据来源 URL（保司官方披露文件）")
    audit_note:      Optional[str]  = Field(None, description="精算观察备注（客观陈述，禁止主观推介）")


# ══════════════════════════════════════════════════════════════
#  储蓄分红险  Savings
# ══════════════════════════════════════════════════════════════

class SavingsProductBase(_ProductBase):
    """
    储蓄分红险特有字段。
    核心精算指标：IRR / 回本年 / 分红实现率 / 非保证比例 / 流动性损失。
    """
    irr_20y:                    Optional[float] = Field(None, description="20年内部收益率 IRR（%）", ge=0, le=100)
    irr_10y:                    Optional[float] = Field(None, description="10年 IRR（%）", ge=0, le=100)
    breakeven_year:             Optional[int]   = Field(None, description="保证回本年数（保证现金价值 ≥ 已缴保费）", ge=1)
    dividend_fulfillment_5y:    Optional[float] = Field(None, description="过去5年分红实现率（%）", ge=0, le=200)
    non_guaranteed_ratio:       Optional[float] = Field(None, description="非保证收益占比（%）", ge=0, le=100)
    max_early_exit_loss_pct:    Optional[float] = Field(None, description="早期退保最大损失比例（%）", ge=0, le=100)
    policy_loan_ltv:            Optional[float] = Field(None, description="保单贷款成数上限（%）", ge=0, le=100)
    guaranteed_cash_value_10y:  Optional[float] = Field(None, description="第10年保证现金价值（原币）", ge=0)
    total_cash_value_20y:       Optional[float] = Field(None, description="第20年总现金价值（含非保证，中性情景，原币）", ge=0)


class SavingsProductCreate(SavingsProductBase):
    pass


class SavingsProductUpdate(BaseModel):
    """PATCH 更新：所有字段均可选。"""
    insurer:                    Optional[str]   = None
    insurer_full:               Optional[str]   = None
    product_name_cn:            Optional[str]   = None
    product_name_en:            Optional[str]   = None
    currency:                   Optional[str]   = None
    premium_years:              Optional[int]   = Field(None, ge=1, le=100)
    premium_annual:             Optional[float] = Field(None, ge=0)
    irr_20y:                    Optional[float] = Field(None, ge=0, le=100)
    irr_10y:                    Optional[float] = Field(None, ge=0, le=100)
    breakeven_year:             Optional[int]   = Field(None, ge=1)
    dividend_fulfillment_5y:    Optional[float] = Field(None, ge=0, le=200)
    non_guaranteed_ratio:       Optional[float] = Field(None, ge=0, le=100)
    max_early_exit_loss_pct:    Optional[float] = Field(None, ge=0, le=100)
    policy_loan_ltv:            Optional[float] = Field(None, ge=0, le=100)
    guaranteed_cash_value_10y:  Optional[float] = Field(None, ge=0)
    total_cash_value_20y:       Optional[float] = Field(None, ge=0)
    is_published:               Optional[bool]  = None
    data_source_url:            Optional[str]   = None
    audit_note:                 Optional[str]   = None


class SavingsProductOut(SavingsProductBase):
    id: int = Field(..., description="数据库主键")

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
#  终身寿险  Whole Life
# ══════════════════════════════════════════════════════════════

class WholeLifeProductBase(_ProductBase):
    """
    终身寿险特有字段。
    核心精算指标：IRR / 身故赔付倍数 / 分红实现率 / 保单贷款成数。
    """
    irr_20y:                        Optional[float] = Field(None, description="20年内部收益率 IRR（%）", ge=0, le=100)
    irr_30y:                        Optional[float] = Field(None, description="30年 IRR（%）", ge=0, le=100)
    breakeven_year:                 Optional[int]   = Field(None, description="保证回本年数", ge=1)
    dividend_fulfillment_5y:        Optional[float] = Field(None, description="过去5年分红实现率（%）", ge=0, le=200)
    non_guaranteed_ratio:           Optional[float] = Field(None, description="非保证收益占比（%）", ge=0, le=100)
    policy_loan_ltv:                Optional[float] = Field(None, description="保单贷款成数上限（%）", ge=0, le=100)
    death_benefit_guaranteed_pct:   Optional[float] = Field(None, description="保证身故赔付（% of 保额）", ge=0)
    death_benefit_total_20y_pct:    Optional[float] = Field(None, description="第20年总身故赔付（% of 保额，含非保证，中性情景）", ge=0)
    cash_value_10y:                 Optional[float] = Field(None, description="第10年现金价值（原币）", ge=0)
    cash_value_20y:                 Optional[float] = Field(None, description="第20年现金价值（原币）", ge=0)
    max_early_exit_loss_pct:        Optional[float] = Field(None, description="早期退保最大损失比例（%）", ge=0, le=100)


class WholeLifeProductCreate(WholeLifeProductBase):
    pass


class WholeLifeProductUpdate(BaseModel):
    """PATCH 更新：所有字段均可选。"""
    insurer:                        Optional[str]   = None
    insurer_full:                   Optional[str]   = None
    product_name_cn:                Optional[str]   = None
    product_name_en:                Optional[str]   = None
    currency:                       Optional[str]   = None
    premium_years:                  Optional[int]   = Field(None, ge=1, le=100)
    premium_annual:                 Optional[float] = Field(None, ge=0)
    irr_20y:                        Optional[float] = Field(None, ge=0, le=100)
    irr_30y:                        Optional[float] = Field(None, ge=0, le=100)
    breakeven_year:                 Optional[int]   = Field(None, ge=1)
    dividend_fulfillment_5y:        Optional[float] = Field(None, ge=0, le=200)
    non_guaranteed_ratio:           Optional[float] = Field(None, ge=0, le=100)
    policy_loan_ltv:                Optional[float] = Field(None, ge=0, le=100)
    death_benefit_guaranteed_pct:   Optional[float] = Field(None, ge=0)
    death_benefit_total_20y_pct:    Optional[float] = Field(None, ge=0)
    cash_value_10y:                 Optional[float] = Field(None, ge=0)
    cash_value_20y:                 Optional[float] = Field(None, ge=0)
    max_early_exit_loss_pct:        Optional[float] = Field(None, ge=0, le=100)
    is_published:                   Optional[bool]  = None
    data_source_url:                Optional[str]   = None
    audit_note:                     Optional[str]   = None


class WholeLifeProductOut(WholeLifeProductBase):
    id: int = Field(..., description="数据库主键")

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
#  重疾险  Critical Illness
# ══════════════════════════════════════════════════════════════

class CriticalProductBase(_ProductBase):
    """
    重疾险特有字段。
    核心精算指标：保障病种数 / 多重赔付 / 早期重疾 / 保费豁免。
    """
    covered_conditions:         Optional[int]   = Field(None, description="涵盖重疾病种总数", ge=1)
    early_stage_conditions:     Optional[int]   = Field(None, description="涵盖早期/轻症病种数", ge=0)
    multipay_max_pct:           Optional[float] = Field(None, description="多重赔付上限（%，相对于基本保额）", ge=0)
    multipay_times:             Optional[int]   = Field(None, description="最大理赔次数", ge=1)
    cancer_relapse_covered:     Optional[bool]  = Field(None, description="癌症复发是否可独立再次理赔")
    premium_waiver_on_claim:    Optional[bool]  = Field(None, description="理赔后是否豁免后续保费")
    sum_assured_preserves:      Optional[bool]  = Field(None, description="多重赔付后寿险保额是否不减")
    sum_assured_example:        Optional[float] = Field(None, description="示例保额（原币）", ge=0)
    premium_example_annual:     Optional[float] = Field(None, description="对应示例保额的年缴保费（原币）", ge=0)
    return_of_premium_year:     Optional[int]   = Field(None, description="保费返还年期（0=不返还）", ge=0)


class CriticalProductCreate(CriticalProductBase):
    pass


class CriticalProductUpdate(BaseModel):
    insurer:                    Optional[str]   = None
    insurer_full:               Optional[str]   = None
    product_name_cn:            Optional[str]   = None
    product_name_en:            Optional[str]   = None
    currency:                   Optional[str]   = None
    premium_years:              Optional[int]   = Field(None, ge=1, le=100)
    premium_annual:             Optional[float] = Field(None, ge=0)
    covered_conditions:         Optional[int]   = Field(None, ge=1)
    early_stage_conditions:     Optional[int]   = Field(None, ge=0)
    multipay_max_pct:           Optional[float] = Field(None, ge=0)
    multipay_times:             Optional[int]   = Field(None, ge=1)
    cancer_relapse_covered:     Optional[bool]  = None
    premium_waiver_on_claim:    Optional[bool]  = None
    sum_assured_preserves:      Optional[bool]  = None
    sum_assured_example:        Optional[float] = Field(None, ge=0)
    premium_example_annual:     Optional[float] = Field(None, ge=0)
    return_of_premium_year:     Optional[int]   = Field(None, ge=0)
    is_published:               Optional[bool]  = None
    data_source_url:            Optional[str]   = None
    audit_note:                 Optional[str]   = None


class CriticalProductOut(CriticalProductBase):
    id: int = Field(..., description="数据库主键")

    class Config:
        from_attributes = True


