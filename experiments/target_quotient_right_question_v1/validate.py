from pathlib import Path
import ast
p=Path(__file__).with_name('run_openai.py')
ast.parse(p.read_text())
pre=Path(__file__).with_name('PRECOMMIT.md')
assert pre.exists() and 'TARGET_QUOTIENT' in pre.read_text()
print('TARGET_QUOTIENT_RIGHT_QUESTION_V1_VALIDATION_PASS')
