from pathlib import Path
R=Path(__file__).parent
assert (R/'PRECOMMIT.md').exists()
assert (R/'run_openai.py').exists()
assert (R/'score.py').exists()
print('RIGHT_QUESTION_CAPSTONE_V1_VALIDATION_PASS')
