import json
from pathlib import Path

ROOT=Path(__file__).parent
D=json.loads((ROOT/'cases.json').read_text())
assert D['schema']=='representation.change.v1'
assert len(D['cases'])==6
ids=set()
for c in D['cases']:
    assert c['id'] not in ids; ids.add(c['id'])
    assert set(c['options'])==set('ABCD')
    assert c['correct'] in c['options']
    for k in ['separator_outcome','prose_memory','structured_state','ablated_state','later_problem']:
        assert isinstance(c[k],str) and c[k].strip()
    assert c['structured_state'] != c['ablated_state']
print('REPRESENTATION_CHANGE_V1_VALIDATION_PASS')
