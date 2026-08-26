from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('divcore_step/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivCoreStep
'''
footer = '\nend GaloistoolsDivCoreStep\n'

probes = {
'available_ring_capabilities': r'''
#check Galoistools.prove_add_zero
#check Galoistools.prove_add_comm
#check Galoistools.prove_add_neg_cancel
#check Galoistools.prove_sub_eq_add_neg
#check Galoistools.prove_mul_one
#check Galoistools.prove_mul_zero
#check Galoistools.prove_mul_eval_hom
#check Galoistools.prove_sub_eval_hom
''',
'divcore_recursive_unfold': r'''
theorem divcore_recursive_unfold
    (p fuel : Nat) (g qacc cur : List Nat) (expDeg : Int)
    (hdeg : ¬ Galoistools.gfDegree (Galoistools.gfStrip cur) < Galoistools.gfDegree g) :
    Galoistools.divCore p g (fuel + 1) qacc expDeg cur =
      let cur0 := Galoistools.gfStrip cur
      let dc := Galoistools.gfDegree cur0
      let dg := Galoistools.gfDegree g
      let c := (Galoistools.leadCoeff cur0 * Galoistools.invMod (Galoistools.leadCoeff g) p) % p
      let s := dc - dg
      let gap := List.replicate (expDeg - s).toNat 0
      let qacc' := qacc ++ gap ++ [c]
      let sub := Galoistools.shiftUp s.toNat (Galoistools.scaleP p c g)
      let cur' := Galoistools.gfSub cur0 sub p
      Galoistools.divCore p g fuel qacc' (s - 1) cur' := by
  simp [Galoistools.divCore, hdeg]
''',
'ref_lead_impl_bridge': r'''
theorem ref_lead_impl_bridge (g : List Nat) :
    Galoistools.leadCoeff g = Galoistools.refLeadCoeff g := by
  cases g <;> rfl
''',
'monic_step_coefficient_shape': r'''
theorem monic_step_coefficient_shape (cur g : List Nat) (p : Nat)
    (hg : Galoistools.refLeadCoeff g = 1) :
    (Galoistools.leadCoeff cur * Galoistools.invMod (Galoistools.leadCoeff g) p) % p =
      (Galoistools.leadCoeff cur * Galoistools.invMod 1 p) % p := by
  have hbridge : Galoistools.leadCoeff g = Galoistools.refLeadCoeff g := by
    cases g <;> rfl
  rw [hbridge, hg]
''',
'invmod_one': r'''
theorem invmod_one (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  simp [Galoistools.invMod, Galoistools.egcdInt, hp]
'''
}

census=[]
for name, text in probes.items():
    probe=source/f'Probe_{name}.lean'
    probe.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',probe.name],cwd=source,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr
    lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+60]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-300:])}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    print(item['raw_tail'])

outdir=Path('divcore_step'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIVCORE_STEP_CENSUS',json.dumps(census))
