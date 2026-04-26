"""
export_reports.py — Xuất 75 báo cáo từ DB ra JSON để benchmark trên Kaggle
Output: scripts/reports_data.json
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONN = "host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass"

conn = psycopg2.connect(DB_CONN)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("""
    SELECT dr.id, dr.findings, dr.conclusion, dr.recommendation,
           s.modality, s.body_part, s.description,
           p.full_name as patient_name
    FROM diagnostic_reports dr
    JOIN studies s ON dr.study_id = s.id
    JOIN patients p ON s.patient_id = p.id
    ORDER BY dr.id
""")
reports = cur.fetchall()

# Convert to serializable
data = []
for r in reports:
    data.append({
        "id": r["id"],
        "findings": r["findings"],
        "conclusion": r["conclusion"],
        "recommendation": r["recommendation"],
        "modality": r["modality"],
        "body_part": r["body_part"],
        "description": r["description"],
        "patient_name": r["patient_name"],
    })

out_path = os.path.join(os.path.dirname(__file__), "reports_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Exported {len(data)} reports -> {out_path}")
cur.close(); conn.close()
