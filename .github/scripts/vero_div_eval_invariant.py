from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_eval_invariant/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivEvalInvariant
'''
footer = '\nend GaloistoolsDivEvalInvariant\n'

probes = {
'eval_reduced': r'''
theorem eval_reduced (p x : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    Galoistools.refPolyEval p xs x % p = Galoistools.refPolyEval p xs x := by
  intro xs
  unfold Galoistools.refPolyEval
  induction xs.reverse with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux, Nat.mod_mod]
''',
'eval_append_zero': r'''
theorem eval_append_zero (p x : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ [0]) x =
      (Galoistools.refPolyEval p f x * x) % p := by
  simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux, Nat.mul_comm]
''',
'eval_zero_prefix_aux': r'''
theorem aux_reduced (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x xs % p = Galoistools.refPolyEvalRevAux p x xs := by
  intro xs
  cases xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as => simp [Galoistools.refPolyEvalRevAux, Nat.mod_mod]

theorem eval_zero_prefix_aux (p x n : Nat) (xs : List Nat) :
    Galoistools.refPolyEvalRevAux p x (List.replicate n 0 ++ xs) =
      (x^n * Galoistools.refPolyEvalRevAux p x xs) % p := by
  induction n with
  | zero =>
      simp only [List.replicate_zero, List.nil_append, pow_zero, Nat.one_mul]
      symm
      exact aux_reduced p x xs
  | succ n ih =>
      simp only [List.replicate_succ, List.cons_append, Galoistools.refPolyEvalRevAux,
        Nat.zero_add, ih, pow_succ]
      rw [Nat.mul_mod]
      rw [Nat.mul_mod]
      simp only [Nat.mod_mod]
      ac_rfl
''',
'eval_append_zeros': r'''
theorem aux_reduced2 (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x xs % p = Galoistools.refPolyEvalRevAux p x xs := by
  intro xs
  cases xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as => simp [Galoistools.refPolyEvalRevAux, Nat.mod_mod]

theorem zero_prefix_aux2 (p x n : Nat) (xs : List Nat) :
    Galoistools.refPolyEvalRevAux p x (List.replicate n 0 ++ xs) =
      (x^n * Galoistools.refPolyEvalRevAux p x xs) % p := by
  induction n with
  | zero =>
      simp only [List.replicate_zero, List.nil_append, pow_zero, Nat.one_mul]
      symm
      exact aux_reduced2 p x xs
  | succ n ih =>
      simp only [List.replicate_succ, List.cons_append, Galoistools.refPolyEvalRevAux,
        Nat.zero_add, ih, pow_succ]
      rw [Nat.mul_mod]
      rw [Nat.mul_mod]
      simp only [Nat.mod_mod]
      ac_rfl

theorem eval_append_zeros (p x n : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ List.replicate n 0) x =
      (Galoistools.refPolyEval p f x * x^n) % p := by
  unfold Galoistools.refPolyEval
  rw [List.reverse_append, List.reverse_replicate]
  rw [zero_prefix_aux2]
  simp [Nat.mul_comm]
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
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-400:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_eval_invariant'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_EVAL_INVARIANT_CENSUS',json.dumps(census))
