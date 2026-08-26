from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('batch_harvest/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

div = source / 'Galoistools/Proof/Division.lean'
text = div.read_text()
istart = '-- !benchmark @start imports\n'
iend = '-- !benchmark @end imports\n'
i = text.index(istart) + len(istart)
j = text.index(iend, i)
text = text[:i] + 'import Galoistools.Proof.Ring\n' + text[j:]

lawbook = r'''
namespace GaloistoolsBatch

lemma norm_head_bounds (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a ≠ 0 ∧ a < p := by
  unfold Galoistools.IsNorm Galoistools.refGfTrunc at hn
  simp [Galoistools.refGfStrip] at hn
  by_cases ha : a = 0
  · subst a
    simp [Galoistools.refGfStrip] at hn
  · have hm : a % p = a := by
      simpa [Galoistools.refGfStrip, ha] using congrArg List.head? hn
    constructor
    · exact ha
    · exact Nat.lt_of_mod_eq_self hm

lemma prime_nonzero_coprime (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (halt : a < p) : Nat.gcd a p = 1 := by
  rcases hp with ⟨hp1, hprime⟩
  let d := Nat.gcd a p
  have hda : d ∣ a := Nat.gcd_dvd_left a p
  have hdp : d ∣ p := Nat.gcd_dvd_right a p
  have hdpos : 0 < d := Nat.gcd_pos_of_pos_left p (Nat.pos_of_ne_zero ha0)
  by_contra hne
  have hd2 : 2 ≤ d := by omega
  have hdp_lt : d < p := by
    have hda_le : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
    omega
  have hmod : p % d = 0 := Nat.mod_eq_zero_of_dvd hdp
  exact hprime d hd2 hdp_lt hmod

lemma norm_nonempty_lead_coprime (p : Nat) (h : List Nat)
    (hp : Galoistools.PrimeField p) (hn : Galoistools.IsNorm p h) (hz : h ≠ []) :
    Nat.gcd (Galoistools.refLeadCoeff h) p = 1 := by
  cases h with
  | nil => contradiction
  | cons a as =>
      have hb := norm_head_bounds p a as hn
      simpa [Galoistools.refLeadCoeff] using prime_nonzero_coprime p a hp hb.1 hb.2

end GaloistoolsBatch
'''
anchor = text.index('/-!')
text = text[:anchor] + lawbook + '\n' + text[anchor:]
div.write_text(text)

def replace_slot(text, name, body):
    start = f'-- !benchmark @start proof def={name} kind=prove target='
    s = text.index(start)
    s = text.index('\n', s) + 1
    end = f'-- !benchmark @end proof def={name}\n'
    e = text.index(end, s)
    return text[:s] + body + text[e:]

candidates = {
'prove_gcd_monic': '''  intro f g p hp hf hg
  simp only [canonical]
  let h := Galoistools.gcdLoop p (f.length + g.length + 1) f g
  by_cases hz : h = []
  · left
    simp [Galoistools.gfGcd, h, hz, Galoistools.gfMonic]
  · right
    change Galoistools.refLeadCoeff (Galoistools.gfMonic h p).2 = 1
    apply prove_monic_leadCoeff_one h p hp.1 hz
    apply GaloistoolsBatch.norm_nonempty_lead_coprime p h hp
    trace_state
    sorry
''',
'prove_gcd_self': '''  intro f p hp hf
  simp only [canonical]
  unfold Galoistools.gfGcd
  trace_state
  sorry
''',
'prove_gcd_empty_iff': '''  intro f g p hp hf hg
  simp only [canonical]
  unfold Galoistools.gfGcd
  constructor
  · intro hzero
    trace_state
    sorry
  · rintro ⟨rfl, rfl⟩
    simp [Galoistools.gcdLoop, Galoistools.gfMonic]
''',
'prove_gcd_divides_both': '''  intro f g p hp hf hg
  simp only [canonical]
  trace_state
  sorry
''',
'prove_rem_idempotent': '''  intro f g p hp hg
  simp only [canonical]
  trace_state
  sorry
''',
}

base = div.read_text()
census = []
for name, body in candidates.items():
    div.write_text(replace_slot(base, name, body))
    cp = subprocess.run(['lake','lean','Galoistools/Proof/Division.lean'], cwd=source, text=True, capture_output=True)
    out = cp.stdout + '\n' + cp.stderr
    states = []
    lines = out.splitlines()
    for k, line in enumerate(lines):
        if line.startswith('case ') or '⊢ ' in line:
            states.append('\n'.join(lines[k:k+12]))
    census.append({'slot': name, 'exit': cp.returncode, 'residual': states[-2:]})
    print(f'=== {name} EXIT {cp.returncode} ===')
    for st in states[-2:]:
        print(st)
div.write_text(base)

outdir = Path('batch_harvest')
outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census, indent=2))
print('BATCH_CENSUS', json.dumps(census))
