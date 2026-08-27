from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_invariant/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityInvariant
'''
footer = '\nend GaloistoolsDivIdentityInvariant\n'

probes = {
'shift_singleton_shape': r'''
theorem shift_singleton_shape (s c : Nat) :
    Galoistools.shiftUp s [c] = [c] ++ List.replicate s 0 := by
  simp [Galoistools.shiftUp]
''',
'convolve_singleton_nonempty': r'''
theorem convolve_singleton_nonempty (p c : Nat) (ys : List Nat)
    (hys : ys ≠ []) :
    Galoistools.convolve p [c] ys = ys.map (fun y => (c * y) % p) := by
  have hnil : ∀ xs : List Nat,
      Galoistools.zipAddPad p xs [] = xs.map (· % p) := by
    intro xs
    cases xs <;> rfl
  cases ys with
  | nil => contradiction
  | cons y ys =>
      simp [Galoistools.convolve, Galoistools.zipAddPad, hnil, Nat.mod_mod]
''',
'zipAddPad_replicate_zero_left': r'''
theorem zipAddPad_replicate_zero_left (p n : Nat) (xs : List Nat)
    (hred : xs.map (· % p) = xs) (hlen : n ≤ xs.length) :
    Galoistools.zipAddPad p (List.replicate n 0) xs = xs := by
  induction n generalizing xs with
  | zero =>
      simpa [Galoistools.zipAddPad] using hred
  | succ n ih =>
      cases xs with
      | nil => simp at hlen
      | cons x xs =>
          simp only [List.length_cons, Nat.succ_le_succ_iff] at hlen
          simp only [List.map_cons] at hred
          injection hred with hx hxs
          simp [List.replicate_succ, Galoistools.zipAddPad, hx, ih xs hxs hlen]
''',
'convolve_zero_prefix': r'''
theorem convolve_zero_prefix (p c s : Nat) (ys : List Nat)
    (hys : ys ≠ []) :
    Galoistools.convolve p (List.replicate s 0 ++ [c]) ys =
      List.replicate s 0 ++ ys.map (fun y => (c * y) % p) := by
  have hnil : ∀ xs : List Nat,
      Galoistools.zipAddPad p xs [] = xs.map (· % p) := by
    intro xs
    cases xs <;> rfl
  have hzeros : ∀ n : Nat, ∀ xs : List Nat,
      xs.map (· % p) = xs → n ≤ xs.length →
      Galoistools.zipAddPad p (List.replicate n 0) xs = xs := by
    intro n xs hred hlen
    induction n generalizing xs with
    | zero => simpa [Galoistools.zipAddPad] using hred
    | succ n ih =>
        cases xs with
        | nil => simp at hlen
        | cons x xs =>
            simp only [List.length_cons, Nat.succ_le_succ_iff] at hlen
            simp only [List.map_cons] at hred
            injection hred with hx hxs
            simp [List.replicate_succ, Galoistools.zipAddPad, hx, ih xs hxs hlen]
  have hmap0 : ∀ zs : List Nat,
      zs.map (fun _ => 0) = List.replicate zs.length 0 := by
    intro zs
    induction zs with
    | nil => rfl
    | cons z zs ihz =>
        simp only [List.map_cons, List.length_cons, List.replicate_succ]
        rw [ihz]
  induction s with
  | zero =>
      simp only [List.replicate_zero, List.nil_append]
      cases ys with
      | nil => contradiction
      | cons y ys =>
          simp [Galoistools.convolve, Galoistools.zipAddPad, hnil, Nat.mod_mod]
  | succ s ih =>
      simp only [List.replicate_succ, List.cons_append, Galoistools.convolve]
      rw [ih]
      simp only [Nat.zero_mul, Nat.zero_mod]
      rw [hmap0 ys]
      apply hzeros ys.length
      · simp [Nat.mod_mod]
      · omega
''',
'quotient_term_mul': r'''
theorem quotient_term_mul (p c s : Nat) (g : List Nat) :
    Galoistools.gfMul (Galoistools.shiftUp s [c]) g p =
      Galoistools.shiftUp s (Galoistools.scaleP p c g) := by
  simp [Galoistools.shiftUp, Galoistools.scaleP, Galoistools.gfMul,
    Galoistools.convolve, Galoistools.zipAddPad, Galoistools.gfStrip]
''',
'completed_prefix_shape': r'''
theorem completed_prefix_shape (q : List Nat) (e s : Int) (c : Nat)
    (hs0 : 0 <= s) (hse : s <= e) :
    let oldQ := q ++ List.replicate (e + 1).toNat 0
    let gap := List.replicate (e - s).toNat 0
    let newQ := q ++ gap ++ [c] ++ List.replicate s.toNat 0
    oldQ.length = newQ.length := by
  simp [Int.toNat_of_nonneg hs0]
  omega
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+120]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-500:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_identity_invariant'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_INVARIANT_CENSUS',json.dumps(census))
