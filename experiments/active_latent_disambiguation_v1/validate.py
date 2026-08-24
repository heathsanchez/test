import json
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R.parent/'law_induction_v1b'/'cases.json').read_text())
assert len(D['cases'])==8
P=(R/'PRECOMMIT.md').read_text()
assert 'INFO_GAIN_QUERY > RANDOM_QUERY' in P
print('ACTIVE_LATENT_DISAMBIGUATION_V1_VALIDATION_PASS')
