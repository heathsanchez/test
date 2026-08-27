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
'eval_append_zeros': r'''
theorem eval_reduced_local (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEval p xs x % p = Galoistools.refPolyEval p xs x := by
  intro xs
  unfold Galoistools.refPolyEval
  induction xs.reverse with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux, Nat.mod_mod]

theorem eval_append_zero_local (p x : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ [0]) x =
      (Galoistools.refPolyEval p f x * x) % p := by
  simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux, Nat.mul_comm]

theorem replicate_succ_tail (n : Nat) :
    List.replicate (n + 1) 0 = List.replicate n 0 ++ [0] := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.replicate_succ, ih]

theorem eval_append_zeros (p x n : Nat) (f : List Nat) (hp : 0 < p) :
    Galoistools.refPolyEval p (f ++ List.replicate n 0) x =
      (Galoistools.refPolyEval p f x * x^n) % p := by
  induction n with
  | zero =>
      simp only [List.replicate_zero, List.append_nil, Nat.pow_zero, Nat.mul_one]
      exact (eval_reduced_local p x f).symm
  | succ n ih =>
      rw [show n + 1 = Nat.succ n by omega]
      rw [show List.replicate (Nat.succ n) 0 = List.replicate n 0 ++ [0] by
        simpa [Nat.succ_eq_add_one] using replicate_succ_tail n]
      rw [← List.append_assoc]
      rw [eval_append_zero_local]
      rw [ih]
      rw [Nat.pow_succ]
      simp only [Nat.mul_mod, Nat.mod_mod]
      ac_rfl
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
