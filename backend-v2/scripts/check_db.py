import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='pacs_db', user='pacs_user', password='pacs_pass'
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=== USERS ===")
cursor.execute("SELECT id, username, role, linked_patient_id, is_active FROM users ORDER BY id")
for r in cursor.fetchall():
    linked = f" -> patient_id={r['linked_patient_id']}" if r['linked_patient_id'] else ""
    print(f"  [{r['role']:12}] id={r['id']} {r['username']}{linked}")

print("\n=== PATIENTS ===")
cursor.execute("SELECT id, patient_id, full_name, gender FROM patients ORDER BY id")
for r in cursor.fetchall():
    print(f"  id={r['id']} {r['patient_id']} / {r['full_name']} ({r['gender']})")

print("\n=== STUDIES ===")
cursor.execute("""
    SELECT s.id, s.study_uid, s.status, s.modality, s.study_date, p.patient_id
    FROM studies s JOIN patients p ON s.patient_id = p.id
    ORDER BY s.id
""")
for r in cursor.fetchall():
    print(f"  id={r['id']} [{r['status']:8}] {r['modality']} {r['study_date']} - BN:{r['patient_id']}")

print("\n=== DIAGNOSTIC_REPORTS ===")
cursor.execute("SELECT id, study_id, doctor_id FROM diagnostic_reports ORDER BY id")
rows = cursor.fetchall()
print(f"  {len(rows)} reports")
for r in rows:
    print(f"  id={r['id']} study_id={r['study_id']}")

print("\n=== REFRESH_TOKENS ===")
cursor.execute("SELECT COUNT(*) AS cnt FROM refresh_tokens")
print(f"  {cursor.fetchone()['cnt']} tokens stored")

cursor.close()
conn.close()
