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

# Run 102 showed that IsNorm is refGfTrunc p f = f, not merely strip-idempotence.
# The right bridge is therefore structural: refGfStrip can never return a list
# whose head is zero.  Hence a normalized nonempty f cannot start with zero, so
# it is already stripped.  We also avoid the canonical-vs-implementation theorem
# mismatch by proving the implementation left-zero law directly from the same
# frozen/implementation truncation bridge.
probes = {
'ref_strip_ne_zero_head': r'''
theorem ref_strip_ne_zero_head (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]
''',
'norm_head_nonzero': r'''
theorem ref_strip_ne_zero_head_local (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_head_nonzero (a : Nat) (as : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hf
  simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
  exact ref_strip_ne_zero_head_local (0 :: as.map (fun x => x % p)) as h
''',
'norm_ref_strip_self': r'''
theorem ref_strip_ne_zero_head_local2 (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_ref_strip_self (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.refGfStrip f = f := by
  cases f with
  | nil => rfl
  | cons a as =>
      have ha : a ≠ 0 := by
        intro hzero
        subst a
        have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hf
        simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
        exact ref_strip_ne_zero_head_local2 (0 :: as.map (fun x => x % p)) as h
      simp [Galoistools.refGfStrip, ha]
''',
'norm_impl_strip_self': r'''
theorem strip_bridge_local (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem ref_strip_ne_zero_head_local3 (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_impl_strip_self (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfStrip f = f := by
  rw [strip_bridge_local]
  cases f with
  | nil => rfl
  | cons a as =>
      have ha : a ≠ 0 := by
        intro hzero
        subst a
        have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hf
        simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
        exact ref_strip_ne_zero_head_local3 (0 :: as.map (fun x => x % p)) as h
      simp [Galoistools.refGfStrip, ha]
''',
'impl_left_zero_norm': r'''
theorem strip_bridge_local4 (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem impl_left_zero_norm (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfAdd [] f p = f := by
  have ht : Galoistools.gfTrunc p f = f := by
    rw [Galoistools.gfTrunc, strip_bridge_local4]
    exact hf
  simpa [Galoistools.gfAdd, Galoistools.zipAddPad, Galoistools.gfTrunc] using ht
''',
'identity_small_branch_closed': r'''
theorem strip_bridge_local5 (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem impl_left_zero_norm5 (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfAdd [] f p = f := by
  have ht : Galoistools.gfTrunc p f = f := by
    rw [Galoistools.gfTrunc, strip_bridge_local5]
    exact hf
  simpa [Galoistools.gfAdd, Galoistools.zipAddPad, Galoistools.gfTrunc] using ht

theorem identity_small_branch_closed (f g : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) (hg : g ≠ [])
    (hd : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfAdd (Galoistools.gfMul (Galoistools.gfDiv f g p).fst g p)
      (Galoistools.gfDiv f g p).snd p = f := by
  simp [Galoistools.gfDiv, hg, hd, Galoistools.gfMul]
  exact impl_left_zero_norm5 f p hf
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
''',
'budget_step': r'''
theorem budget_step (fuel : Nat) (e s : Int)
    (hb : (e + 1).toNat ≤ fuel + 1)
    (hs : s ≤ e) : s.toNat ≤ fuel + 1 := by
  omega
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
