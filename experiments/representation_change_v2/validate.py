import json
from pathlib import Path

ROOT=Path(__file__).parent
data=json.loads((ROOT/'cases.json').read_text())
assert data['schema']=='representation.change.v2'
cases=data['cases']
assert len(cases)==6
ids=[c['id'] for c in cases]
assert len(ids)==len(set(ids))
for c in cases:
    assert c['correct'] in 'ABCD'
    assert set(c['options'])==set('ABCD')
    for k in ['raw_outcome','prose_memory','structured_state','ablated_state','later_problem']:
        assert isinstance(c[k],str) and c[k].strip()
print('REPRESENTATION_CHANGE_V2_VALIDATION_PASS')
