"""
保司评级种子 — 后端启动时自动执行，无需手动运行
"""
from datetime import date

from app.models.insurer_rating import InsurerRating

# 官方披露数据，与 Product.company 匹配
INSURER_RATINGS = [
    {"company": "AIA", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.aia.com/en/investor-relations/overview/credit-investors",
     "as_of_date": date(2024, 6, 1), "note": "AIA Group Limited 集团层面"},
    {"company": "Prudential", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.prudential.com.hk/en/all-news/prudential-hong-kong-assigned-credit-ratings-by-s-n-p-global-ratings-including-aa--financial-strength-rating/",
     "as_of_date": date(2024, 1, 12), "note": "Prudential Hong Kong 财务实力评级"},
    {"company": "Manulife", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.manulife.com/en/investors/ratings.html",
     "as_of_date": date(2024, 6, 1), "note": "Manulife Financial 集团层面"},
    {"company": "Sun Life", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.sunlife.com/en/investors/",
     "as_of_date": date(2024, 6, 1), "note": "Sun Life Financial 集团层面"},
    {"company": "Zurich", "rating": "AA", "agency": "S&P",
     "source_url": "https://www.zurich.com/en/investor-relations",
     "as_of_date": date(2024, 6, 1), "note": "苏黎世保险集团"},
    {"company": "HSBC", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.hsbc.com/investors/",
     "as_of_date": date(2024, 6, 1), "note": "汇丰集团"},
    {"company": "FWD", "rating": "A", "agency": "S&P",
     "source_url": "https://www.fwd.com/en/investor-relations/",
     "as_of_date": date(2024, 6, 1), "note": "富卫集团"},
    {"company": "YF Life", "rating": "A", "agency": "S&P",
     "source_url": "https://www.yflife.com/en/about-us/",
     "as_of_date": date(2024, 6, 1), "note": "万通保险"},
    {"company": "China Life", "rating": "A", "agency": "S&P",
     "source_url": "https://www.chinalife.com.hk/en/investor-relations/",
     "as_of_date": date(2024, 6, 1), "note": "中国人寿海外"},
    {"company": "BOC Life", "rating": "A", "agency": "S&P",
     "source_url": "https://www.boclifepension.com/",
     "as_of_date": date(2024, 6, 1), "note": "中银人寿"},
    {"company": "AXA", "rating": "AA-", "agency": "S&P",
     "source_url": "https://www.axa.com/investor/financial-strength-ratings",
     "as_of_date": date(2025, 10, 3), "note": "AXA SA 集团主要保险子公司"},
    {"company": "CTFLife", "rating": "A-", "agency": "Fitch",
     "source_url": "https://www.ctflife.com.hk/en/about-ctflife/about-us",
     "as_of_date": date(2025, 10, 1), "note": "周大福人寿，Fitch 财务实力评级"},
]


def seed_insurer_ratings(session):
    """幂等种子：有则更新，无则插入"""
    for r in INSURER_RATINGS:
        existing = session.query(InsurerRating).filter(
            InsurerRating.company == r["company"],
            InsurerRating.agency == r["agency"],
        ).first()
        if existing:
            existing.rating = r["rating"]
            existing.source_url = r["source_url"]
            existing.as_of_date = r["as_of_date"]
            existing.note = r.get("note")
        else:
            session.add(InsurerRating(**r))
    session.commit()
