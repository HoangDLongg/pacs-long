"""Test SQL validation — copy trực tiếp hàm _validate_sql để test độc lập."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Copy từ nl2sql_engine.py (tránh import chain)
_BLOCKED_TABLES = {'users', 'refresh_tokens', 'pg_catalog', 'information_schema'}
_BLOCKED_COLUMNS = {'password_hash', 'token_hash', 'embedding', 'is_active'}

def _validate_sql(sql):
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith('SELECT'):
        return False
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'TRUNCATE', 'CREATE', 'EXEC', 'GRANT', 'REVOKE']
    for kw in dangerous:
        if re.search(rf'\b{kw}\b', sql_upper):
            return False
    sql_lower = sql.lower()
    for table in _BLOCKED_TABLES:
        if re.search(rf'\b{table}\b', sql_lower):
            return False
    for col in _BLOCKED_COLUMNS:
        if re.search(rf'\b{col}\b', sql_lower):
            return False
    if 'information_schema' in sql_lower or 'pg_' in sql_lower:
        return False
    return True

# === Test cases ===
dangerous_sqls = [
    ("DELETE FROM patients", "DELETE"),
    ("DROP TABLE patients", "DROP"),
    ("INSERT INTO patients VALUES (1, 'hack')", "INSERT"),
    ("UPDATE patients SET full_name='hacked'", "UPDATE"),
    ("ALTER TABLE patients ADD COLUMN hack TEXT", "ALTER"),
    ("TRUNCATE patients", "TRUNCATE"),
    ("SELECT * FROM users", "access users table"),
    ("SELECT password_hash FROM patients", "access password"),
    ("SELECT * FROM patients; DROP TABLE patients;", "SQL injection"),
    ("SELECT * FROM information_schema.tables", "schema leak"),
    ("SELECT * FROM pg_catalog.pg_tables", "pg_catalog leak"),
]

safe_sqls = [
    "SELECT COUNT(*) FROM studies WHERE modality='CT'",
    "SELECT p.full_name, s.modality FROM studies s JOIN patients p ON s.patient_id=p.id",
    "SELECT * FROM patients WHERE full_name ILIKE '%Nguyen%'",
    "SELECT COUNT(*) FROM studies WHERE study_date = CURRENT_DATE",
]

print("=== DANGEROUS SQL (phải bị BLOCK) ===")
blocked = 0
for sql, desc in dangerous_sqls:
    result = _validate_sql(sql)
    status = "✅ BLOCKED" if not result else "❌ LEAKED!"
    if not result: blocked += 1
    print(f"  {status} | {desc}: {sql[:60]}")

print(f"\n  Blocked: {blocked}/{len(dangerous_sqls)}")

print("\n=== SAFE SQL (phải PASS) ===")
passed = 0
for sql in safe_sqls:
    result = _validate_sql(sql)
    status = "✅ PASSED" if result else "❌ FALSE POSITIVE"
    if result: passed += 1
    print(f"  {status} | {sql[:70]}")

print(f"\n  Passed: {passed}/{len(safe_sqls)}")

print(f"\n{'='*50}")
if blocked == len(dangerous_sqls) and passed == len(safe_sqls):
    print("ALL TESTS PASSED — SQL validation an toàn!")
else:
    print("CÓ LỖI — Cần fix!")
