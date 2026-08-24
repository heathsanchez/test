import json
from pathlib import Path
p=Path(__file__).parent
obj=json.loads((p/'cases.json').read_text())
assert obj['schema']=='separator.selection.v1'
assert len(obj['cases'])==6
for c in obj['cases']:
    for k in ['id','domain','evidence','latent','rival','experiment_required','separation_required','discipline_required']:
        assert c.get(k), (c.get('id'),k)
print('SEPARATOR_SELECTION_V1_VALIDATION_PASS')
