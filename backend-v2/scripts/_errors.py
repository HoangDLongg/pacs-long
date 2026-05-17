import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

data = json.load(open(r'e:\HoangDucLong_javisai\pacs_rag_system\dataset\datatest.json','r',encoding='utf-8'))
from core.query_router import classify

errors_pl = []
errors_st = []
for g in data:
    for c in g['cases']:
        intent, conf, debug = classify(c['query'])
        if intent != c['expected']:
            entry = f"[{intent}] '{c['query']}' (group: {g['group']})"
            if c['expected'] == 'PATIENT_LOOKUP':
                errors_pl.append(entry)
            elif c['expected'] == 'STRUCTURED':
                errors_st.append(entry)

print(f"=== PATIENT_LOOKUP errors: {len(errors_pl)} ===")
for e in errors_pl:
    print(f"  {e}")
print(f"\n=== STRUCTURED errors: {len(errors_st)} ===")
for e in errors_st[:30]:
    print(f"  {e}")
