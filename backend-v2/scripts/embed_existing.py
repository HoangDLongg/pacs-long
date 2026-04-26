"""
scripts/embed_existing.py — Batch embed 75 báo cáo hiện có
Spec UC18: tạo embedding cho reports chưa có vector

Chạy 1 lần duy nhất. Sau này report mới sẽ auto-embed qua api/report.py

Usage: python scripts/embed_existing.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from core.embeddings import EmbeddingModel

DB_CONN = "host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass"


def main():
    print("=" * 60)
    print("  Batch Embed: e5-large -> diagnostic_reports.embedding")
    print("=" * 60)

    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Lay reports chua co embedding
    cur.execute("""
        SELECT id, findings, conclusion
        FROM diagnostic_reports
        WHERE embedding IS NULL
        ORDER BY id
    """)
    reports = cur.fetchall()
    print(f"\nReports chua embed: {len(reports)}")

    if not reports:
        print("[OK] Tat ca reports da co embedding.")
        cur.close(); conn.close()
        return

    # 2. Encode tung report
    success = 0
    for i, r in enumerate(reports):
        text = EmbeddingModel.make_report_text(r["findings"], r["conclusion"])
        if not text:
            print(f"  #{r['id']}: SKIP (empty text)")
            continue

        try:
            vector = EmbeddingModel.encode(text)
            if vector:
                cur.execute(
                    "UPDATE diagnostic_reports SET embedding = %s::vector WHERE id = %s",
                    (str(vector), r["id"])
                )
                success += 1
                if (i + 1) % 10 == 0:
                    conn.commit()
                    print(f"  ... {i+1}/{len(reports)} done")
        except Exception as e:
            print(f"  #{r['id']}: ERROR {e}")

    conn.commit()

    # 3. Verify
    cur.execute("SELECT COUNT(*) as total FROM diagnostic_reports WHERE embedding IS NOT NULL")
    total_embed = cur.fetchone()["total"]

    print(f"\nKet qua:")
    print(f"  Embed thanh cong: {success}")
    print(f"  Tong co embedding: {total_embed}")

    cur.close(); conn.close()
    print("\n[DONE]")


if __name__ == "__main__":
    main()
