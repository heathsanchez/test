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

# Second-stage batch: push the shared Euclidean invariants one layer deeper.
# In particular, determine whether rem_self alone collapses gcd_self and make
# gcdLoop-normalization reduce explicitly to remainder-normalization.
probes = {
'rem_self_step': r'''
theorem probe_rem_self_step (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f) :
    Galoistools.gfRem f f p = [] := by
  unfold Galoistools.gfRem Galoistools.gfDiv
  by_cases hz : f = []
  · simp [hz]
  · simp [hz]
    simp only [Galoistools.divCore]
    trace_state
    sorry
''',
'gcd_self_from_rem': r'''
theorem probe_gcd_self_from_rem (f : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p f)
    (hrem : Galoistools.gfRem f f p = []) :
    Galoistools.gfGcd f f p = (Galoistools.gfMonic f p).2 := by
  unfold Galoistools.gfGcd
  by_cases hz : f = []
  · subst f; simp [Galoistools.gcdLoop, Galoistools.gfMonic]
  · simp [Galoistools.gcdLoop, hz, hrem]
''',
'gcdloop_norm_from_remnorm': r'''
theorem probe_gcdloop_norm_from_remnorm (f g : List Nat) (p fuel : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hg : Galoistools.IsNorm p g)
    (hremnorm : ∀ a b, Galoistools.IsNorm p a → Galoistools.IsNorm p b → b ≠ [] →
      Galoistools.IsNorm p (Galoistools.gfRem a b p)) :
    Galoistools.IsNorm p (Galoistools.gcdLoop p fuel f g) := by
  induction fuel generalizing f g with
  | zero => simpa [Galoistools.gcdLoop] using hf
  | succ fuel ih =>
      simp only [Galoistools.gcdLoop]
      by_cases hz : g = []
      · simp [hz, hf]
      · simp [hz]
        exact ih hg (hremnorm f g hf hg hz)
''',
'rem_norm_unfold': r'''
theorem probe_rem_norm_unfold (f g : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hg : Galoistools.IsNorm p g) (hz : g ≠ []) :
    Galoistools.IsNorm p (Galoistools.gfRem f g p) := by
  unfold Galoistools.gfRem Galoistools.gfDiv
  simp [hz]
  by_cases hdeg : Galoistools.gfDegree f < Galoistools.gfDegree g
  · simp [hdeg]
    trace_state
    sorry
  · simp [hdeg]
    trace_state
    sorry
''',
'rem_degree_unfold': r'''
theorem probe_rem_degree_unfold (f g : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hg : Galoistools.IsNorm p g) (hz : g ≠ []) :
    let r := Galoistools.gfRem f g p
    r = [] ∨ Galoistools.refGfDegree r < Galoistools.refGfDegree g := by
  dsimp
  unfold Galoistools.gfRem Galoistools.gfDiv
  simp [hz]
  by_cases hdeg : Galoistools.gfDegree f < Galoistools.gfDegree g
  · simp [hdeg]
    trace_state
    sorry
  · simp [hdeg]
    trace_state
    sorry
''',
}

census = []
for name, theorem_text in probes.items():
    probe = source / f'Probe_{name}.lean'
    probe.write_text(header + theorem_text + footer)
    cp = subprocess.run(['lake','lean', probe.name], cwd=source, text=True, capture_output=True)
    out = cp.stdout + '\n' + cp.stderr
    lines = out.splitlines()
    errors = [line for line in lines if 'error:' in line or line.startswith('error:')]
    states = []
    for k, line in enumerate(lines):
        if line.startswith('case ') or '⊢ ' in line:
            states.append('\n'.join(lines[k:k+18]))
    item = {'probe': name, 'exit': cp.returncode, 'errors': errors[-8:], 'residual': states[-3:]}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-8:]: print(e)
    for st in states[-3:]: print(st)

outdir = Path('batch_harvest')
outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census, indent=2))
print('BATCH_CENSUS', json.dumps(census))
