import json
data = json.load(open(r'e:\HoangDucLong_javisai\pacs_rag_system\dataset\datatest.json','r',encoding='utf-8'))
count = 0
for g in data:
    if 'entity (BN' in g['group']:
        g['group'] = g['group'].replace('STRUCTURED', 'PATIENT_LOOKUP')
        for c in g['cases']:
            c['expected'] = 'PATIENT_LOOKUP'
            count += 1
json.dump(data, open(r'e:\HoangDucLong_javisai\pacs_rag_system\dataset\datatest.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'Updated {count} cases to PATIENT_LOOKUP')
