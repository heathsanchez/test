from pathlib import Path
p=Path(__file__).parent
assert (p/'PRECOMMIT.md').exists()
text=(p/'run_openai.py').read_text()
for s in ['SEED=2026082507','FAMILIES=[2,3,5]','TASKS_PER_FAMILY=16','TARGET_INFO_GAIN_OBS_ONLY','OPTIMAL_QUERY']:
    assert s in text,s
print('RIGHT_QUESTION_TRANSFER_V1_VALIDATION_PASS')
