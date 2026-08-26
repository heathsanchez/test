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

# Run 97 exposed the correct recursion boundary.  The quotient accumulator is a
# high-degree prefix; completing it with the still-unfilled low-degree zero slots
# gives the polynomial whose contribution plus `cur` should remain the original
# dividend.  These probes test that representation before attempting induction.
probes = {
'add_left_zero_from_ratchet': r'''
theorem add_left_zero_from_ratchet (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfAdd [] f p = f := by
  rw [prove_add_comm]
  exact prove_add_zero f p hf
''',
'monic_nonempty': r'''
theorem monic_nonempty (g : List Nat)
    (h : Galoistools.refLeadCoeff g = 1) : g ≠ [] := by
  intro hg
  subst g
  simp [Galoistools.refLeadCoeff] at h
''',
'strip_zero_fill': r'''
theorem strip_zero_fill (n : Nat) :
    Galoistools.gfStrip (List.replicate n 0) = [] := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.replicate_succ, Galoistools.gfStrip, ih]
''',
'initial_prefix_identity': r'''
theorem initial_prefix_identity (f g : List Nat) (p k : Nat)
    (hf : Galoistools.IsNorm p f) :
    Galoistools.gfAdd
      (Galoistools.gfMul (Galoistools.gfStrip ([] ++ List.replicate k 0)) g p)
      f p = f := by
  rw [strip_zero_fill]
  simp [Galoistools.gfMul]
  exact add_left_zero_from_ratchet f p hf
''',
'div_identity_split_sharp': r'''
theorem div_identity_split_sharp (f g : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p f) (hgN : Galoistools.IsNorm p g)
    (hmonic : Galoistools.refLeadCoeff g = 1) :
    Galoistools.gfAdd (Galoistools.gfMul (Galoistools.gfDiv f g p).fst g p)
      (Galoistools.gfDiv f g p).snd p = f := by
  have hg : g ≠ [] := monic_nonempty g hmonic
  by_cases hd : Galoistools.gfDegree f < Galoistools.gfDegree g
  · simp [Galoistools.gfDiv, hg, hd, Galoistools.gfMul]
    rw [prove_add_comm]
    apply prove_add_zero
    simpa [Galoistools.IsNorm] using hf
  · simp only [Galoistools.gfDiv, hg, hd, if_false]
''',
'prefix_complete_step_shape': r'''
theorem prefix_complete_step_shape (q : List Nat) (e s : Int) (c : Nat)
    (hes : s ≤ e) (hs : 0 ≤ s) :
    let gap := List.replicate (e - s).toNat 0
    let q' := q ++ gap ++ [c]
    q' ++ List.replicate s.toNat 0 =
      q ++ gap ++ [c] ++ List.replicate s.toNat 0 := by
  simp
''',
'divcore_invariant_statement': r'''
def completedQ (q : List Nat) (e : Int) : List Nat :=
  Galoistools.gfStrip (q ++ List.replicate (e + 1).toNat 0)

def DivInv (p : Nat) (g origin q cur : List Nat) (e : Int) : Prop :=
  Galoistools.gfAdd (Galoistools.gfMul (completedQ q e) g p)
    (Galoistools.gfStrip cur) p = origin

theorem divCore_zero_inv_readout (p : Nat) (g origin q cur : List Nat) (e : Int)
    (h : DivInv p g origin q cur e) :
    Galoistools.gfAdd
      (Galoistools.gfMul (completedQ (Galoistools.divCore p g 0 q e cur).1 (-1)) g p)
      (Galoistools.divCore p g 0 q e cur).2 p = origin := by
  simp [Galoistools.divCore, completedQ, DivInv] at h ⊢
  simpa using h
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+50]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-260:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-12:]: print(e)
    for g in goals[-3:]: print(g)
    if cp.returncode: print(item['raw_tail'])

outdir=Path('batch_harvest'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('BATCH_CENSUS',json.dumps(census))
