import json
from pathlib import Path
p=Path(__file__).with_name('precommit.json')
x=json.loads(p.read_text())
assert x['schema']=='verified.decision.certificate.v1.precommit'
assert x['frozen']['families']==[2,3,5]
assert x['frozen']['tasks_per_family']==16
assert x['frozen']['max_verified_proposals']==4
assert 'VERIFIED_CERTIFICATE' in x['arms']
print('VERIFIED_DECISION_CERTIFICATE_V1_VALIDATION_PASS')
