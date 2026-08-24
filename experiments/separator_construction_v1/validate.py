import json,itertools
from pathlib import Path
R=Path(__file__).parent
obj=json.loads((R/'cases.json').read_text())
assert obj['schema']=='separator.construction.v1'
assert len(obj['cases'])==6
for c in obj['cases']:
    assert set(c['allowed'])=={'probe','control','metric'}
    found=False
    for p,ctrl,m in itertools.product(c['allowed']['probe'],c['allowed']['control'],c['allowed']['metric']):
        e=f'{p}|{ctrl}|{m}'
        if c['target'].get(e,c['default'])!=c['rival'].get(e,c['default']): found=True
    assert found, c['id']
print('SEPARATOR_CONSTRUCTION_V1_VALIDATION_PASS')
