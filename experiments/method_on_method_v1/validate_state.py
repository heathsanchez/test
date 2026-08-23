from pathlib import Path
import sys

REQUIRED = [
    '## G — Real goal', '## V — Verifier', '## A — Apparatus',
    '## F — Current frame', '## R — Sharpest residual', '## H — Live rivals',
    '## Current controller state', '## Candidate-generation boundary',
    '## Q — Next deciding experiment', '## B — Budget vector',
    '## X — Supplied scaffolds', '## E — Evidence ledger update',
    '## Attack', '## Transfer', '## Reconstruction', '## K — Retention decision',
    '## Method residual'
]

def validate(path: str) -> list[str]:
    text = Path(path).read_text(encoding='utf-8')
    missing = [h for h in REQUIRED if h not in text]
    errors = [f'missing section: {h}' for h in missing]
    if 'Lifecycle:' not in text:
        errors.append('missing lifecycle declaration')
    if 'Mode:' not in text:
        errors.append('missing epistemic mode declaration')
    if 'Frozen before protected outcomes?' not in text:
        errors.append('missing freeze declaration')
    return errors

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'templates/UVRM_STATE_TEMPLATE.md'
    errors = validate(path)
    if errors:
        print('UVRM_STATE_INVALID')
        for e in errors: print('-', e)
        raise SystemExit(1)
    print('UVRM_STATE_VALID')

if __name__ == '__main__':
    main()
