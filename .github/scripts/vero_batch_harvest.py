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

# Run 99 validated the quotient fuel-budget skeleton.  The only failures were
# the implementation/reference normal-form boundary: gfStrip and refGfStrip are
# byte-for-byte recursive copies, but Lean will not identify distinct defs by
# unfolding under the IsNorm hypothesis.  Close that bridge explicitly, derive
# implementation normalization from frozen IsNorm, then immediately retest the
# small division branch and the divCore readout prerequisites.
probes = {
'strip_bridge': r'''
theorem strip_bridge (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]
''',
'trunc_bridge': r'''
theorem strip_bridge_local (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem trunc_bridge (p : Nat) (f : List Nat) :
    Galoistools.gfStrip (f.map (fun x => x % p)) = Galoistools.refGfTrunc p f := by
  rw [strip_bridge_local]
  rfl
''',
'norm_to_impl_trunc': r'''
theorem strip_bridge_local2 (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_to_impl_trunc (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) :
    Galoistools.gfStrip (f.map (fun x => x % p)) = f := by
  rw [strip_bridge_local2]
  exact hf
''',
'add_left_zero_bridged': r'''
theorem strip_bridge_local3 (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem add_left_zero_bridged (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfAdd [] f p = f := by
  simp [Galoistools.gfAdd, Galoistools.zipAddPad]
  rw [strip_bridge_local3]
  exact hf
''',
'identity_small_branch_bridged': r'''
theorem strip_bridge_local4 (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem identity_small_branch_bridged (f g : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) (hg : g ≠ [])
    (hd : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfAdd (Galoistools.gfMul (Galoistools.gfDiv f g p).fst g p)
      (Galoistools.gfDiv f g p).snd p = f := by
  simp [Galoistools.gfDiv, hg, hd, Galoistools.gfMul]
  simp [Galoistools.gfAdd, Galoistools.zipAddPad]
  rw [strip_bridge_local4]
  exact hf
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
