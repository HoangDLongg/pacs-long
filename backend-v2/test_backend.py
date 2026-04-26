"""
PACS++ Backend Feature Test Script
Chạy 16 test cases kiểm tra toàn bộ chức năng backend
"""
import requests
import json

BASE = 'http://localhost:8000'
results = []

def test(name, fn):
    try:
        ok, detail = fn()
        results.append((name, 'PASS' if ok else 'FAIL', detail))
    except Exception as e:
        results.append((name, 'ERROR', str(e)[:120]))

# ========== 1. Health Check ==========
def t_health():
    r = requests.get(f'{BASE}/health')
    d = r.json()
    return r.status_code == 200 and d.get('status') == 'ok', f'{r.status_code} {d}'
test('1. Health Check', t_health)

# ========== 2. Login valid ==========
def t_login_ok():
    r = requests.post(f'{BASE}/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    d = r.json()
    has_token = 'access_token' in d
    return r.status_code == 200 and has_token, f'{r.status_code} has_token={has_token}'
test('2. Login (admin)', t_login_ok)

# ========== 3. Login wrong ==========
def t_login_fail():
    r = requests.post(f'{BASE}/api/auth/login', data={'username': 'admin', 'password': 'wrong'})
    return r.status_code == 401, f'{r.status_code}'
test('3. Login wrong password', t_login_fail)

# Get tokens
r = requests.post(f'{BASE}/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
ADMIN_TOKEN = r.json().get('access_token', '')
admin_h = {'Authorization': f'Bearer {ADMIN_TOKEN}'}

r = requests.post(f'{BASE}/api/auth/login', data={'username': 'dr.nam', 'password': 'doctor123'})
resp_doc = r.json()
DOC_TOKEN = resp_doc.get('access_token', '')
doc_h = {'Authorization': f'Bearer {DOC_TOKEN}'}

r = requests.post(f'{BASE}/api/auth/login', data={'username': 'tech.hung', 'password': 'tech123'})
TECH_TOKEN = r.json().get('access_token', '')
tech_h = {'Authorization': f'Bearer {TECH_TOKEN}'}

# ========== 4. Login doctor ==========
def t_doc():
    return resp_doc.get('role') == 'doctor', f"role={resp_doc.get('role')}"
test('4. Login (dr.nam) role=doctor', t_doc)

# ========== 5. Login technician ==========
def t_tech():
    r = requests.post(f'{BASE}/api/auth/login', data={'username': 'tech.hung', 'password': 'tech123'})
    d = r.json()
    return d.get('role') == 'technician', f"role={d.get('role')}"
test('5. Login (tech.hung) role=tech', t_tech)

# ========== 6. Worklist ==========
def t_worklist():
    r = requests.get(f'{BASE}/api/worklist', headers=admin_h)
    d = r.json()
    studies = d.get('studies', [])
    return r.status_code == 200 and len(studies) > 0, f'{r.status_code} count={len(studies)}'
test('6. Worklist GET', t_worklist)

# ========== 7. Worklist Stats ==========
def t_stats():
    r = requests.get(f'{BASE}/api/worklist/stats/dashboard', headers=admin_h)
    d = r.json()
    return r.status_code == 200 and 'total' in d, f"total={d.get('total')} pending={d.get('pending')}"
test('7. Worklist Stats', t_stats)

# ========== 8. Worklist Filter ==========
def t_filter():
    r = requests.get(f'{BASE}/api/worklist?modality=CT', headers=admin_h)
    d = r.json()
    studies = d.get('studies', [])
    all_ct = all(s.get('modality') == 'CT' for s in studies) if studies else True
    return r.status_code == 200 and all_ct, f'ct_count={len(studies)}'
test('8. Worklist Filter (CT)', t_filter)

# ========== 9. No Auth ==========
def t_no_auth():
    r = requests.get(f'{BASE}/api/worklist')
    return r.status_code in (401, 403), f'{r.status_code}'
test('9. No auth -> 401', t_no_auth)

# ========== 10. Admin Users ==========
def t_admin_users():
    r = requests.get(f'{BASE}/api/admin/users', headers=admin_h)
    d = r.json()
    users = d.get('users', [])
    return r.status_code == 200 and len(users) > 0, f'count={len(users)}'
test('10. Admin Users', t_admin_users)

# ========== 11. Admin System ==========
def t_admin_system():
    r = requests.get(f'{BASE}/api/admin/system', headers=admin_h)
    d = r.json()
    return r.status_code == 200 and 'users' in d, f"users={d.get('users')} patients={d.get('patients')} studies={d.get('studies')}"
test('11. Admin System Stats', t_admin_system)

# ========== 12. RBAC: Doctor no admin ==========
def t_rbac():
    r = requests.get(f'{BASE}/api/admin/users', headers=doc_h)
    return r.status_code in (401, 403), f'{r.status_code}'
test('12. RBAC: Doctor no Admin', t_rbac)

# ========== 13. Report GET ==========
def t_report():
    r = requests.get(f'{BASE}/api/report/1', headers=admin_h)
    return r.status_code == 200, f'{r.status_code}'
test('13. Report GET study=1', t_report)

# ========== 14. Keyword Search ==========
def t_keyword():
    r = requests.get(f'{BASE}/api/search/keyword?q=phoi&limit=5', headers=admin_h)
    d = r.json()
    return r.status_code == 200, f"total={d.get('total', 0)}"
test('14. Keyword Search', t_keyword)

# ========== 15. Refresh Token ==========
def t_refresh():
    r = requests.post(f'{BASE}/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    d = r.json()
    rt = d.get('refresh_token')
    if not rt:
        return False, 'No refresh_token in response'
    r2 = requests.post(f'{BASE}/api/auth/refresh', json={'refresh_token': rt})
    d2 = r2.json()
    has_new = 'access_token' in d2
    return r2.status_code == 200 and has_new, f'{r2.status_code} new_token={has_new}'
test('15. Refresh Token', t_refresh)

# ========== 16. Logout ==========
def t_logout():
    r = requests.post(f'{BASE}/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    tok = r.json().get('access_token', '')
    r2 = requests.post(f'{BASE}/api/auth/logout', headers={'Authorization': f'Bearer {tok}'})
    return r2.status_code == 200, f'{r2.status_code}'
test('16. Logout', t_logout)

# ========== PRINT RESULTS ==========
print()
print('=' * 65)
print(f'  PACS++ Backend Test Results')
print('=' * 65)
passed = 0
for name, status, detail in results:
    icon = 'OK' if status == 'PASS' else 'XX' if status == 'FAIL' else '!!'
    print(f'  [{icon}] {status:5s} | {name:35s} | {detail}')
    if status == 'PASS':
        passed += 1
print('=' * 65)
print(f'  Result: {passed}/{len(results)} passed')
if passed == len(results):
    print('  ALL TESTS PASSED!')
else:
    print(f'  {len(results) - passed} test(s) failed')
print('=' * 65)
