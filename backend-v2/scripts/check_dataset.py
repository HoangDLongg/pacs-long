import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = json.load(open(r'e:\HoangDucLong_javisai\pacs_rag_system\dataset\datatest.json', 'r', encoding='utf-8'))

total = sum(len(g['cases']) for g in data)
print(f"Total cases: {total}\n")

# Per-group
print("Per group:")
for g in data:
    print(f"  [{len(g['cases']):>3}] {g['group']}")

# Per-intent
intents = {}
for g in data:
    for c in g['cases']:
        intents[c['expected']] = intents.get(c['expected'], 0) + 1
print(f"\nPer intent:")
for k, v in sorted(intents.items()):
    print(f"  {k}: {v} ({v/total*100:.1f}%)")

# Duplicates
seen = {}
for g in data:
    for c in g['cases']:
        q = c['query'].strip().lower()
        if q not in seen:
            seen[q] = []
        seen[q].append(g['group'])
dups = {q: gs for q, gs in seen.items() if len(gs) > 1}
print(f"\nDuplicate queries: {len(dups)}")
for q, gs in list(dups.items()):
    print(f"  '{q}' -> appears in: {gs}")

# Potential label issues
print(f"\nPotential issues:")
issues_count = 0
for g in data:
    for c in g['cases']:
        q = c['query'].lower()
        exp = c['expected']
        issues = []

        # Medical term labeled STRUCTURED (without counting/listing keywords)
        medical = ['viêm', 'u ', 'tổn thương', 'gãy', 'tràn dịch', 'xuất huyết', 'nhồi máu', 'sỏi', 'ung thư', 'di căn']
        counting = ['bao nhiêu', 'mấy', 'đếm', 'danh sách', 'liệt kê', 'thống kê', 'ca nào', 'chụp gì', 'tổng', 'số lượng', 'tk', 'ds', 'sl']
        if exp == "STRUCTURED" and any(m in q for m in medical) and not any(k in q for k in counting):
            issues.append("medical terms but STRUCTURED (no counting keyword)")

        # Name pattern labeled as non-PATIENT_LOOKUP
        vn_surnames = ['nguyễn', 'trần', 'lê', 'phạm', 'hoàng', 'huỳnh', 'phan', 'vũ', 'võ', 'đặng', 'bùi', 'đỗ', 'hồ', 'ngô', 'dương', 'lý', 'cao', 'mai', 'lương', 'tô', 'đinh', 'nguyen', 'tran', 'le', 'pham', 'hoang', 'huynh', 'phan', 'vu', 'vo', 'dang', 'bui', 'do', 'ho', 'ngo', 'duong', 'ly', 'cao', 'mai', 'luong', 'to', 'dinh']

        if exp == "PATIENT_LOOKUP" and "EDGE" in g['group']:
            issues.append("edge case labeled PATIENT_LOOKUP")

        if issues:
            issues_count += 1
            print(f"  [{exp}] '{c['query']}' -> {', '.join(issues)}")

if issues_count == 0:
    print("  None found!")

# Length distribution
lengths = []
for g in data:
    for c in g['cases']:
        lengths.append(len(c['query'].split()))
short = sum(1 for l in lengths if l <= 2)
medium = sum(1 for l in lengths if 3 <= l <= 6)
long_q = sum(1 for l in lengths if l > 6)
print(f"\nLength distribution:")
print(f"  Short (1-2 words):  {short} ({short/total*100:.1f}%)")
print(f"  Medium (3-6 words): {medium} ({medium/total*100:.1f}%)")
print(f"  Long (7+ words):    {long_q} ({long_q/total*100:.1f}%)")

print(f"\n{'='*50}")
print(f"SUMMARY: {total} cases, {len(dups)} duplicates, {len(data)} groups")
