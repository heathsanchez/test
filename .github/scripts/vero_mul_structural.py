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

norm_helpers = r'''
theorem ref_strip_ne_zero_head_mul (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_head_nonzero_mul (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hn
  simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
  exact ref_strip_ne_zero_head_mul (0 :: as.map (fun x => x % p)) as h

theorem strip_len_mul (xs : List Nat) :
    (Galoistools.refGfStrip xs).length ≤ xs.length := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases ha : a = 0
      · simp [ha]
        omega
      · simp [ha]

theorem norm_head_mod_eq_mul (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a % p = a := by
  change Galoistools.refGfStrip ((a % p) :: as.map (fun x => x % p)) = a :: as at hn
  by_cases hz : a % p = 0
  · have hlen := congrArg List.length hn
    have hle := strip_len_mul (as.map (fun x => x % p))
    simp [Galoistools.refGfStrip, hz] at hlen
    simp at hle
    omega
  · have heq : (a % p) :: as.map (fun x => x % p) = a :: as := by
      simpa [Galoistools.refGfStrip, hz] using hn
    exact (List.cons.inj heq).1
'''

coprime_helper = r'''
theorem primefield_coprime_lt_local (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (ha : a < p) : p.Coprime a := by
  have hgcd : Nat.gcd a p = 1 := by
    let d := Nat.gcd a p
    have hda : d ∣ a := Nat.gcd_dvd_left a p
    have hdp : d ∣ p := Nat.gcd_dvd_right a p
    have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
    have hdlt : d < p := by omega
    by_cases hd1 : d = 1
    · exact hd1
    · have hd2 : 2 ≤ d := by
        have hdpos : 0 < d := Nat.pos_of_dvd_of_pos hdp (by omega)
        omega
      have hnot := hp.2 d hd2 hdlt
      exact (hnot (Nat.mod_eq_zero_of_dvd hdp)).elim
  rw [Nat.coprime_comm]
  exact hgcd
'''

probes = {
'norm_head_bounds': norm_helpers + r'''
theorem norm_head_bounds (p a : Nat) (as : List Nat)
    (hp : Galoistools.PrimeField p) (hn : Galoistools.IsNorm p (a :: as)) :
    a ≠ 0 ∧ a < p := by
  have ha0 := norm_head_nonzero_mul p a as hn
  have hmod := norm_head_mod_eq_mul p a as hn
  have hp0 : 0 < p := by omega
  constructor
  · exact ha0
  · rw [← hmod]
    exact Nat.mod_lt _ hp0
''',
'primefield_coprime_lt': coprime_helper + r'''
theorem primefield_coprime_lt (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (ha : a < p) : p.Coprime a :=
  primefield_coprime_lt_local p a hp ha0 ha
''',
'mul_mod_nonzero': coprime_helper + r'''
theorem mul_mod_nonzero (p a b : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (hb0 : b ≠ 0) (ha : a < p) (hb : b < p) :
    (a * b) % p ≠ 0 := by
  intro hz
  have hcop : p.Coprime a := primefield_coprime_lt_local p a hp ha0 ha
  have hdvd : p ∣ a * b := Nat.dvd_of_mod_eq_zero hz
  have hpb : p ∣ b := hcop.dvd_of_dvd_mul_left hdvd
  have hle : p ≤ b := Nat.le_of_dvd (Nat.pos_of_ne_zero hb0) hpb
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-400:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('mul_structural'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('MUL_STRUCTURAL_CENSUS',json.dumps(census))
