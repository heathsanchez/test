import json
from pathlib import Path
HERE=Path(__file__).parent
v5=json.loads((HERE.parent/'uvrm_graph_v5'/'cases.json').read_text())
assert len(v5['cases'])==8
assert len({c['id'] for c in v5['cases']})==8
assert all(len(c['required'])==3 and len(c['forbidden'])>=2 and c['relations'] for c in v5['cases'])
from render import WRONG
assert WRONG=={'SUPPORTS':'REFUTES','REFUTES':'SUPPORTS','MOTIVATES':'WEAKENS','WEAKENS':'MOTIVATES','BLOCKS':'SUPPORTS'}
print('cases=8 reused_v5_rubric=TRUE wrong_label_map=FROZEN validation=PASS')
