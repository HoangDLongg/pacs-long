"""
database/base.py — SQLAlchemy declarative Base.

Trước đây file này duplicate toàn bộ engine + pool từ connection.py,
gây nguy cơ hai SQLAlchemy engine cùng tồn tại. Đã thu gọn chỉ còn Base.

Tất cả engine, SessionLocal, get_db, psycopg2 pool nằm trong
`database/connection.py` — single source of truth.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
