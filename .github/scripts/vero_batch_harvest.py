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

# Run 98 exposed the missing part of the representation: reconstruction alone
# is not enough because divCore has a fuel=0 branch that can return before the
# quotient's low-degree slots are filled.  The public call starts with enough
# fuel; the inductive statement must carry that budget.  We now test exactly
# that condition and the base-case consequence e < 0.
probes = {
'add_left_zero_direct': r'''
theorem add_left_zero_direct (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfAdd [] f p = f := by
  simpa [Galoistools.gfAdd, Galoistools.zipAddPad, Galoistools.IsNorm,
    Galoistools.refGfTrunc, Galoistools.gfStrip, Galoistools.refGfStrip] using hf
''',
'monic_nonempty_inline': r'''
theorem monic_nonempty_inline (g : List Nat)
    (h : Galoistools.refLeadCoeff g = 1) : g ≠ [] := by
  intro hg
  subst g
  simp [Galoistools.refLeadCoeff] at h
''',
'initial_budget': r'''
theorem initial_budget (f g : List Nat)
    (hd : ¬ Galoistools.gfDegree f < Galoistools.gfDegree g) :
    (Galoistools.gfDegree f - Galoistools.gfDegree g + 1).toNat ≤ f.length + 1 := by
  simp [Galoistools.gfDegree] at hd ⊢
  omega
''',
'zero_budget_forces_complete': r'''
theorem zero_budget_forces_complete (e : Int)
    (hbudget : (e + 1).toNat ≤ 0) : (e + 1).toNat = 0 := by
  omega

theorem zero_budget_completedQ (q : List Nat) (e : Int)
    (hbudget : (e + 1).toNat ≤ 0) :
    Galoistools.gfStrip (q ++ List.replicate (e + 1).toNat 0) =
      Galoistools.gfStrip q := by
  have hz : (e + 1).toNat = 0 := by omega
  simp [hz]
''',
'budget_step': r'''
theorem budget_step (fuel : Nat) (e s : Int)
    (hb : (e + 1).toNat ≤ fuel + 1)
    (hs : s ≤ e) : s.toNat ≤ fuel + 1 := by
  omega
''',
'identity_small_branch': r'''
theorem identity_small_branch (f g : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) (hg : g ≠ [])
    (hd : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfAdd (Galoistools.gfMul (Galoistools.gfDiv f g p).fst g p)
      (Galoistools.gfDiv f g p).snd p = f := by
  simp [Galoistools.gfDiv, hg, hd, Galoistools.gfMul]
  simpa [Galoistools.gfAdd, Galoistools.zipAddPad, Galoistools.IsNorm,
    Galoistools.refGfTrunc, Galoistools.gfStrip, Galoistools.refGfStrip] using hf
''',
'divcore_zero_budget_readout': r'''
def completedQ0 (q : List Nat) (e : Int) : List Nat :=
  Galoistools.gfStrip (q ++ List.replicate (e + 1).toNat 0)

def DivInv0 (p : Nat) (g origin q cur : List Nat) (e : Int) : Prop :=
  Galoistools.gfAdd (Galoistools.gfMul (completedQ0 q e) g p)
    (Galoistools.gfStrip cur) p = origin

theorem divCore_zero_budget_readout (p : Nat) (g origin q cur : List Nat) (e : Int)
    (hbudget : (e + 1).toNat ≤ 0)
    (h : DivInv0 p g origin q cur e) :
    Galoistools.gfAdd
      (Galoistools.gfMul (Galoistools.divCore p g 0 q e cur).1 g p)
      (Galoistools.divCore p g 0 q e cur).2 p = origin := by
  have hz : (e + 1).toNat = 0 := by omega
  simp [Galoistools.divCore, DivInv0, completedQ0, hz] at h ⊢
  simpa using h
''',
'completed_prefix_step_exact': r'''
theorem completed_prefix_step_exact (q : List Nat) (e s : Int) (c : Nat)
    (hs0 : 0 ≤ s) (hse : s ≤ e) :
    let gap := List.replicate (e - s).toNat 0
    let q' := q ++ gap ++ [c]
    q' ++ List.replicate s.toNat 0 =
      q ++ List.replicate (e - s).toNat 0 ++ [c] ++ List.replicate s.toNat 0 := by
  simp
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
