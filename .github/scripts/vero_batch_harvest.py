from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('batch_harvest/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsBatch
'''
footer = '\nend GaloistoolsBatch\n'

# We deliberately stop probing invMod/egcd internals here.  The 23/48 plateau
# says the next useful object must live at the division recursion boundary.
# These probes expose the exact induction interface of divCore before we commit
# to a large proof: base case, early-stop case, recursive-step equation, and the
# public gfDiv unfolding under the scored hypotheses.
probes = {
'divcore_zero': r'''
theorem divCore_zero (p : Nat) (g q cur : List Nat) (e : Int) :
    Galoistools.divCore p g 0 q e cur =
      (Galoistools.gfStrip q, Galoistools.gfStrip cur) := by
  rfl
''',
'divcore_stop': r'''
theorem divCore_stop (p fuel : Nat) (g q cur : List Nat) (e : Int)
    (h : Galoistools.gfDegree (Galoistools.gfStrip cur) < Galoistools.gfDegree g) :
    Galoistools.divCore p g (fuel+1) q e cur =
      (Galoistools.gfStrip (q ++ List.replicate (e+1).toNat 0),
       Galoistools.gfStrip cur) := by
  simp [Galoistools.divCore, h]
''',
'divcore_step': r'''
theorem divCore_step (p fuel : Nat) (g q cur : List Nat) (e : Int)
    (h : ¬ Galoistools.gfDegree (Galoistools.gfStrip cur) < Galoistools.gfDegree g) :
    let cur0 := Galoistools.gfStrip cur
    let dg := Galoistools.gfDegree g
    let dc := Galoistools.gfDegree cur0
    let c := (Galoistools.leadCoeff cur0 * Galoistools.invMod (Galoistools.leadCoeff g) p) % p
    let s := dc - dg
    let gap := List.replicate (e - s).toNat 0
    let q' := q ++ gap ++ [c]
    let sub := Galoistools.shiftUp s.toNat (Galoistools.scaleP p c g)
    let cur' := Galoistools.gfSub cur0 sub p
    Galoistools.divCore p g (fuel+1) q e cur =
      Galoistools.divCore p g fuel q' (s-1) cur' := by
  simp [Galoistools.divCore, h]
''',
'gfdiv_unfold_monic': r'''
theorem gfDiv_unfold_monic (f g : List Nat) (p : Nat)
    (hg : g ≠ [])
    (hdeg : ¬ Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfDiv f g p =
      Galoistools.divCore p g (f.length+1) []
        (Galoistools.gfDegree f - Galoistools.gfDegree g) f := by
  simp [Galoistools.gfDiv, hg, hdeg]
''',
'div_identity_split': r'''
theorem div_identity_split (f g : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p f) (hgN : Galoistools.IsNorm p g)
    (hmonic : Galoistools.refLeadCoeff g = 1) :
    Galoistools.gfAdd (Galoistools.gfMul (Galoistools.gfDiv f g p).fst g p)
      (Galoistools.gfDiv f g p).snd p = f := by
  by_cases hg : g = []
  · subst g
    simp [Galoistools.gfDiv]
  by_cases hd : Galoistools.gfDegree f < Galoistools.gfDegree g
  · simp [Galoistools.gfDiv, hg, hd]
    simpa using hf
  · simp only [Galoistools.gfDiv, hg, hd, if_false]
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+40]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-220:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-12:]: print(e)
    for g in goals[-3:]: print(g)
    if cp.returncode: print(item['raw_tail'])

outdir=Path('batch_harvest'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('BATCH_CENSUS',json.dumps(census))
