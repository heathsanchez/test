import json
from pathlib import Path
R=Path(__file__).parent
d=json.loads((R/'cases.json').read_text())
assert d['schema']=='developmental.transfer.v1'
assert len(d['cases'])==8
ids=set()
for c in d['cases']:
    assert c['id'] not in ids; ids.add(c['id'])
    assert set(c['options'])==set('JKLM')
    assert c['correct'] in c['options']
    assert all(k in c for k in ['raw','prose','structured','wrong','query'])
    assert c['structured'] != c['wrong']
print('DEVELOPMENTAL_TRANSFER_V1_VALIDATION_PASS')