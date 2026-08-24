import json
from pathlib import Path
H=Path(__file__).parent
D=json.loads((H/'cases.json').read_text())
assert len(D['cases'])==8
ids=[c['id'] for c in D['cases']]; assert len(ids)==len(set(ids))
for c in D['cases']:
    assert c['expected_mode'] in {'MAP','DISCRIMINATE','VERIFY','TRANSFER','REFRAME'}
    assert len(c['required'])==3 and len(c['forbidden'])>=2
    assert all(len(g)>=1 for g in c['required']+c['forbidden'])
print('cases=8 domains=',sorted({c['domain'] for c in D['cases']}),'validation=PASS')
