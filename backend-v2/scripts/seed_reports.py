"""
seed_reports.py — Tải text báo cáo y tế từ ViX-Ray (HuggingFace)
và seed vào bảng diagnostic_reports cho RAG search.

Chỉ tải TEXT (findings + impressions), KHÔNG tải ảnh 17GB.

Usage:
  pip install datasets
  python scripts/seed_reports.py
"""

import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONN = "host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass"


def get_studies_without_reports(conn):
    """Lấy danh sách studies chưa có báo cáo"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT s.id, s.modality, s.body_part, s.description
        FROM studies s
        LEFT JOIN diagnostic_reports dr ON dr.study_id = s.id
        WHERE dr.id IS NULL
        ORDER BY s.id
    """)
    studies = cur.fetchall()
    cur.close()
    return studies


def get_doctor_ids(conn):
    """Lấy danh sách doctor để gán báo cáo"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM users WHERE role IN ('doctor', 'admin')")
    doctors = [r["id"] for r in cur.fetchall()]
    cur.close()
    return doctors if doctors else [1]  # fallback admin=1


def download_vixray_texts(max_reports=200):
    """Tải text findings/impressions từ ViX-Ray (streaming, không tải ảnh)"""
    try:
        from datasets import load_dataset
    except ImportError:
        print("[ERROR] Cần cài: pip install datasets")
        print("  Chạy: .\\venv\\Scripts\\pip.exe install datasets")
        sys.exit(1)

    print("[1/3] Đang tải ViX-Ray dataset (chỉ text, streaming)...")
    
    ds = load_dataset(
        "MilitaryHospital175/VNMedical_bv175",
        split="train",
        streaming=True,  # ← KHÔNG tải toàn bộ 17GB
    )

    reports = []
    for i, row in enumerate(ds):
        if i >= max_reports:
            break

        findings = row.get("findings") or row.get("Findings") or ""
        impressions = row.get("impressions") or row.get("Impressions") or row.get("impression") or ""

        # Bỏ qua rows trống
        if not findings.strip() and not impressions.strip():
            continue

        reports.append({
            "findings": findings.strip(),
            "conclusion": impressions.strip(),
        })

        if (i + 1) % 50 == 0:
            print(f"  ... đã tải {i + 1} rows, {len(reports)} có text")

    print(f"[1/3] Hoàn tất: {len(reports)} báo cáo có text")
    return reports


def seed_reports(conn, reports, studies, doctor_ids):
    """Insert reports vào DB, gán cho studies chưa có báo cáo"""
    cur = conn.cursor()
    inserted = 0

    # Shuffle reports để random
    random.shuffle(reports)

    for i, study in enumerate(studies):
        if i >= len(reports):
            break

        report = reports[i]
        doctor_id = random.choice(doctor_ids)

        # Thêm recommendation dựa trên nội dung
        recommendation = "Theo dõi định kỳ, chụp lại sau 3-6 tháng nếu cần."
        if "u" in report["conclusion"].lower() or "khối" in report["conclusion"].lower():
            recommendation = "Đề nghị chụp CT có tiêm thuốc cản quang để đánh giá thêm."
        elif "viêm" in report["conclusion"].lower():
            recommendation = "Đề nghị điều trị nội khoa và tái khám sau 2 tuần."

        try:
            cur.execute("""
                INSERT INTO diagnostic_reports (study_id, doctor_id, findings, conclusion, recommendation)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (study_id) DO NOTHING
            """, (
                study["id"],
                doctor_id,
                report["findings"],
                report["conclusion"],
                recommendation,
            ))

            # Update study status → REPORTED
            cur.execute(
                "UPDATE studies SET status = 'REPORTED' WHERE id = %s AND status = 'PENDING'",
                (study["id"],)
            )
            inserted += 1

        except Exception as e:
            print(f"  [WARN] Study {study['id']}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    return inserted


def main():
    print("=" * 60)
    print("  PACS++ — Seed Diagnostic Reports từ ViX-Ray")
    print("=" * 60)

    # 1. Check DB
    conn = psycopg2.connect(DB_CONN)
    studies = get_studies_without_reports(conn)
    doctor_ids = get_doctor_ids(conn)

    print(f"\n[DB] Studies chưa có báo cáo: {len(studies)}")
    print(f"[DB] Doctor IDs available: {doctor_ids}")

    if not studies:
        print("[OK] Tất cả studies đã có báo cáo. Không cần seed thêm.")
        conn.close()
        return

    # 2. Tải text từ ViX-Ray
    max_reports = min(len(studies) + 20, 200)  # tải dư 20 phòng trống
    reports = download_vixray_texts(max_reports=max_reports)

    if not reports:
        print("[ERROR] Không tải được báo cáo từ ViX-Ray")
        conn.close()
        return

    # 3. Seed vào DB
    print(f"\n[2/3] Đang seed {min(len(reports), len(studies))} báo cáo vào DB...")
    inserted = seed_reports(conn, reports, studies, doctor_ids)

    # 4. Verify
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM diagnostic_reports")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as with_embed FROM diagnostic_reports WHERE embedding IS NOT NULL")
    with_embed = cur.fetchone()["with_embed"]
    cur.close()

    print(f"\n[3/3] Kết quả:")
    print(f"  Đã insert: {inserted} báo cáo")
    print(f"  Tổng reports trong DB: {total}")
    print(f"  Có embedding: {with_embed}")
    print(f"  Chưa embedding: {total - with_embed} (cần chạy embed_existing.py)")

    conn.close()
    print("\n[DONE] Seed hoàn tất!")


if __name__ == "__main__":
    main()
