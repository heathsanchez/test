import json
from pathlib import Path
R=Path(__file__).parent
c=json.loads((R/'cases.json').read_text())
assert c['schema']=='separator.selection.v2' and len(c['cases'])==6
for x in c['cases']:
    assert set(x['options'])==set('ABCD') and x['correct'] in x['options']
print('SEPARATOR_SELECTION_V2_VALIDATION_PASS')