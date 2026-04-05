import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor


def seed_staff():
    """Tạo 5 tài khoản staff để test"""
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    users = [
        ("admin",     "admin123",  "Quản trị viên",       "admin"),
        ("dr.nam",    "doctor123", "BS. Nguyễn Văn Nam",  "doctor"),
        ("dr.lan",    "doctor123", "BS. Trần Thị Lan",    "doctor"),
        ("tech.hung", "tech123",   "KTV. Lê Văn Hùng",   "technician"),
        ("tech.mai",  "tech123",   "KTV. Phạm Thị Mai",  "technician"),
    ]

    try:
        for username, password, full_name, role in users:
            password_hash = AuthUtils.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, password_hash, full_name, role))
            print(f"  {username} / {password} ({role})")

        conn.commit()
        print("\n[SEED] Done!")
    except Exception as e:
        conn.rollback()
        print(f"[SEED] Error: {e}")
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


if __name__ == "__main__":
    print("[SEED] Creating staff users...\n")
    DatabaseConnection.init_db()
    seed_staff()
