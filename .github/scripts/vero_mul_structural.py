from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('mul_structural/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulStructural
'''
footer = '\nend GaloistoolsMulStructural\n'

probes = {
'primefield_natprime': r'''
theorem primefield_natprime (p : Nat) (hp : Galoistools.PrimeField p) : Nat.Prime p := by
  by_contra hnp
  have hp2 : 2 ≤ p := by omega
  rw [Nat.not_prime_iff_exists_dvd_lt hp2] at hnp
  rcases hnp with ⟨d, hdvd, hd2, hdlt⟩
  exact hp.2 d hd2 hdlt (Nat.mod_eq_zero_of_dvd hdvd)
''',
'mul_mod_nonzero': r'''
theorem primefield_natprime_local (p : Nat) (hp : Galoistools.PrimeField p) : Nat.Prime p := by
  by_contra hnp
  have hp2 : 2 ≤ p := by omega
  rw [Nat.not_prime_iff_exists_dvd_lt hp2] at hnp
  rcases hnp with ⟨d, hdvd, hd2, hdlt⟩
  exact hp.2 d hd2 hdlt (Nat.mod_eq_zero_of_dvd hdvd)

theorem mul_mod_nonzero (p a b : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (hb0 : b ≠ 0) (ha : a < p) (hb : b < p) :
    (a * b) % p ≠ 0 := by
  intro hz
  have hprime : Nat.Prime p := primefield_natprime_local p hp
  have hdvd : p ∣ a * b := Nat.dvd_of_mod_eq_zero hz
  rcases hprime.dvd_or_dvd hdvd with hpa | hpb
  · have hle : p ≤ a := Nat.le_of_dvd (by omega) hpa
    omega
  · have hle : p ≤ b := Nat.le_of_dvd (by omega) hpb
    omega
''',
'norm_head_bounds': r'''
theorem norm_head_bounds (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) :
    a ≠ 0 ∧ a < p := by
  change Galoistools.refGfStrip ((a % p) :: as.map (fun x => x % p)) = a :: as at hn
  by_cases hz : a % p = 0
  · simp [Galoistools.refGfStrip, hz] at hn
  · have heq : (a % p) :: as.map (fun x => x % p) = a :: as := by
      simpa [Galoistools.refGfStrip, hz] using hn
    have hmod : a % p = a := (List.cons.inj heq).1
    constructor
    · intro ha0
      subst a
      simp at hz
    · rw [← hmod]
      exact Nat.mod_lt _ (by
        intro hp0
        subst p
        simp at hz)
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

outdir=Path('mul_structural'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('MUL_STRUCTURAL_CENSUS',json.dumps(census))
