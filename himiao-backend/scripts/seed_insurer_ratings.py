#!/usr/bin/env python3
"""
保司信用评级种子数据 — 须来自官方披露

运行方式（写入与后端相同的 himiao-data/db/himiao.db）：
  本地：python3 scripts/seed_insurer_ratings.py
  NAS/Docker：docker compose exec -w /app himiao-api python scripts/seed_insurer_ratings.py

合规要求：
- rating 必须来自标普(S&P)、穆迪(Moody's)、惠誉(Fitch) 等国际评级机构
- source_url 必填：指向保司投资者关系页或评级机构官网
- 定期复核更新，as_of_date 记录披露日期

数据来源（请核实后更新）：
- 标普: https://www.spglobal.com/ratings/
- 各保司投资者关系: AIA / Prudential / Manulife 等官网
"""
import os
import sys
from datetime import date

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.insurer_rating import InsurerRating


# 官方披露数据（company 与 Product.company 匹配：AIA / Prudential / Manulife 等）
# 请定期复核并更新 rating / source_url / as_of_date
INSURER_RATINGS = [
    {
        "company": "AIA",
        "rating": "AA-",
        "agency": "S&P",
        "source_url": "https://www.aia.com/en/investor-relations/overview/credit-investors",
        "as_of_date": date(2024, 6, 1),
        "note": "AIA Group Limited 集团层面",
    },
    {
        "company": "Prudential",
        "rating": "AA-",
        "agency": "S&P",
        "source_url": "https://www.prudential.com.hk/en/all-news/prudential-hong-kong-assigned-credit-ratings-by-s-n-p-global-ratings-including-aa--financial-strength-rating/",
        "as_of_date": date(2024, 1, 12),
        "note": "Prudential Hong Kong 财务实力评级",
    },
    {
        "company": "Manulife",
        "rating": "AA-",
        "agency": "S&P",
        "source_url": "https://www.manulife.com/en/investors/ratings.html",
        "as_of_date": date(2024, 6, 1),
        "note": "Manulife Financial 集团层面",
    },
    {
        "company": "Sun Life",
        "rating": "AA-",
        "agency": "S&P",
        "source_url": "https://www.sunlife.com/en/investors/",
        "as_of_date": date(2024, 6, 1),
        "note": "Sun Life Financial 集团层面",
    },
    {
        "company": "Zurich",
        "rating": "AA",
        "agency": "S&P",
        "source_url": "https://www.zurich.com/en/investor-relations",
        "as_of_date": date(2024, 6, 1),
        "note": "苏黎世保险集团",
    },
    {
        "company": "HSBC",
        "rating": "AA-",
        "agency": "S&P",
        "source_url": "https://www.hsbc.com/investors/",
        "as_of_date": date(2024, 6, 1),
        "note": "汇丰集团",
    },
    {
        "company": "FWD",
        "rating": "A",
        "agency": "S&P",
        "source_url": "https://www.fwd.com/en/investor-relations/",
        "as_of_date": date(2024, 6, 1),
        "note": "富卫集团，请以官网披露为准",
    },
    {
        "company": "YF Life",
        "rating": "A",
        "agency": "S&P",
        "source_url": "https://www.yflife.com/en/about-us/",
        "as_of_date": date(2024, 6, 1),
        "note": "万通保险，请以官网披露为准",
    },
    {
        "company": "China Life",
        "rating": "A",
        "agency": "S&P",
        "source_url": "https://www.chinalife.com.hk/en/investor-relations/",
        "as_of_date": date(2024, 6, 1),
        "note": "中国人寿海外",
    },
    {
        "company": "BOC Life",
        "rating": "A",
        "agency": "S&P",
        "source_url": "https://www.boclifepension.com/",
        "as_of_date": date(2024, 6, 1),
        "note": "中银人寿，请以官网披露为准",
    },
]


def seed(db: Session) -> int:
    """插入或更新保司评级，返回处理条数"""
    count = 0
    for r in INSURER_RATINGS:
        existing = db.query(InsurerRating).filter(
            InsurerRating.company == r["company"],
            InsurerRating.agency == r["agency"],
        ).first()
        if existing:
            existing.rating = r["rating"]
            existing.source_url = r["source_url"]
            existing.as_of_date = r["as_of_date"]
            existing.note = r.get("note")
            db.merge(existing)
        else:
            rec = InsurerRating(**r)
            db.add(rec)
        count += 1
    db.commit()
    return count


def main():
    # 默认与 backend/.env 一致：使用 himiao-data/db（Docker 挂载 /app/data）
    _default = "sqlite:///" + os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "himiao-data", "db", "himiao.db"
    ).replace("\\", "/")
    db_url = os.getenv("DATABASE_URL", _default)
    connect_args = {"check_same_thread": False, "timeout": 30} if "sqlite" in db_url else {}
    engine = create_engine(db_url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        n = seed(db)
        print(f"[seed_insurer_ratings] 已写入 {n} 条保司评级")
        for r in db.query(InsurerRating).all():
            print(f"  {r.company}: {r.rating} ({r.agency}) ← {r.source_url[:50]}...")


if __name__ == "__main__":
    main()
