from pathlib import Path
import json, subprocess

BASE = Path('coldcert/project').resolve()
OUT = Path('cold_division_residual_v1').resolve()
OUT.mkdir(exist_ok=True)

cp = subprocess.run(['lake','build','Galoistools.Proof.Division'], cwd=BASE, text=True, capture_output=True)
raw = cp.stdout + '\n' + cp.stderr
errs = []
for line in raw.splitlines():
    if 'error:' in line or 'error: Galoistools/Proof/Division.lean' in line:
        errs.append(line)
res = {'exit': cp.returncode, 'errors': errs, 'tail': raw[-50000:]}
(OUT/'result.json').write_text(json.dumps(res, indent=2))
print('COLD_DIVISION_RESIDUAL_V1', json.dumps({'exit': cp.returncode, 'error_lines': len(errs)}))
print(raw[-50000:])
raise SystemExit(cp.returncode)
