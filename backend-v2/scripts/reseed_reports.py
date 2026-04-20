"""
reseed_reports.py — Xoá reports cũ (random) và seed lại ĐÚNG theo modality/description
- CR/DX chest → ViX-Ray reports (X-quang ngực)
- CT chest   → ViX-Ray reports (phù hợp)
- CT abdomen → báo cáo CT bụng tự viết
- CT spine   → báo cáo CT cột sống tự viết
- MG breast  → báo cáo mammography tự viết
- MR         → báo cáo MR tự viết

Usage: python scripts/reseed_reports.py
"""

import sys, os, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONN = "host=localhost port=5432 dbname=pacs_db user=pacs_user password=pacs_pass"

# ====================== BÁO CÁO MẪU THEO MODALITY ======================

MG_REPORTS = [
    {
        "findings": "- Tuyến vú hai bên mật độ không đồng nhất type C (theo BI-RADS).\n- Không thấy hình ảnh nốt đặc hay calci hóa nghi ngờ.\n- Các cấu trúc mạch máu và mô mỡ bình thường.\n- Hạch nách hai bên không to.",
        "conclusion": "- Tuyến vú hai bên không ghi nhận bất thường.\n- BI-RADS 1: Bình thường.",
        "recommendation": "Tầm soát định kỳ mammography sau 12 tháng."
    },
    {
        "findings": "- Tuyến vú phải: nốt đặc bờ rõ, kích thước khoảng 12x10mm vùng 1/4 trên ngoài, mật độ trung bình.\n- Tuyến vú trái: không ghi nhận bất thường.\n- Không thấy vi vôi hóa nghi ngờ.\n- Hạch nách phải kích thước bình thường.",
        "conclusion": "- Nốt đặc vú phải vùng 1/4 trên ngoài.\n- BI-RADS 3: Có thể lành tính, cần theo dõi.",
        "recommendation": "Đề nghị siêu âm vú để đánh giá thêm. Tái khám mammography sau 6 tháng."
    },
    {
        "findings": "- Tuyến vú hai bên mật độ type D (rất đặc).\n- Vú trái: đám vi vôi hóa dạng đa hình vùng 1/4 trên trong, phân bố nhóm, kéo dài khoảng 15mm.\n- Vú phải: không ghi nhận tổn thương.\n- Hạch nách hai bên không to bất thường.",
        "conclusion": "- Vi vôi hóa nghi ngờ ác tính vùng 1/4 trên trong vú trái.\n- BI-RADS 4B: Nghi ngờ ác tính.",
        "recommendation": "Đề nghị sinh thiết lõi (core biopsy) dưới hướng dẫn stereotaxy."
    },
    {
        "findings": "- Tuyến vú hai bên mật độ type B.\n- Vú phải: nang đơn thuần kích thước 8mm vùng 1/4 dưới trong.\n- Vú trái: nang đơn thuần kích thước 5mm.\n- Không ghi nhận calci hóa nghi ngờ hay tổn thương khối đặc.\n- Da và núm vú hai bên bình thường.",
        "conclusion": "- Nang đơn thuần vú hai bên.\n- BI-RADS 2: Lành tính.",
        "recommendation": "Theo dõi mammography định kỳ hàng năm."
    },
    {
        "findings": "- Tuyến vú trái: khối đặc bờ không đều, kích thước 25x18mm vùng 1/4 trên ngoài, co kéo tổ chức xung quanh.\n- Dày da vùng trên ngoài vú trái.\n- Hạch nách trái to, hình tròn, mất cấu trúc rốn mỡ, kích thước 18mm.\n- Vú phải: không ghi nhận bất thường.",
        "conclusion": "- Khối đặc vú trái nghi ngờ ác tính kèm hạch nách trái nghi di căn.\n- BI-RADS 5: Rất nghi ngờ ác tính.",
        "recommendation": "Đề nghị sinh thiết lõi u vú trái và chọc hút hạch nách trái. Chuyển khoa Ung bướu."
    },
    {
        "findings": "- Tuyến vú hai bên mật độ không đồng nhất type C.\n- Vú phải: hai nốt đặc bờ rõ, đều, kích thước 7mm và 5mm vùng sau núm vú.\n- Vú trái: bình thường.\n- Calci hóa lành tính dạng vỏ trứng rải rác.\n- Hạch nách hai bên bình thường.",
        "conclusion": "- Nốt đặc vú phải, hướng lành tính (fibroadenoma?).\n- BI-RADS 3: Có thể lành tính.",
        "recommendation": "Siêu âm vú bổ sung. Theo dõi mammography sau 6 tháng."
    },
]

