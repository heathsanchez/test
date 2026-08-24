from pathlib import Path
import re
p=Path(__file__).parent
for f in ['PRECOMMIT.md','run_openai.py','score.py']:
    assert (p/f).exists(),f
text=(p/'PRECOMMIT.md').read_text()
assert 'VERIFIED_SYNTHESIS' in text and 'ONE_SHOT_SYNTHESIS' in text
run=(p/'run_openai.py').read_text()
assert 'SEED=2026082509' in run
assert 'TASKS_PER_FAMILY=12' in run
assert 'rounds<4' in run
print('VERIFIED_QUOTIENT_SYNTHESIS_V1_VALIDATION_PASS')
