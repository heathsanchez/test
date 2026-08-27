from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('quotient_bridge_v2/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsQuotientBridgeV2
'''
footer = '\nend GaloistoolsQuotientBridgeV2\n'

common = r'''
have hconv : ∀ ys : List Nat, ys ≠ [] →
    Galoistools.convolve p (List.replicate s 0 ++ [c]) ys =
      List.replicate s 0 ++ ys.map (fun y => (c * y) % p) := by
  intro ys hys
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
    · simp only [List.length_cons, List.length_append, List.length_replicate, List.length_map]
      omega
'''

probes = {}
probes['convolve_zero_prefix_reuse'] = r'''
theorem convolve_zero_prefix_reuse (p c s : Nat) (ys : List Nat) (hys : ys ≠ []) :
    Galoistools.convolve p (List.replicate s 0 ++ [c]) ys =
      List.replicate s 0 ++ ys.map (fun y => (c * y) % p) := by
''' + common + r'''
  exact hconv ys hys
'''

probes['quotient_term_mul_reuse'] = r'''
theorem quotient_term_mul_reuse (p c s : Nat) (g : List Nat) :
    Galoistools.gfMul (Galoistools.shiftUp s [c]) g p =
      Galoistools.shiftUp s (Galoistools.scaleP p c g) := by
''' + common + r'''
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
    | nil => simpa [Galoistools.gfStrip] using hz n
    | cons x xs ih =>
        by_cases hx : x = 0
        · simp [Galoistools.gfStrip, hx, ih]
        · simp [Galoistools.gfStrip, hx]
  by_cases hg : g = []
  · subst g
    simp [Galoistools.shiftUp, Galoistools.scaleP, Galoistools.gfMul]
  · have hgr : g.reverse ≠ [] := by
      intro h
      apply hg
      have hh := congrArg List.reverse h
      simpa using hh
    simp only [Galoistools.gfMul, Galoistools.shiftUp, Galoistools.scaleP, hg,
      if_false, List.reverse_append, List.reverse_replicate, List.reverse_singleton]
    rw [hconv g.reverse hgr]
    simp only [List.reverse_append, List.map_reverse, List.reverse_replicate,
      List.reverse_reverse]
    rw [hstrip (g.map (fun y => (c * y) % p)) s]
    simp [Nat.mul_comm]
'''

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
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-400:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('quotient_bridge_v2'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('QUOTIENT_BRIDGE_V2_CENSUS',json.dumps(census))
