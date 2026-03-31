"""保险知识讲堂：首次部署时写入示例内容（幂等）"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.article import Article


def seed_academy_articles(db: Session) -> None:
    if db.query(Article).filter(Article.channel == "academy").first():
        return

    now = datetime.now(timezone.utc)
    samples: list[dict] = [
        {
            "slug": "academy-why-disclosure",
            "title_zh": "投保前为什么要「如实告知」？",
            "excerpt": "理解最高诚信原则：哪些信息需要告诉保险公司，遗漏可能带来什么后果。",
            "category": "guide",
            "read_min": 4,
            "content_zh": """<p>在多数司法辖区，保险合同建立在<strong>最高诚信（Utmost Good Faith）</strong>基础上。投保时，您会被要求填写健康、职业、既往病史等信息。</p>
<p><strong>建议做法：</strong>按问卷逐项核对，不确定时可保留记录或向持牌顾问求证；不要猜测或故意隐瞒。</p>
<p class="hm-disclaimer" style="margin-top:1.5rem;padding:12px;border-left:3px solid #c9a227;background:rgba(201,162,39,0.08);font-size:13px;color:#444;">本文为通识教育，不构成任何投保建议。具体以保单条款及持牌中介意见为准。</p>""",
        },
        {
            "slug": "academy-read-policy-3-steps",
            "title_zh": "读懂保单：新手可照做的三个步骤",
            "excerpt": "从保障范围、免责条款到现金价值表，用结构化方式阅读长篇保单。",
            "category": "guide",
            "read_min": 5,
            "content_zh": """<ol>
<li><strong>先看清「保什么」</strong>：保障责任、给付条件、是否含身故/重疾/医疗等。</li>
<li><strong>再核对「不保什么」</strong>：免责条款与等待期，避免理赔预期偏差。</li>
<li><strong>最后看「钱怎么算」</strong>：保费缴费期、现金价值（如适用）、退保可能损失。</li>
</ol>
<p>可将关键页打印或标注，便于日后与顾问复核。</p>
<p class="hm-disclaimer" style="margin-top:1.5rem;padding:12px;border-left:3px solid #c9a227;background:rgba(201,162,39,0.08);font-size:13px;color:#444;">本文为通识教育，不构成任何投保建议。</p>""",
        },
        {
            "slug": "academy-compare-dimensions",
            "title_zh": "比较储蓄险时，建议关注哪些维度？",
            "excerpt": "从产品结构、币种、流动性到保险公司财务披露，建立个人化的比较清单。",
            "category": "guide",
            "read_min": 6,
            "content_zh": """<p>不同读者关注点不同，下面是一份<strong>中性</strong>的参考维度（非排名、非推荐）：</p>
<ul>
<li>保证 vs 非保证利益的披露方式与历史实现情况（仅供参考，不代表未来）</li>
<li>提领/部分退保规则与潜在费用</li>
<li>保单货币与汇率风险</li>
<li>保司公开信息：偿付能力、评级披露（以官方为准）</li>
</ul>
<p>建议结合自身现金流、持有期与税务/合规环境，与持牌顾问讨论。</p>
<p class="hm-disclaimer" style="margin-top:1.5rem;padding:12px;border-left:3px solid #c9a227;background:rgba(201,162,39,0.08);font-size:13px;color:#444;">本文为通识教育，不构成任何投保或投资建议。</p>""",
        },
    ]

    for row in samples:
        db.add(
            Article(
                slug=row["slug"],
                title_zh=row["title_zh"],
                excerpt=row["excerpt"],
                content_zh=row["content_zh"],
                category=row["category"],
                channel="academy",
                content_format="html",
                author="HiMiao 精算团队",
                read_min=row["read_min"],
                is_published=True,
                published_at=now,
                is_hot=False,
                tags=["保险讲堂", "通识"],
            )
        )
    db.commit()
