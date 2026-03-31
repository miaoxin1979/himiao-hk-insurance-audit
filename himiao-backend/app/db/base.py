"""
app/db/base.py
所有 ORM Model 继承此 Base
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# 在这里 import 所有 model，确保 Base.metadata 能看到全部表
# 供 alembic 或 Base.metadata.create_all() 使用
from app.models import user, product, product_sub, article, subscriber, broker, ad_slot, insurer_rating  # noqa
