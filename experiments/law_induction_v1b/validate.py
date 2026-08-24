import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R/'cases.json').read_text())
assert D['schema']=='law.induction.v1b'
assert len(D['cases'])==8
ids=[c['id'] for c in D['cases']]
assert len(set(ids))==8
for c in D['cases']:
    assert len(c['observations'])==7
    assert c['query'] not in [o.split('->')[0] for o in c['observations']]
    assert c['correct'] in 'JKLM'
    assert c['oracle']
print('LAW_INDUCTION_V1B_VALIDATION_PASS')
