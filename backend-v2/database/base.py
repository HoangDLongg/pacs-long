# database/connection.py
import os
import sys
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base

import config

# Thêm path để import config và models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ====================== SQLAlchemy Setup ======================
DATABASE_URL = f"postgresql://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,        # kiểm tra kết nối trước khi dùng
    pool_recycle=3600,         # recycle connection sau 1 giờ
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()      # ← Dùng chung cho tất cả models

# ====================== psycopg2 Pool (nếu vẫn muốn dùng raw) ======================
_psycopg2_pool = None

def get_psycopg2_pool():
    global _psycopg2_pool
    if _psycopg2_pool is None:
        _psycopg2_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
    return _psycopg2_pool


# ====================== Dependency cho FastAPI ======================
def get_db() -> Session:
    """Dependency chính dùng trong toàn bộ API (SQLAlchemy Session)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Dùng khi cần session ngoài dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====================== psycopg2 helpers (giữ lại nếu cần) ======================
def get_connection():
    """Lấy kết nối psycopg2 (raw)"""
    return get_psycopg2_pool().getconn()


def release_connection(conn):
    """Trả kết nối psycopg2 về pool"""
    if conn:
        get_psycopg2_pool().putconn(conn)


# ====================== Init Database ======================
def init_db():
    """Chạy script init_db.sql"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql_path = os.path.join(os.path.dirname(__file__), "init_db.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        cursor.execute(sql)
        conn.commit()
        print("[DB] Tables and indexes created successfully")
    except Exception as e:
        conn.rollback()
        print(f"[DB] Error creating tables: {e}")
    finally:
        cursor.close()
        release_connection(conn)


# Close pool khi shutdown app
def close_all_connections():
    global _psycopg2_pool
    if _psycopg2_pool:
        _psycopg2_pool.closeall()
        print("[DB] All connections closed")