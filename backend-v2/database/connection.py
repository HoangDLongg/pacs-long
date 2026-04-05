import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

class DatabaseConnection:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            cls._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=config.DB_HOST,
                port=config.DB_PORT,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASS
            )
        return cls._pool

    @classmethod
    def get_connection(cls):
        return cls.get_pool().getconn()

    @classmethod
    def close_all(cls):
        if cls._pool:
            cls._pool.closeall()

    @classmethod
    def release_connection(cls, conn):
        """Trả kết nối về pool — PHẢI gọi sau khi dùng xong"""
        if cls._pool and conn:
            cls._pool.putconn(conn)

    @classmethod
    def init_db(cls):
        """Chạy init_db.sql để tạo bảng"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            sql_path = os.path.join(os.path.dirname(__file__), "init_db.sql")
            with open(sql_path, "r", encoding="utf-8") as f:
                sql = f.read()
            cursor.execute(sql)
            conn.commit()
            print("[DB] Tables created successfully")
        except Exception as e:
            conn.rollback()
            print(f"[DB] Error creating tables: {e}")
        finally:
            cursor.close()
            cls.release_connection(conn)
