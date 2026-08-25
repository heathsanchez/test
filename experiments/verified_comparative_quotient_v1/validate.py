from pathlib import Path
p=Path(__file__).parent
assert (p/'PRECOMMIT.md').exists()
text=(p/'run_openai.py').read_text()
for s in ['FAMILIES=[2,3,5]','TASKS_PER_FAMILY=16','max_verified_proposals','VERIFIED_COMPARATIVE']:
    assert s in text, s
print('VERIFIED_COMPARATIVE_QUOTIENT_V1_VALIDATION_PASS')
