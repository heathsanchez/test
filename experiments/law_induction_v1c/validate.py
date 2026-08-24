import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R.parent/'law_induction_v1b'/'cases.json').read_text())
assert len(D['cases'])==8
assert all(set(c.keys())>={'id','observations','query','oracle','correct'} for c in D['cases'])
assert len({c['id'] for c in D['cases']})==8
print('LAW_INDUCTION_V1C_VALIDATION_PASS')
