from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('batch_harvest/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

# One run, many independent theorem probes.  Each file imports the same seeded
# project, so a failed proof never masks the others.
header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsBatch
'''
footer = '\nend GaloistoolsBatch\n'

probes = {
'norm_head_bounds': r'''
lemma probe_norm_head_bounds (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a ≠ 0 ∧ a < p := by
  unfold Galoistools.IsNorm Galoistools.refGfTrunc at hn
  simp only [Galoistools.refGfStrip, List.map_cons] at hn
  by_cases ha : a = 0
  · subst a
    simp at hn
  · have hma : a % p = a := by
      have hh := congrArg List.head? hn
      simpa [Galoistools.refGfStrip, ha] using hh
    constructor
    · exact ha
    · exact Nat.lt_of_mod_eq_self hma
''',
'prime_nonzero_coprime': r'''
lemma probe_prime_nonzero_coprime (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (halt : a < p) : Nat.gcd a p = 1 := by
  rcases hp with ⟨hp1, hprime⟩
  let d := Nat.gcd a p
  have hda : d ∣ a := Nat.gcd_dvd_left a p
  have hdp : d ∣ p := Nat.gcd_dvd_right a p
  have hdpos : 0 < d := Nat.gcd_pos_of_pos_left p (Nat.pos_of_ne_zero ha0)
  by_contra hne
  have hd2 : 2 ≤ d := by omega
  have hda_le : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
  have hdp_lt : d < p := by omega
  have hmod : p % d = 0 := Nat.mod_eq_zero_of_dvd hdp
  exact hprime d hd2 hdp_lt hmod
''',
'rem_self': r'''
lemma probe_rem_self (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f) :
    Galoistools.gfRem f f p = [] := by
  unfold Galoistools.gfRem Galoistools.gfDiv
  by_cases hz : f = []
  · simp [hz]
  · simp [hz]
    trace_state
    sorry
''',
'rem_norm': r'''
lemma probe_rem_norm (f g : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hg : Galoistools.IsNorm p g) (hz : g ≠ []) :
    Galoistools.IsNorm p (Galoistools.gfRem f g p) := by
  unfold Galoistools.gfRem
  trace_state
  sorry
''',
'rem_degree': r'''
lemma probe_rem_degree (f g : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hg : Galoistools.IsNorm p g) (hz : g ≠ []) :
    let r := Galoistools.gfRem f g p
    r = [] ∨ Galoistools.refGfDegree r < Galoistools.refGfDegree g := by
  dsimp
  unfold Galoistools.gfRem
  trace_state
  sorry
''',
'gcdloop_norm': r'''
lemma probe_gcdloop_norm (f g : List Nat) (p fuel : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hg : Galoistools.IsNorm p g) :
    Galoistools.IsNorm p (Galoistools.gcdLoop p fuel f g) := by
  induction fuel generalizing f g with
  | zero => simpa [Galoistools.gcdLoop] using hf
  | succ fuel ih =>
      simp only [Galoistools.gcdLoop]
      by_cases hz : g = []
      · simp [hz, hf]
      · simp [hz]
        apply ih hg
        trace_state
        sorry
''',
'gcd_self': r'''
lemma probe_gcd_self (f : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p f) :
    Galoistools.gfGcd f f p = (Galoistools.gfMonic f p).2 := by
  unfold Galoistools.gfGcd
  by_cases hz : f = []
  · subst f; simp [Galoistools.gcdLoop, Galoistools.gfMonic]
  · simp [Galoistools.gcdLoop, hz]
    trace_state
    sorry
''',
}

census = []
for name, theorem in probes.items():
    probe = source / f'Probe_{name}.lean'
    probe.write_text(header + theorem + footer)
    cp = subprocess.run(['lake','lean', probe.name], cwd=source, text=True, capture_output=True)
    out = cp.stdout + '\n' + cp.stderr
    lines = out.splitlines()
    errors = [line for line in lines if 'error:' in line or line.startswith('error:')]
    states = []
    for k, line in enumerate(lines):
        if line.startswith('case ') or '⊢ ' in line:
            states.append('\n'.join(lines[k:k+14]))
    item = {'probe': name, 'exit': cp.returncode, 'errors': errors[-8:], 'residual': states[-2:]}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-8:]: print(e)
    for st in states[-2:]: print(st)

outdir = Path('batch_harvest')
outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census, indent=2))
print('BATCH_CENSUS', json.dumps(census))
