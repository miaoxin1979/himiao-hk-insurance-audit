#!/usr/bin/env python3
"""
导出产品 special_features（标签）用于前端 TAGS_I18N
运行: python scripts/export_product_tags.py
输出: 所有不重复的标签，便于补充翻译
"""
import json
import os
import sys

# 添加项目根路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.db.base import SessionLocal
    from app.models.product_sub import SavingsProduct, WholelifeProduct, CiProduct
    from app.models.product import Product
    from sqlalchemy.orm import joinedload

    db = SessionLocal()
    tags = set()

    for model in [SavingsProduct, WholelifeProduct, CiProduct]:
        rows = db.query(model).filter(model.special_features_json.isnot(None)).all()
        for r in rows:
            fs = r.special_features_json or []
            if isinstance(fs, list):
                for t in fs:
                    if isinstance(t, str) and t.strip():
                        tags.add(t.strip())

    db.close()
    for t in sorted(tags):
        print(t)
except Exception as e:
    # 回退：从 JSON 文件读取
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base, "../himiao-web/data/products.json")
    if os.path.exists(data_path):
        with open(data_path) as f:
            d = json.load(f)
        tags = set()
        for p in d.get("products", []):
            for t in p.get("tags", []) + p.get("features", []):
                if t:
                    tags.add(t)
        for t in sorted(tags):
            print(t)
    else:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