CT_ABD_REPORTS = [
    {
        "findings": "- Gan kích thước bình thường, nhu mô đồng nhất, không ghi nhận nốt hay khối bất thường.\n- Túi mật căng, thành mỏng, không sỏi.\n- Lách kích thước bình thường.\n- Tụy hình thái bình thường.\n- Hai thận kích thước bình thường, không sỏi, không giãn đài bể thận.\n- Không dịch tự do ổ bụng.",
        "conclusion": "- Không ghi nhận bất thường cơ quan trong ổ bụng.",
        "recommendation": "Theo dõi định kỳ."
    },
    {
        "findings": "- Gan to, nhu mô không đồng nhất, nốt giảm tỉ trọng thùy phải kích thước 35x30mm, bắt thuốc mạnh thì động mạch, thải thuốc thì tĩnh mạch cửa.\n- Tĩnh mạch cửa 14mm, lách to 15cm.\n- Không dịch ổ bụng.\n- Các cơ quan khác bình thường.",
        "conclusion": "- Nốt gan phải nghi HCC (ung thư biểu mô tế bào gan) trên nền xơ gan.\n- Lách to, tăng áp tĩnh mạch cửa.",
        "recommendation": "Đề nghị MRI gan với chất tương phản đặc hiệu gan (Primovist) để đánh giá thêm. Xét nghiệm AFP."
    },
    {
        "findings": "- Gan kích thước bình thường.\n- Sỏi túi mật đường kính khoảng 12mm, thành túi mật dày nhẹ.\n- Ống mật chủ 5mm không giãn.\n- Tụy, lách, hai thận bình thường.\n- Không dịch ổ bụng.",
        "conclusion": "- Sỏi túi mật kèm viêm túi mật mạn.",
        "recommendation": "Đề nghị khám ngoại tiêu hóa, cân nhắc phẫu thuật cắt túi mật nội soi."
    },
    {
        "findings": "- Thận phải: sỏi bể thận kích thước 18mm, giãn đài bể thận và niệu quản đoạn trên phải.\n- Thận trái: bình thường.\n- Bàng quang dịch tốt, thành mỏng.\n- Gan, lách, tụy bình thường.\n- Không dịch ổ bụng.",
        "conclusion": "- Sỏi bể thận phải kèm ứ nước thận phải độ II.",
        "recommendation": "Đề nghị khám tiết niệu. Cân nhắc tán sỏi ngoài cơ thể hoặc phẫu thuật."
    },
]

CT_SPINE_REPORTS = [
    {
        "findings": "- Giảm chiều cao thân đốt sống L1, gãy lún khoảng 40%.\n- Thoái hóa đĩa đệm L4-L5, L5-S1, giảm tín hiệu đĩa đệm.\n- Phồng đĩa đệm L4-L5 chèn ép nhẹ bao cùng.\n- Hẹp ống sống L4-L5.\n- Các cấu trúc khác bình thường.",
        "conclusion": "- Gãy lún đốt sống L1.\n- Thoái hóa đĩa đệm đa tầng L4-S1 kèm phồng đĩa đệm L4-L5.",
        "recommendation": "Đề nghị MRI cột sống thắt lưng để đánh giá thêm. Khám chuyên khoa cột sống."
    },
    {
        "findings": "- Thoát vị đĩa đệm trung tâm-cạnh bên trái L5-S1, kích thước khoảng 8mm, chèn ép rễ S1 trái.\n- Hẹp lỗ liên hợp L5-S1 bên trái.\n- Các tầng đĩa đệm khác bình thường.\n- Không ghi nhận tổn thương xương.",
        "conclusion": "- Thoát vị đĩa đệm L5-S1 trái chèn ép rễ S1 trái.",
        "recommendation": "Đề nghị điều trị bảo tồn. Tái khám nếu triệu chứng không cải thiện sau 6 tuần."
    },
    {
        "findings": "- Cong vẹo cột sống ngực-thắt lưng, lồi bên phải.\n- Gai xương thân đốt sống đa tầng.\n- Vôi hóa dây chằng dọc trước.\n- Hẹp khoang đĩa đệm L3-L4, L4-L5.\n- Không ghi nhận thoát vị đĩa đệm rõ.",
        "conclusion": "- Thoái hóa cột sống đa tầng.\n- Cong vẹo cột sống.",
        "recommendation": "Vật lý trị liệu. Theo dõi định kỳ."
    },
]

MR_REPORTS = [
    {
        "findings": "- Hai thận kích thước bình thường, bờ đều.\n- Nang đơn thuần cực dưới thận trái kích thước 22mm.\n- Không ghi nhận khối u đặc hay sỏi.\n- Tuyến thượng thận hai bên bình thường.\n- Hệ thống đài bể thận không giãn.",
        "conclusion": "- Nang đơn thuần thận trái (Bosniak I).",
        "recommendation": "Theo dõi siêu âm sau 12 tháng."
    },
]


