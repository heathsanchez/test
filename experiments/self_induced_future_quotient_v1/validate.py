from pathlib import Path

root=Path(__file__).parent
assert (root/'PRECOMMIT.md').exists()
assert (root/'run_openai.py').exists()
assert (root/'score.py').exists()
text=(root/'PRECOMMIT.md').read_text()
for s in ['SELF_INDUCED','RAW_DIRECT','HAND_QUOTIENT','SHAM_MARGINAL','Primary']:
    assert s in text
print('SELF_INDUCED_FUTURE_QUOTIENT_V1_VALIDATION_PASS')
