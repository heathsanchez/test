from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('quotient_bridge/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsQuotientBridge
'''
footer = '\nend GaloistoolsQuotientBridge\n'

probes = {
'gfStrip_replicate_zero': r'''
theorem gfStrip_replicate_zero (s : Nat) :
    Galoistools.gfStrip (List.replicate s 0) = [] := by
  induction s with
  | zero => rfl
  | succ s ih =>
      simp [List.replicate_succ, Galoistools.gfStrip, ih]
''',
'gfStrip_append_zeros_fixed': r'''
theorem gfStrip_append_zeros_fixed (xs : List Nat) (s : Nat) :
    Galoistools.gfStrip (xs ++ List.replicate s 0) =
      if Galoistools.gfStrip xs = [] then []
      else Galoistools.gfStrip xs ++ List.replicate s 0 := by
  have hz : ∀ n : Nat, Galoistools.gfStrip (List.replicate n 0) = [] := by
    intro n
    induction n with
    | zero => rfl
    | succ n ih => simp [List.replicate_succ, Galoistools.gfStrip, ih]
  induction xs with
  | nil => simp [hz]
  | cons x xs ih =>
      by_cases hx : x = 0
      · simp [Galoistools.gfStrip, hx, ih]
      · simp [Galoistools.gfStrip, hx]
''',
'shift_singleton_reverse': r'''
theorem shift_singleton_reverse (s c : Nat) :
    (Galoistools.shiftUp s [c]).reverse = List.replicate s 0 ++ [c] := by
  simp [Galoistools.shiftUp]
''',
'quotient_term_mul_raw': r'''
theorem quotient_term_mul_raw (p c s : Nat) (g : List Nat) (hg : g ≠ []) :
    Galoistools.gfMul (Galoistools.shiftUp s [c]) g p =
      Galoistools.shiftUp s (Galoistools.scaleP p c g) := by
  have hz : ∀ n : Nat, Galoistools.gfStrip (List.replicate n 0) = [] := by
    intro n
    induction n with
    | zero => rfl
    | succ n ih => simp [List.replicate_succ, Galoistools.gfStrip, ih]
  have hstrip : ∀ xs : List Nat, ∀ n : Nat,
      Galoistools.gfStrip (xs ++ List.replicate n 0) =
        if Galoistools.gfStrip xs = [] then []
        else Galoistools.gfStrip xs ++ List.replicate n 0 := by
    intro xs n
    induction xs with
    | nil => simp [hz]
    | cons x xs ih =>
        by_cases hx : x = 0
        · simp [Galoistools.gfStrip, hx, ih]
        · simp [Galoistools.gfStrip, hx]
  simp only [Galoistools.gfMul, hg, or_false, if_false]
  simp only [Galoistools.shiftUp, Galoistools.scaleP]
  simp only [List.reverse_append, List.reverse_replicate, List.reverse_singleton]
  simp only [List.reverse_reverse, List.map_reverse]
''',
'quotient_term_mul_convolve_target': r'''
theorem quotient_term_mul_convolve_target (p c s : Nat) (g : List Nat) (hg : g ≠ []) :
    Galoistools.convolve p (List.replicate s 0 ++ [c]) g.reverse =
      List.replicate s 0 ++ (g.map (fun y => (c * y) % p)).reverse := by
  have hnil : ∀ xs : List Nat,
      Galoistools.zipAddPad p xs [] = xs.map (· % p) := by
    intro xs
    cases xs <;> rfl
  have hzeros : ∀ n : Nat, ∀ xs : List Nat,
      xs.map (· % p) = xs -> n ≤ xs.length ->
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
    | cons z zs ih => simp [List.replicate_succ, ih]
  induction s with
  | zero =>
      simp only [List.replicate_zero, List.nil_append]
      cases g with
      | nil => contradiction
      | cons y ys => simp [Galoistools.convolve, Galoistools.zipAddPad, hnil, Nat.mod_mod]
  | succ s ih =>
      simp only [List.replicate_succ, List.cons_append, Galoistools.convolve]
      rw [ih]
      simp only [Nat.zero_mul, Nat.zero_mod]
      rw [hmap0 g.reverse]
      apply hzeros g.reverse.length
      · simp [Nat.mod_mod]
      · simp
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+80]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-300:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('quotient_bridge'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('QUOTIENT_BRIDGE_CENSUS',json.dumps(census))