def classify_study(study):
    """Phân loại study theo body region để match report phù hợp"""
    mod = (study["modality"] or "").upper()
    body = (study["body_part"] or "").upper()
    desc = (study["description"] or "").upper()

    # MG = mammography
    if mod == "MG" or "MAMMO" in desc or "DBT" in desc or "BREAST" in body:
        return "MG"

    # MR
    if mod == "MR":
        return "MR"

    # CT/CR/DX abdomen
    if "ABD" in desc or "PELVIS" in desc or "ABDOMEN" in body or "ABD" in body:
        return "CT_ABD"

    # CT spine
    if "SPINE" in desc or "SPINE" in body or "BONE" in desc:
        return "CT_SPINE"

    # CT/CR/DX chest (most common — default for CR, DX)
    if mod in ("CR", "DX") or "CHEST" in desc or "THORAX" in desc or "LUNG" in desc or "PORT" in body:
        return "CHEST"

    # PET/CT → chest (close enough)
    if "PET" in desc:
        return "CHEST"

    # Default → chest
    return "CHEST"


def download_vixray_chest_reports(max_reports=100):
    """Tải reports chest X-ray từ ViX-Ray"""
    try:
        from datasets import load_dataset
    except ImportError:
        print("[ERROR] pip install datasets")
        sys.exit(1)

    print("[1/4] Tai ViX-Ray (chi text, streaming)...")
    ds = load_dataset("MilitaryHospital175/VNMedical_bv175", split="train", streaming=True)

    reports = []
    for i, row in enumerate(ds):
        if len(reports) >= max_reports:
            break
        findings = row.get("findings") or row.get("Findings") or ""
        impressions = row.get("impressions") or row.get("Impressions") or row.get("impression") or ""
        if findings.strip() and impressions.strip():
            reports.append({"findings": findings.strip(), "conclusion": impressions.strip()})
        if (i + 1) % 50 == 0:
            print(f"  ... scanned {i+1} rows, got {len(reports)}")

    print(f"[1/4] Got {len(reports)} chest reports from ViX-Ray")
    return reports


def main():
    print("=" * 60)
    print("  RESEED: Match reports theo modality/description")
    print("=" * 60)

    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Xoa reports cu (random)
    cur.execute("DELETE FROM diagnostic_reports")
    cur.execute("UPDATE studies SET status = 'PENDING'")
    conn.commit()
    print("\n[0/4] Da xoa reports cu")

    # 2. Lay studies
    cur.execute("""
        SELECT s.id, s.modality, s.body_part, s.description
        FROM studies s ORDER BY s.id
    """)
    studies = cur.fetchall()

    # 3. Phan loai
    groups = {}
    for s in studies:
        cat = classify_study(s)
        groups.setdefault(cat, []).append(s)

    print("\n[2/4] Phan loai studies:")
    for cat, lst in groups.items():
        print(f"  {cat:10}: {len(lst)} studies")

    # 4. Tai ViX-Ray cho chest
    chest_count = len(groups.get("CHEST", []))
    vixray = download_vixray_chest_reports(max_reports=max(chest_count + 10, 50))

    # 5. Lay doctor IDs
    cur.execute("SELECT id FROM users WHERE role IN ('doctor', 'admin')")
    doctor_ids = [r["id"] for r in cur.fetchall()] or [1]

    # 6. Seed theo tung nhom
    inserted = 0
    random.shuffle(vixray)

    for cat, cat_studies in groups.items():
        if cat == "CHEST":
            pool = vixray
        elif cat == "MG":
            pool = MG_REPORTS
        elif cat == "CT_ABD":
            pool = CT_ABD_REPORTS
        elif cat == "CT_SPINE":
            pool = CT_SPINE_REPORTS
        elif cat == "MR":
            pool = MR_REPORTS
        else:
            pool = vixray

        for i, study in enumerate(cat_studies):
            report = pool[i % len(pool)]
            doctor_id = random.choice(doctor_ids)

            rec = report.get("recommendation", "Theo doi dinh ky, chup lai sau 3-6 thang neu can.")

            try:
                cur.execute("""
                    INSERT INTO diagnostic_reports (study_id, doctor_id, findings, conclusion, recommendation)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (study_id) DO NOTHING
                """, (study["id"], doctor_id, report["findings"], report["conclusion"], rec))

                cur.execute("UPDATE studies SET status = 'REPORTED' WHERE id = %s", (study["id"],))
                inserted += 1
            except Exception as e:
                print(f"  [WARN] Study {study['id']}: {e}")
                conn.rollback()

    conn.commit()

    # 7. Verify
    cur.execute("SELECT COUNT(*) as total FROM diagnostic_reports")
    total = cur.fetchone()["total"]

    print(f"\n[4/4] Ket qua:")
    print(f"  Da insert: {inserted} bao cao")
    print(f"  Tong reports: {total}")
    print(f"  - CHEST (ViX-Ray): {len(groups.get('CHEST', []))}")
    print(f"  - MG (mammography): {len(groups.get('MG', []))}")
    print(f"  - CT_ABD: {len(groups.get('CT_ABD', []))}")
    print(f"  - CT_SPINE: {len(groups.get('CT_SPINE', []))}")
    print(f"  - MR: {len(groups.get('MR', []))}")

    cur.close()
    conn.close()
    print("\n[DONE] Reseed hoan tat!")


if __name__ == "__main__":
    main()
