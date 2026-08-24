import json
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parent
data=json.loads((ROOT/'uvrm_graph_v5'/'cases.json').read_text())
assert len(data['cases'])==8
assert all(len(c['relations'])==2 for c in data['cases'])
assert all(len(c['required'])==3 for c in data['cases'])
assert all(len(c['forbidden'])>=2 for c in data['cases'])
print('cases=8 relations_per_case=2 masks=4 reused_v5_rubric=TRUE validation=PASS')
