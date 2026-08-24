import json
from pathlib import Path

ROOT = Path(__file__).parent
obj = json.loads((ROOT/'cases.json').read_text())
assert obj['schema'] == 'residual.oocr.v1'
assert len(obj['cases']) == 6
ids = [c['id'] for c in obj['cases']]
assert len(ids) == len(set(ids))
assert set(obj['shuffle_map']) == set(ids)
assert set(obj['shuffle_map'].values()) == set(ids)
for c in obj['cases']:
    assert len(c['evidence']) >= 4
    assert len(c['abstraction_required']) == 3
    assert len(c['experiment_required']) == 2
    assert c['id'] != obj['shuffle_map'][c['id']]
print('RESIDUAL_OOCR_V1_VALIDATION_PASS')
