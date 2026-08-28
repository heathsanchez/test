from pathlib import Path
import json, subprocess

BASE = Path('baseline28/galoistools_allin28').resolve()
OUT = Path('strict_baseline28_gate_v1').resolve()
OUT.mkdir(exist_ok=True)

def run(args):
    cp = subprocess.run(args,cwd=BASE,text=True,capture_output=True)
    raw = cp.stdout+'\n'+cp.stderr
    return {'exit':cp.returncode,'tail':raw[-30000:]}

# Explicit Lake targets force compilation of the Proof modules while preserving
# the package/module search path. Plain `lake build` does not include them.
ring = run(['lake','build','Galoistools.Proof.Ring'])
div = run(['lake','build','Galoistools.Proof.Division'])
full = run(['lake','build'])
res={'ring':ring,'division':div,'full':full}
(OUT/'result.json').write_text(json.dumps(res,indent=2))
print('STRICT_BASELINE28_GATE_V2', json.dumps({'ring_exit':ring['exit'],'division_exit':div['exit'],'full_exit':full['exit']}))
if ring['exit']:
    print('RING_RESIDUAL\n'+ring['tail'])
if div['exit']:
    print('DIVISION_RESIDUAL\n'+div['tail'])
raise SystemExit(0 if ring['exit']==0 and div['exit']==0 and full['exit']==0 else 1)
