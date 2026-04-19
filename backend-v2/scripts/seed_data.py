"""
scripts/seed_data.py
Tạo dữ liệu test đầy đủ cho 4 roles
Bao gồm: users, patients, studies mẫu
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import get_connection, release_connection
from psycopg2.extras import RealDictCursor


def seed_all():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        print("[SEED] Tao users...")

        # ============ 1. Staff users ============
        staff = [
            ("admin",      "admin123",   "Quan tri vien",       "admin",       None),
            ("dr.nam",     "doctor123",  "BS. Nguyen Van Nam",  "doctor",      None),
            ("dr.lan",     "doctor123",  "BS. Tran Thi Lan",    "doctor",      None),
            ("tech.hung",  "tech123",    "KTV. Le Van Hung",    "technician",  None),
            ("tech.mai",   "tech123",    "KTV. Pham Thi Mai",   "technician",  None),
        ]

        for username, password, full_name, role, linked in staff:
            ph = AuthUtils.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, linked_patient_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, ph, full_name, role, linked))
            print(f"  [{role}] {username} / {password}")

        # ============ 2. Patient records ============
        print("\n[SEED] Tao patients...")

        patients = [
            ("P001001", "Nguyen Thi Hoa",  "1985-03-12", "F", "0901111111"),
            ("P001002", "Tran Van Minh",   "1970-07-24", "M", "0902222222"),
            ("P001003", "Le Thi Bich",     "1990-11-05", "F", "0903333333"),
        ]

        patient_ids = {}
        for pid, name, bdate, gender, phone in patients:
            cursor.execute("""
                INSERT INTO patients (patient_id, full_name, birth_date, gender, phone)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (patient_id) DO UPDATE SET full_name = EXCLUDED.full_name
                RETURNING id
            """, (pid, name, bdate, gender, phone))
            db_id = cursor.fetchone()["id"]
            patient_ids[pid] = db_id
            print(f"  {pid} / {name}")

        # ============ 3. Patient user accounts ============
        print("\n[SEED] Tao patient accounts...")

        patient_accounts = [
            ("P001001", "Nguyen Thi Hoa"),
            ("P001002", "Tran Van Minh"),
        ]

        for pid, name in patient_accounts:
            ph = AuthUtils.hash_password(f"{pid}@")
            linked = patient_ids.get(pid)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, linked_patient_id)
                VALUES (%s, %s, %s, 'patient', %s)
                ON CONFLICT (username) DO NOTHING
            """, (pid, ph, name, linked))
            print(f"  [patient] {pid} / {pid}@")

        # ============ 4. Mẫu studies ============
        print("\n[SEED] Tao studies mau...")

        # Lấy technician id
        cursor.execute("SELECT id FROM users WHERE username = 'tech.hung'")
        tech_row = cursor.fetchone()
        tech_id = tech_row["id"] if tech_row else None

        studies_data = [
            # (study_uid, patient_pid, date, modality, body_part, description, status)
            ("1.2.3.4.001", "P001001", "2026-04-01", "CT", "Chest", "CT Nguc thang",       "PENDING"),
            ("1.2.3.4.002", "P001001", "2026-03-20", "MR", "Brain", "MRI Nao khong thuoc", "REPORTED"),
            ("1.2.3.4.003", "P001002", "2026-04-05", "CT", "Abdomen","CT Bung co thuoc",   "PENDING"),
            ("1.2.3.4.004", "P001002", "2026-02-14", "CR", "Chest", "X-Quang Nguc thang",  "VERIFIED"),
            ("1.2.3.4.005", "P001003", "2026-04-07", "US", "Abdomen","Sieu am Bung tong quat","PENDING"),
        ]

        for study_uid, pid, date, modality, body_part, desc, status in studies_data:
            pt_id = patient_ids.get(pid)
            if not pt_id:
                continue
            cursor.execute("""
                INSERT INTO studies (study_uid, patient_id, study_date, modality,
                                     body_part, description, status, technician_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (study_uid) DO NOTHING
            """, (study_uid, pt_id, date, modality, body_part, desc, status, tech_id))
            print(f"  [{status}] {study_uid} - {pid} - {modality}")

        conn.commit()
        print("\n[SEED] Hoan thanh!")
        print("\n=== Tai khoan test ===")
        print("admin       / admin123")
        print("dr.nam      / doctor123")
        print("tech.hung   / tech123")
        print("P001001     / P001001@     (patient - 2 ca chup)")
        print("P001002     / P001002@     (patient - 2 ca chup)")

    except Exception as e:
        conn.rollback()
        print(f"\n[SEED] ERROR: {e}")
        raise
    finally:
        cursor.close()
        release_connection(conn)


if __name__ == "__main__":
    seed_all()
