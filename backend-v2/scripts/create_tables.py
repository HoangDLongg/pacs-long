import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='pacs_db', user='pacs_user', password='pacs_pass'
)
cursor = conn.cursor()

with open('database/init_db.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    cursor.execute(sql)
    conn.commit()
    print('[OK] Tables created/verified successfully')
except Exception as e:
    conn.rollback()
    print(f'[ERROR] {e}')
    raise

# List tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = cursor.fetchall()
print('[DB] Tables in pacs_db:')
for t in tables:
    print(f'  - {t[0]}')

cursor.close()
conn.close()
