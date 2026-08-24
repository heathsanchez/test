import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R.parent/'law_induction_v1b'/'cases.json').read_text())
assert len(D['cases'])==8
assert all(len(c['observations'])==7 for c in D['cases'])
assert all(c['query']=='DY' for c in D['cases'])
assert (R/'PRECOMMIT.md').exists()
print('LATENT_COORDINATE_INDUCTION_V1_VALIDATION_PASS')
