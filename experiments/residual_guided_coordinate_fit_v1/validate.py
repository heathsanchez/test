import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R.parent/'law_induction_v1b'/'cases.json').read_text())
assert len(D['cases'])==8
for c in D['cases']:
    assert len(c['observations'])==7
    assert c['query']=='DY'
    assert c['correct'] in 'JKLM'
print('RESIDUAL_GUIDED_COORDINATE_FIT_V1_VALIDATION_PASS')
