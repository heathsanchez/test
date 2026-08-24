import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R/'cases.json').read_text())
assert D['schema']=='law.induction.v1'
assert len(D['cases'])==8
for c in D['cases']:
    assert len(c['observations'])==7
    assert c['query'] not in ' '.join(c['observations'])
    assert c['correct'] in 'JKLM'
    assert 'Encode' in c['oracle']
print('LAW_INDUCTION_V1_VALIDATION_PASS')
