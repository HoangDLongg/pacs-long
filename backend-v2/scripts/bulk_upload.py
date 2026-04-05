"""Upload tất cả file DICOM lên Orthanc + lưu metadata vào DB"""
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from core.dicom_parser import DicomParser
from core.orthanc_client import OrthancClient
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

DICOM_DIR = r"E:\HoangDucLong_javisai\pacs_rag_system\dataset\dicom"


def upload_all(max_files=0):
    DatabaseConnection.init_db()
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    count = 0
    errors = 0
    patients_created = set()
    start = time.time()

    for root, dirs, files in os.walk(DICOM_DIR):
        for filename in files:
            if not filename.endswith(".dcm"):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                # 1. Parse metadata
                metadata = DicomParser.parse(file_bytes)
                if not metadata["patient_id"] or not metadata["study_uid"]:
                    errors += 1
                    continue

                # 2. Upsert patient
                cursor.execute("""
                    INSERT INTO patients (patient_id, full_name, gender)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (patient_id) DO NOTHING
                    RETURNING id
                """, (
                    metadata["patient_id"],
                    metadata["patient_name"] or metadata["patient_id"],
                    metadata["patient_sex"] if metadata["patient_sex"] in ("M", "F") else None
                ))
                result = cursor.fetchone()
                if result:
                    patient_db_id = result["id"]
                else:
                    cursor.execute("SELECT id FROM patients WHERE patient_id = %s",
                                   (metadata["patient_id"],))
                    patient_db_id = cursor.fetchone()["id"]

                # 3. Upload to Orthanc
                orthanc_result = OrthancClient.upload_dicom(file_bytes)
                orthanc_study_id = orthanc_result.get("ParentStudy", "")

                # 4. Upsert study
                cursor.execute("""
                    INSERT INTO studies (study_uid, patient_id, study_date, modality, body_part,
                                       description, orthanc_id, num_instances)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    ON CONFLICT (study_uid) DO UPDATE SET
                        orthanc_id = EXCLUDED.orthanc_id,
                        num_instances = studies.num_instances + 1
                """, (
                    metadata["study_uid"],
                    patient_db_id,
                    metadata["study_date"],
                    metadata["modality"] if metadata["modality"] in ("CR","CT","MR","US","DX","MG","SEG") else None,
                    metadata["body_part"],
                    metadata["study_description"],
                    orthanc_study_id
                ))

                # 5. Auto-create patient account
                pid = metadata["patient_id"]
                if pid not in patients_created:
                    cursor.execute("SELECT id FROM users WHERE username = %s", (pid,))
                    if not cursor.fetchone():
                        pw_hash = AuthUtils.hash_password(pid + "@")
                        cursor.execute("""
                            INSERT INTO users (username, password_hash, full_name, role, linked_patient_id)
                            VALUES (%s, %s, %s, 'patient', %s)
                            ON CONFLICT (username) DO NOTHING
                        """, (pid, pw_hash, metadata["patient_name"] or pid, patient_db_id))
                    patients_created.add(pid)

                count += 1
                if count % 200 == 0:
                    conn.commit()
                    elapsed = time.time() - start
                    rate = count / elapsed
                    print(f"  [{count}] {rate:.0f} files/s | {filename}")

                if max_files > 0 and count >= max_files:
                    break

            except Exception as e:
                conn.rollback()
                errors += 1
                if errors <= 10:
                    print(f"  ERROR: {filename}: {e}")

        if max_files > 0 and count >= max_files:
            break

    conn.commit()
    elapsed = time.time() - start

    cursor.close()
    DatabaseConnection.release_connection(conn)

    print(f"\n{'='*50}")
    print(f"  DONE!")
    print(f"  Files uploaded: {count}")
    print(f"  Errors: {errors}")
    print(f"  Patients created: {len(patients_created)}")
    print(f"  Time: {elapsed:.1f}s ({count/elapsed:.0f} files/s)")
    print(f"{'='*50}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=0, help="Max files (0=all)")
    args = parser.parse_args()

    print(f"[UPLOAD] Starting... (max={args.max or 'ALL'})")
    upload_all(args.max)
