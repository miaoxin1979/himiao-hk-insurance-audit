#!/usr/bin/env python3
"""补充盈御3、环宇盈活等产品的分红实现率（dividend_fulfillment_5y）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# 数据来源：AIA 官网/香港保险资讯网，盈御3 总现金价值比率100%，环宇盈活参考同系列
UPDATES = [
    ("aia-global-wealth-3", 100.0),   # 盈御多元货币计划3，2024总现价比率100%
    ("aia-globalife-active", 100.0),  # 环宇盈活储蓄保险计划，参考盈御系列
]

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # 默认 NAS 数据库路径
        default = "sqlite:///" + os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "himiao-data", "db", "himiao.db"
        ).replace("\\", "/")
        db_url = default
    engine = create_engine(db_url, connect_args={"check_same_thread": False, "timeout": 15})
    with Session(engine) as db:
        for slug, val in UPDATES:
            r = db.execute(text("UPDATE products SET dividend_fulfillment_5y = :v WHERE slug = :s"), {"v": val, "s": slug})
            if r.rowcount:
                print(f"  OK {slug} -> {val}%")
            else:
                print(f"  SKIP {slug} (not found)")
        db.commit()
    print("完成")

if __name__ == "__main__":
    main()
