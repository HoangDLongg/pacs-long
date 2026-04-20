import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass")
cur = conn.cursor(cursor_factory=RealDictCursor)

# Study distribution
cur.execute("""
    SELECT modality, body_part, description, COUNT(*) as cnt
    FROM studies
    WHERE modality IS NOT NULL
    GROUP BY modality, body_part, description
    ORDER BY cnt DESC
""")
print("=== Studies by Modality / BodyPart / Description ===")
for r in cur.fetchall():
    print(f"  {r['modality']:4} | {str(r['body_part'] or '-'):15} | {str(r['description'] or '-')[:50]:50} | x{r['cnt']}")

# NULL modality
cur.execute("SELECT COUNT(*) as cnt FROM studies WHERE modality IS NULL")
null_mod = cur.fetchone()["cnt"]
print(f"\n  NULL modality: {null_mod}")

# Sample studies with descriptions
cur.execute("""
    SELECT s.id, s.modality, s.body_part, s.description, p.full_name
    FROM studies s JOIN patients p ON s.patient_id = p.id
    ORDER BY s.id LIMIT 10
""")
print("\n=== Sample Studies ===")
for r in cur.fetchall():
    print(f"  #{r['id']:4} | {str(r['modality'] or 'NULL'):4} | {str(r['body_part'] or '-'):15} | {str(r['description'] or '-')[:40]} | {r['full_name']}")

cur.close()
conn.close()
