from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_recursive/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityRecursive
'''
footer = '\nend GaloistoolsDivIdentityRecursive\n'

probes = {
'divcore_stop_unfold': r'''
theorem divcore_stop_unfold
    (p fuel : Nat) (g qacc cur : List Nat) (expDeg : Int)
    (hstrip : Galoistools.gfStrip cur = cur)
    (hlt : Galoistools.gfDegree cur < Galoistools.gfDegree g) :
    Galoistools.divCore p g (fuel + 1) qacc expDeg cur =
      (Galoistools.gfStrip
        (qacc ++ List.replicate (expDeg + 1).toNat 0), cur) := by
  simp [Galoistools.divCore, hstrip, hlt]
''',
'divcore_recursive_unfold': r'''
theorem divcore_recursive_unfold
    (p fuel : Nat) (g qacc cur : List Nat) (expDeg : Int)
    (hstrip : Galoistools.gfStrip cur = cur)
    (hge : ¬ Galoistools.gfDegree cur < Galoistools.gfDegree g) :
    Galoistools.divCore p g (fuel + 1) qacc expDeg cur =
      let c := (Galoistools.leadCoeff cur *
        Galoistools.invMod (Galoistools.leadCoeff g) p) % p
      let s := Galoistools.gfDegree cur - Galoistools.gfDegree g
      let gap := List.replicate (expDeg - s).toNat 0
      let qacc' := qacc ++ gap ++ [c]
      let sub := Galoistools.shiftUp s.toNat (Galoistools.scaleP p c g)
      let cur' := Galoistools.gfSub cur sub p
      Galoistools.divCore p g fuel qacc' (s - 1) cur' := by
  simp [Galoistools.divCore, hstrip, hge]
''',
'divcore_zero_fuel': r'''
theorem divcore_zero_fuel
    (p : Nat) (g qacc cur : List Nat) (expDeg : Int) :
    Galoistools.divCore p g 0 qacc expDeg cur =
      (Galoistools.gfStrip qacc, Galoistools.gfStrip cur) := by
  rfl
''',
'raw_sub_eq_add_neg': r'''
theorem raw_sub_eq_add_neg (f g : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f g p =
      Galoistools.gfAdd f (Galoistools.gfNeg g p) p := by
  simp only [Galoistools.gfSub, Galoistools.gfAdd, Galoistools.gfNeg]
  rw [← List.map_reverse]
  rw [zipSubPad_eq_add_neg]
''',
'raw_add_neg_cancel': r'''
theorem raw_add_neg_cancel (f : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfAdd f (Galoistools.gfNeg f p) p = [] := by
  simp only [Galoistools.gfAdd, Galoistools.gfNeg]
  rw [← List.map_reverse]
  rw [zipAddPad_neg_self p hp]
  simpa [List.map_reverse] using gfStrip_map_zero f
''',
'canonical_sub_bridge': r'''
theorem canonical_sub_bridge (f g : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f g p =
      Galoistools.gfAdd f (Galoistools.gfNeg g p) p := by
  simpa only [canonical] using (prove_sub_eq_add_neg f g p hp)
''',
'canonical_add_neg_bridge': r'''
theorem canonical_add_neg_bridge (f : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfAdd f (Galoistools.gfNeg f p) p = [] := by
  simpa only [canonical] using (prove_add_neg_cancel f p hp)
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-440:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_identity_recursive'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_RECURSIVE_CENSUS',json.dumps(census))
