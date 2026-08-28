from pathlib import Path
import subprocess, json, re
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_mul_direct_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

# Extract the previously certified helper blocks from repository scripts.
def extract_probe(path: str) -> str:
    src = Path(path).read_text()
    m = re.search(r"probe = r'''(.*)'''\n\np = out", src, re.S)
    if not m:
        raise RuntimeError(f'could not extract probe from {path}')
    return m.group(1)

unit_lift = extract_probe('../.github/scripts/vero_msi_gfmul_unit_lift_v1.py')
unit_zero = extract_probe('../.github/scripts/vero_msi_unit_zero_bridge_v1.py')
scalar = extract_probe('../.github/scripts/vero_monic_scalar_probe_v4.py')

# Compile helpers as separate Lean modules, then import them into the direct theorem probe.
(out/'MSIUnitLift.lean').write_text(unit_lift)
(out/'MSIUnitZero.lean').write_text(unit_zero)
(out/'MonicScalar.lean').write_text(scalar)
for mod in ['MSIUnitLift.lean','MSIUnitZero.lean','MonicScalar.lean']:
    cp = subprocess.run(['lake','lean',mod],cwd=out,text=True,capture_output=True)
    if cp.returncode:
        print(f'HELPER_FAIL {mod}', cp.returncode)
        print((cp.stdout+cp.stderr)[-20000:])
        raise SystemExit(cp.returncode)

probe = r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring
import MSIUnitLift
import MSIUnitZero
import MonicScalar

open Galoistools

namespace GaloistoolsMonicMulDirectV1

-- First direct composition attempt against the actual benchmark slot.
theorem direct : spec_monic_mul_associate canonical := by
  simp only [spec_monic_mul_associate, canonical]
  intro f g p hp hnf hng hf hg
  have hprod := reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
  cases f with
  | nil => contradiction
  | cons a as =>
      cases g with
      | nil => contradiction
      | cons b bs =>
          simp only [Galoistools.gfMonic]
          by_cases ha1 : a = 1
          · subst a
            simp
          · by_cases hb1 : b = 1
            · subst b
              simp
            · simp [ha1, hb1]

end GaloistoolsMonicMulDirectV1
'''

p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MONIC_MUL_DIRECT_V1_EXIT',cp.returncode)
print(raw[-36000:])
Path('monic_mul_direct_v1').mkdir(exist_ok=True)
Path('monic_mul_direct_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-42000:]},indent=2))
