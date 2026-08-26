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

common = r'''
theorem probe_sub_self (f : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f f p = [] := by
  calc
    Galoistools.gfSub f f p
        = Galoistools.gfAdd f (Galoistools.gfNeg f p) p := prove_sub_eq_add_neg f f p hp
    _ = [] := prove_add_neg_cancel f p hp

theorem probe_norm_impl_identity (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) :
    Galoistools.gfStrip (f.map (fun a => a % p)) = f := by
  change Galoistools.refGfTrunc p f = f at hf
  unfold Galoistools.refGfTrunc at hf
  calc
    Galoistools.gfStrip (f.map (fun a => a % p))
        = Galoistools.refGfStrip (f.map (fun a => a % p)) := ring_gfStrip_eq_ref _
    _ = f := hf

theorem probe_refstrip_no_zero_head (xs as : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: as := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a xs ih =>
      simp only [Galoistools.refGfStrip]
      by_cases ha : a = 0
      · simp [ha, ih]
      · simp [ha]

theorem probe_norm_head_nonzero (a : Nat) (as : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  change Galoistools.refGfTrunc p (0 :: as) = 0 :: as at hf
  unfold Galoistools.refGfTrunc at hf
  simp only [List.map_cons, Nat.zero_mod] at hf
  exact probe_refstrip_no_zero_head (as.map (fun x => x % p)) as hf

theorem probe_norm_strip_identity (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) : Galoistools.gfStrip f = f := by
  cases f with
  | nil => rfl
  | cons a as =>
      have ha := probe_norm_head_nonzero a as p hf
      simp [Galoistools.gfStrip, ha]

theorem probe_divcore_zero_nonempty (p fuel : Nat) (g q : List Nat) (e : Int)
    (hg : g ≠ []) :
    (Galoistools.divCore p g fuel q e []).2 = [] := by
  cases g with
  | nil => contradiction
  | cons a as =>
      cases fuel with
      | zero => simp [Galoistools.divCore, Galoistools.gfStrip]
      | succ n =>
          cases as with
          | nil =>
              simp [Galoistools.divCore, Galoistools.gfStrip, Galoistools.gfDegree]
          | cons b bs =>
              have hdeg : (-1 : Int) < (bs.length : Int) + 1 := by
                change Int.negSucc 0 < Int.ofNat (bs.length + 1)
                revert bs
                decide
              simp [Galoistools.divCore, Galoistools.gfStrip, Galoistools.gfDegree, hdeg]
'''

probes = {
'divcore_zero_nonempty': common + r'''
example (p fuel : Nat) (g q : List Nat) (e : Int) (hg : g ≠ []) :
    (Galoistools.divCore p g fuel q e []).2 = [] :=
  probe_divcore_zero_nonempty p fuel g q e hg
''',
'rem_self_closed': common + r'''
theorem probe_rem_self (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hinv : (Galoistools.leadCoeff f * Galoistools.invMod (Galoistools.leadCoeff f) p) % p = 1) :
    Galoistools.gfRem f f p = [] := by
  have hp1 : 1 < p := hp.1
  have hstrip := probe_norm_strip_identity f p hf
  have htrunc := probe_norm_impl_identity f p hf
  have hsub := probe_sub_self f p hp1
  unfold Galoistools.gfRem Galoistools.gfDiv
  by_cases hz : f = []
  · simp [hz]
  · simp [hz]
    simp only [Galoistools.divCore]
    rw [hstrip]
    simp [hz, hinv, Galoistools.shiftUp, Galoistools.scaleP, htrunc, hsub]
    exact probe_divcore_zero_nonempty p f.length f [1] (-1) hz
''',
'gcd_self_full': common + r'''
theorem probe_rem_self (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hinv : (Galoistools.leadCoeff f * Galoistools.invMod (Galoistools.leadCoeff f) p) % p = 1) :
    Galoistools.gfRem f f p = [] := by
  have hp1 : 1 < p := hp.1
  have hstrip := probe_norm_strip_identity f p hf
  have htrunc := probe_norm_impl_identity f p hf
  have hsub := probe_sub_self f p hp1
  unfold Galoistools.gfRem Galoistools.gfDiv
  by_cases hz : f = []
  · simp [hz]
  · simp [hz]
    simp only [Galoistools.divCore]
    rw [hstrip]
    simp [hz, hinv, Galoistools.shiftUp, Galoistools.scaleP, htrunc, hsub]
    exact probe_divcore_zero_nonempty p f.length f [1] (-1) hz

theorem probe_gcdloop_zero_right (p fuel : Nat) (f : List Nat) :
    Galoistools.gcdLoop p fuel f [] = f := by
  cases fuel with
  | zero => rfl
  | succ n => simp [Galoistools.gcdLoop]

theorem probe_gcd_self_full (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hinv : (Galoistools.leadCoeff f * Galoistools.invMod (Galoistools.leadCoeff f) p) % p = 1) :
    Galoistools.gfGcd f f p = (Galoistools.gfMonic f p).2 := by
  have hrem := probe_rem_self f p hp hf hinv
  unfold Galoistools.gfGcd
  simp only [Galoistools.gcdLoop]
  rw [hrem]
  rw [probe_gcdloop_zero_right]
  simp
''',
}

census = []
for name, theorem_text in probes.items():
    probe = source / f'Probe_{name}.lean'
    probe.write_text(header + theorem_text + footer)
    cp = subprocess.run(['lake','lean', probe.name], cwd=source, text=True, capture_output=True)
    out = cp.stdout + '\n' + cp.stderr
    lines = out.splitlines()
    errors = [line for line in lines if 'error:' in line or line.startswith('error:') or 'error(' in line]
    states = []
    for k, line in enumerate(lines):
        if line.startswith('case ') or '⊢ ' in line:
            states.append('\n'.join(lines[k:k+28]))
    raw_tail = '\n'.join(lines[-120:]) if cp.returncode != 0 else ''
    item = {'probe': name, 'exit': cp.returncode, 'errors': errors[-8:], 'residual': states[-3:], 'raw_tail': raw_tail}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-8:]: print(e)
    for st in states[-3:]: print(st)
    if cp.returncode != 0:
        print(f'--- RAW TAIL {name} ---')
        print(raw_tail)

outdir = Path('batch_harvest')
outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census, indent=2))
print('BATCH_CENSUS', json.dumps(census))