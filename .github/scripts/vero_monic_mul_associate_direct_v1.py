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

src = Path('../.github/scripts/vero_msi_gfmul_unit_lift_v1.py').read_text()
m = re.search(r"base = m.group\(1\).*?extra = r'''(.*)'''\n\nprobe = base \+ extra", src, re.S)
if not m:
    raise RuntimeError('could not extract unit-lift extra')
src0 = Path('../.github/scripts/vero_msi_gfmul_scale_both_v1.py').read_text()
m0 = re.search(r"probe = r'''(.*)'''\n\np = out", src0, re.S)
if not m0:
    raise RuntimeError('could not extract gfMul base')
base = m0.group(1).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')
extra = strip_imports(m.group(1)).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

su = Path('../.github/scripts/vero_msi_unit_zero_bridge_v1.py').read_text()
mu = re.search(r"probe = r'''(.*)'''\n\np = out", su, re.S)
if not mu:
    raise RuntimeError('could not extract unit-zero block')
unit = strip_imports(mu.group(1))
unit = unit.replace('namespace GaloistoolsMSIUnitZeroBridgeV2', 'namespace GaloistoolsMSIGfMulScaleBothV1')
unit = unit.replace('end GaloistoolsMSIUnitZeroBridgeV2', '')
unit = unit.replace('theorem mul_left_reduce (p a k : Nat) :', 'theorem unit_mul_left_reduce (p a k : Nat) :')
unit = unit.replace('(mul_left_reduce p (z*k) c).symm', '(unit_mul_left_reduce p (z*k) c).symm')

ss = Path('../.github/scripts/vero_monic_scalar_probe_v4.py').read_text()
ms = re.search(r"probe = r'''(.*)'''\n\np = out", ss, re.S)
if not ms:
    raise RuntimeError('could not extract scalar block')
scalar = strip_imports(ms.group(1))

final = r'''

namespace GaloistoolsMSIGfMulScaleBothV1

theorem prove_monic_mul_associate_msi_v5 : spec_monic_mul_associate canonical := by
  simp only [spec_monic_mul_associate, canonical]
  intro f g p hp hnf hng hf hg
  cases f with
  | nil => exact (hf rfl).elim
  | cons a as =>
    cases g with
    | nil => exact (hg rfl).elim
    | cons b bs =>
      have hfa := norm_head_bounds_local p a as hp hnf
      have hgb := norm_head_bounds_local p b bs hp hng
      have hlead := reversed_convolve_lead_nonzero p (a :: as) (b :: bs) hp hnf hng (by simp) (by simp)
      have hmulform :
          Galoistools.gfMul (a :: as) (b :: bs) p =
            (Galoistools.convolve p (a :: as).reverse (b :: bs).reverse).reverse := by
        simp only [Galoistools.gfMul, List.cons_ne_nil, false_or, if_false]
        exact gfStrip_self_of_leadCoeff_ne _ hlead
      have hfr : (a :: as).reverse ≠ [] := by simp
      have hgr : (b :: bs).reverse ≠ [] := by simp
      have hconvlen := convolve_length_local p (a :: as).reverse (b :: bs).reverse hfr hgr
      have hconvne : Galoistools.convolve p (a :: as).reverse (b :: bs).reverse ≠ [] := by
        intro hz
        have hl := congrArg List.length hz
        rw [hconvlen] at hl
        simp at hl
      have hprodhead :
          Galoistools.leadCoeff (Galoistools.gfMul (a :: as) (b :: bs) p) = (a*b)%p := by
        rw [hmulform]
        rw [leadCoeff_reverse_eq_last0 _ hconvne]
        rw [convolve_last0 p _ _ hfr hgr]
        simp only [List.reverse_cons]
        rw [last0_append_singleton, last0_append_singleton]
      simp only [Galoistools.gfMonic]
      trace_state
      simp [Galoistools.gfMul]

end GaloistoolsMSIGfMulScaleBothV1
'''

probe = base + extra + unit + '\nend GaloistoolsMSIGfMulScaleBothV1\n\n' + scalar + final
p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MONIC_MUL_ASSOCIATE_DIRECT_V5_EXIT',cp.returncode)
print(raw[-36000:])
Path('monic_mul_associate_direct_v1').mkdir(exist_ok=True)
Path('monic_mul_associate_direct_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-46000:]},indent=2))
