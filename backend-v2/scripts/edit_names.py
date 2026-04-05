import requests

edits = [
    {"patient_id": "10250",       "new_name": "Mai Thi Dung"},
    {"patient_id": "10352",       "new_name": "Luong Thi Yen"},
    {"patient_id": "10355",       "new_name": "Cao Van Phuc"},
    {"patient_id": "11084",       "new_name": "Ho Van Tai"},
    {"patient_id": "1215936303",  "new_name": "Huynh Thi Tam"},
    {"patient_id": "1535333000",  "new_name": "Phan Van Long"},
    {"patient_id": "1778001589",  "new_name": "Vu Thi Ha"},
    {"patient_id": "1781655154",  "new_name": "To Van Binh"},
    {"patient_id": "A000801",     "new_name": "Nguyen Van Tuan"},
    {"patient_id": "A000936",     "new_name": "Tran Thi Mai"},
    {"patient_id": "A002279",     "new_name": "Le Hoang Minh"},
    {"patient_id": "A002304",     "new_name": "Pham Thi Lan"},
    {"patient_id": "AP-6H6G",    "new_name": "Ngo Van Thanh"},
    {"patient_id": "AP-6M60",    "new_name": "Duong Thi Lien"},
    {"patient_id": "AP-95DK",    "new_name": "Trinh Van Khoa"},
    {"patient_id": "AP-97PG",    "new_name": "Ly Thi Phuong"},
    {"patient_id": "AP-9GTR",    "new_name": "Dinh Van Son"},
    {"patient_id": "C3L-00189",  "new_name": "Vo Van Duc"},
    {"patient_id": "C3L-00263",  "new_name": "Hoang Thi Nga"},
    {"patient_id": "C3L-00275",  "new_name": "Dang Van Hai"},
    {"patient_id": "C3L-00609",  "new_name": "Bui Thi Huong"},
]

print(f"Editing {len(edits)} patients...")
r = requests.post("http://localhost:8000/api/editor/edit-bulk", json={"edits": edits})
print(f"Status: {r.status_code}")
data = r.json()
print(f"Total files edited: {data['total_files']}")
for pid, cnt in data["per_patient"].items():
    print(f"  {pid}: {cnt} files")
