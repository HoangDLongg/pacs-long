"""Check data integrity: orthanc_id in DB vs actual instances on Orthanc"""
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

ORTHANC = "http://localhost:8042"
DB_CONN = "host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass"

conn = psycopg2.connect(DB_CONN)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("""
    SELECT s.id, s.orthanc_id, s.study_uid, s.modality, s.num_instances AS db_instances,
           p.full_name AS patient_name
    FROM studies s JOIN patients p ON s.patient_id = p.id
    WHERE s.orthanc_id IS NOT NULL AND s.orthanc_id != ''
    ORDER BY s.id
""")
studies = cur.fetchall()

print(f"{'ID':>6} | {'Patient':<16} | {'Mod':<4} | {'DB#':>4} | {'Orth#':>5} | {'Status':<12} | orthanc_id")
print("-" * 100)

ok = 0
empty = 0
missing = 0
mismatch_mod = 0

null_modality_fixes = []

for s in studies:
    oid = s["orthanc_id"]
    try:
        # Check study exists on Orthanc
        r = requests.get(f"{ORTHANC}/studies/{oid}", timeout=5)
        if r.status_code == 404:
            # Try find by UID
            fr = requests.post(f"{ORTHANC}/tools/find", json={
                "Level": "Study", "Query": {"StudyInstanceUID": s["study_uid"]}, "Limit": 1
            }, timeout=5)
            found = fr.json()
            if found:
                real_oid = found[0]
                r2 = requests.get(f"{ORTHANC}/studies/{real_oid}", timeout=5)
                orth_data = r2.json()
                inst_count = len(orth_data.get("Instances", []))
                status = "FIXED_OID" if inst_count > 0 else "EMPTY"
            else:
                inst_count = 0
                status = "NOT_FOUND"
                missing += 1
        else:
            orth_data = r.json()
            inst_count = len(orth_data.get("Instances", []))
            
            if inst_count == 0:
                status = "EMPTY"
                empty += 1
            else:
                status = "OK"
                ok += 1
                
            # Check modality mismatch
            orth_mod = orth_data.get("MainDicomTags", {}).get("StudyDescription", "")
            if s["modality"] is None and inst_count > 0:
                # Can fix modality from Orthanc series
                try:
                    series_r = requests.get(f"{ORTHANC}/studies/{oid}/series", timeout=5)
                    series = series_r.json()
                    if series:
                        s1 = requests.get(f"{ORTHANC}/series/{series[0]['ID']}", timeout=5).json()
                        real_mod = s1.get("MainDicomTags", {}).get("Modality", "")
                        if real_mod:
                            null_modality_fixes.append((s["id"], real_mod))
                            mismatch_mod += 1
                except:
                    pass

    except Exception as e:
        inst_count = -1
        status = f"ERROR: {e}"

    mod = s["modality"] or "NULL"
    print(f"{s['id']:>6} | {s['patient_name']:<16} | {mod:<4} | {s['db_instances']:>4} | {inst_count:>5} | {status:<12} | {oid[:20]}...")

print()
print(f"=== Summary ===")
print(f"Total studies: {len(studies)}")
print(f"OK (has instances): {ok}")
print(f"EMPTY (0 instances): {empty}")  
print(f"NOT_FOUND on Orthanc: {missing}")
print(f"Modality NULL fixable: {mismatch_mod}")

if null_modality_fixes:
    print(f"\nModality NULL can be fixed:")
    for sid, mod in null_modality_fixes:
        print(f"  UPDATE studies SET modality = '{mod}' WHERE id = {sid};")

cur.close()
conn.close()
