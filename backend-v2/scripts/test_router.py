"""Test query router accuracy"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.query_router import classify

# Test cases: (question, expected_intent)
TEST_CASES = [
    # STRUCTURED (SQL)
    ("Bao nhiêu ca CT hôm nay?", "STRUCTURED"),
    ("Tổng số ca chụp", "STRUCTURED"),
    ("Ca nào chưa đọc?", "STRUCTURED"),
    ("Thống kê theo modality", "STRUCTURED"),
    ("Bệnh nhân Trần Văn B chụp gì?", "STRUCTURED"),
    ("Danh sách ca tháng 4", "STRUCTURED"),
    ("Mấy ca pending?", "STRUCTURED"),
    ("Ai viết báo cáo nhiều nhất?", "STRUCTURED"),
    ("Ca reported hôm nay", "STRUCTURED"),
    ("Có bao nhiêu bệnh nhân nữ?", "STRUCTURED"),
    
    # SEMANTIC (RAG)
    ("Tổn thương phổi dạng nốt đơn độc", "SEMANTIC"),
    ("Hình ảnh mờ kính rải rác hai phổi", "SEMANTIC"),
    ("Viêm phổi kèm tràn dịch màng phổi", "SEMANTIC"),
    ("U gan HCC giai đoạn 3", "SEMANTIC"),
    ("Gãy xương đùi", "SEMANTIC"),
    ("Thoát vị đĩa đệm", "SEMANTIC"),
    ("Vôi hóa động mạch chủ", "SEMANTIC"),
    ("Dày tổ chức kẽ hai phổi", "SEMANTIC"),
    ("Tìm báo cáo tương tự nhồi máu não", "SEMANTIC"),
    ("BI-RADS 4 tuyến vú phải", "SEMANTIC"),
]

print("=" * 70)
print("  Query Router Evaluation (6805 pattern)")  
print("=" * 70)

correct = 0
total = len(TEST_CASES)

for question, expected in TEST_CASES:
    intent, conf, debug = classify(question)
    ok = "✅" if intent == expected else "❌"
    if intent == expected:
        correct += 1
    
    scores = debug["scores"]
    print(f"{ok} [{intent:10s} conf={conf:.2f}] "
          f"S={scores.get('STRUCTURED',0):.2f} R={scores.get('SEMANTIC',0):.2f} "
          f"| {question[:45]}")

print(f"\n{'=' * 70}")
print(f"  Accuracy: {correct}/{total} = {correct/total*100:.1f}%")
print(f"{'=' * 70}")
