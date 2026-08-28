from pathlib import Path
import subprocess, json, re
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_mul_associate_direct_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

def strip_imports(s: str) -> str:
    return '\n'.join(line for line in s.splitlines() if not line.startswith('import '))

# Certified structural stack: convolution -> gfStrip -> gfMul with local zero preservation.
src = Path('../.github/scripts/vero_msi_gfmul_unit_lift_v1.py').read_text()
m = re.search(r"base = m.group\(1\).*?extra = r'''(.*)'''\n\nprobe = base \+ extra", src, re.S)
if not m:
    raise RuntimeError('could not extract unit-lift extra')
# Re-extract the underlying certified gfMul block directly.
src0 = Path('../.github/scripts/vero_msi_gfmul_scale_both_v1.py').read_text()
m0 = re.search(r"probe = r'''(.*)'''\n\np = out", src0, re.S)
if not m0:
    raise RuntimeError('could not extract gfMul base')
base = m0.group(1).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')
extra = strip_imports(m.group(1)).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

# Certified canonical-residue + unit-zero block.
su = Path('../.github/scripts/vero_msi_unit_zero_bridge_v1.py').read_text()
mu = re.search(r"probe = r'''(.*)'''\n\np = out", su, re.S)
if not mu:
    raise RuntimeError('could not extract unit-zero block')
unit = strip_imports(mu.group(1))
unit = unit.replace('namespace GaloistoolsMSIUnitZeroBridgeV2', 'namespace GaloistoolsMSIGfMulScaleBothV1')
unit = unit.replace('end GaloistoolsMSIUnitZeroBridgeV2', '')

# Certified scalar inverse-product block.
ss = Path('../.github/scripts/vero_monic_scalar_probe_v4.py').read_text()
ms = re.search(r"probe = r'''(.*)'''\n\np = out", ss, re.S)
if not ms:
    raise RuntimeError('could not extract scalar block')
scalar = strip_imports(ms.group(1))

final = r'''

namespace GaloistoolsMSIGfMulScaleBothV1

-- First direct contact with the actual benchmark slot.  All lower transport
-- lemmas above are already certified; this theorem is intentionally kept close
-- to the spec so Lean exposes only the remaining monic-specific residual.
theorem prove_monic_mul_associate_msi_v1 : spec_monic_mul_associate canonical := by
  simp only [spec_monic_mul_associate, canonical]
  intro f g p hp hnf hng hf hg
  cases f with
  | nil => exact (hf rfl).elim
  | cons a as =>
    cases g with
    | nil => exact (hg rfl).elim
    | cons b bs =>
      simp only [Galoistools.gfMonic]
      simp [Galoistools.gfMul]

end GaloistoolsMSIGfMulScaleBothV1
'''

probe = base + extra + unit + '\nend GaloistoolsMSIGfMulScaleBothV1\n\n' + scalar + final
p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MONIC_MUL_ASSOCIATE_DIRECT_V2_EXIT',cp.returncode)
print(raw[-32000:])
Path('monic_mul_associate_direct_v1').mkdir(exist_ok=True)
Path('monic_mul_associate_direct_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-42000:]},indent=2))
