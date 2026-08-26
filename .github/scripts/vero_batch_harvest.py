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

common = r'''
theorem refstrip_no_zero_head (xs as : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: as := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a xs ih =>
      simp only [Galoistools.refGfStrip]
      split <;> simp_all

theorem norm_head_nonzero (a : Nat) (as : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  change Galoistools.refGfTrunc p (0 :: as) = 0 :: as at hf
  unfold Galoistools.refGfTrunc at hf
  simp only [List.map_cons, Nat.zero_mod] at hf
  exact refstrip_no_zero_head (as.map (fun x => x % p)) as hf

theorem norm_head_mod (a : Nat) (as : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p (a :: as)) : a % p = a := by
  have ha : a ≠ 0 := norm_head_nonzero a as p hf
  change Galoistools.refGfTrunc p (a :: as) = a :: as at hf
  unfold Galoistools.refGfTrunc at hf
  simp only [List.map_cons] at hf
  have hamod : a % p ≠ 0 := by
    intro hz
    rw [hz] at hf
    exact refstrip_no_zero_head (as.map (fun x => x % p)) as hf
  simp [Galoistools.refGfStrip, hamod] at hf
  exact hf.1

theorem norm_head_lt (a : Nat) (as : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p (a :: as)) : a < p := by
  have hm := norm_head_mod a as p hf
  have hp0 : 0 < p := by omega
  have hlt := Nat.mod_lt a hp0
  omega
'''

probes = {
'checks': r'''
#check Nat.gcd_dvd_left
#check Nat.gcd_dvd_right
#check Nat.le_of_dvd
#check Nat.mod_eq_zero_of_dvd
#check Nat.dvd_of_mod_eq_zero
#check Nat.gcd_pos_of_pos_left
#check Nat.gcd_pos_of_pos_right
#check Nat.eq_one_of_dvd_one
#check Nat.dvd_one
''',
'norm_head_lt': common + r'''
example (a : Nat) (as : List Nat) (p : Nat)
    (hp : 1 < p) (hf : Galoistools.IsNorm p (a :: as)) : a < p := by
  exact norm_head_lt a as p hp hf
''',
'prime_norm_gcd_one_a': common + r'''
theorem prime_norm_gcd_one (a : Nat) (as : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p (a :: as)) :
    Nat.gcd a p = 1 := by
  have ha0 : a ≠ 0 := norm_head_nonzero a as p hf
  have halt : a < p := norm_head_lt a as p hp.1 hf
  let d := Nat.gcd a p
  have hdA : d ∣ a := Nat.gcd_dvd_left a p
  have hdP : d ∣ p := Nat.gcd_dvd_right a p
  have hdpos : 0 < d := by
    have : 0 < a := Nat.pos_of_ne_zero ha0
    exact Nat.gcd_pos_of_pos_left p this
  have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hdA
  by_contra hne
  have hd2 : 2 ≤ d := by omega
  have hdp : d < p := lt_of_le_of_lt hdle halt
  have hnot := hp.2 d hd2 hdp
  have hz : p % d = 0 := Nat.mod_eq_zero_of_dvd hdP
  exact hnot hz
''',
'prime_norm_gcd_one_b': common + r'''
theorem prime_norm_gcd_one (a : Nat) (as : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p (a :: as)) :
    Nat.gcd a p = 1 := by
  have ha0 : a ≠ 0 := norm_head_nonzero a as p hf
  have halt : a < p := norm_head_lt a as p hp.1 hf
  let d := Nat.gcd a p
  have hdA : d ∣ a := Nat.gcd_dvd_left a p
  have hdP : d ∣ p := Nat.gcd_dvd_right a p
  have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hdA
  have hdne : d ≠ 0 := by
    intro hz
    simp [hz] at hdA
    exact ha0 hdA
  by_contra hne
  have hd2 : 2 ≤ d := by omega
  have hdp : d < p := lt_of_le_of_lt hdle halt
  have hnot := hp.2 d hd2 hdp
  have hz : p % d = 0 := Nat.mod_eq_zero_of_dvd hdP
  exact hnot hz
''',
'lead_inv': common + r'''
theorem prime_norm_gcd_one (a : Nat) (as : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p (a :: as)) :
    Nat.gcd a p = 1 := by
  have ha0 : a ≠ 0 := norm_head_nonzero a as p hf
  have halt : a < p := norm_head_lt a as p hp.1 hf
  let d := Nat.gcd a p
  have hdA : d ∣ a := Nat.gcd_dvd_left a p
  have hdP : d ∣ p := Nat.gcd_dvd_right a p
  have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hdA
  have hdne : d ≠ 0 := by
    intro hz
    simp [hz] at hdA
    exact ha0 hdA
  by_contra hne
  have hd2 : 2 ≤ d := by omega
  have hdp : d < p := lt_of_le_of_lt hdle halt
  have hnot := hp.2 d hd2 hdp
  have hz : p % d = 0 := Nat.mod_eq_zero_of_dvd hdP
  exact hnot hz

example (a : Nat) (as : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p (a :: as)) :
    (a * Galoistools.invMod a p) % p = 1 := by
  have hcop : Nat.gcd a p = 1 := prime_norm_gcd_one a as p hp hf
  have hm := prove_monic_leadCoeff_one (a :: as) p hp.1 (by simp) hcop
  change Galoistools.refLeadCoeff (Galoistools.gfMonic (a :: as) p).2 = 1 at hm
  rw [Galoistools.gfMonic] at hm
  by_cases ha1 : a = 1
  · simp [ha1]
  · simp [ha1, Galoistools.gfQuoGround, Galoistools.refLeadCoeff] at hm
    exact hm
''',
'div_step_drop': common + r'''
example (p : Nat) (g cur : List Nat)
    (hp : Galoistools.PrimeField p)
    (hg : Galoistools.IsNorm p g) (hc : Galoistools.IsNorm p cur)
    (hgn : g ≠ []) (hcn : cur ≠ [])
    (hdeg : Galoistools.gfDegree g ≤ Galoistools.gfDegree cur) :
    let c := (Galoistools.leadCoeff cur * Galoistools.invMod (Galoistools.leadCoeff g) p) % p
    let s := Galoistools.gfDegree cur - Galoistools.gfDegree g
    let sub := Galoistools.shiftUp s.toNat (Galoistools.scaleP p c g)
    Galoistools.gfDegree (Galoistools.gfSub cur sub p) < Galoistools.gfDegree cur := by
  simp only
  sorry
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+28]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-140:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-12:]: print(e)
    for g in goals[-3:]: print(g)
    if cp.returncode: print(item['raw_tail'])

outdir=Path('batch_harvest'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('BATCH_CENSUS',json.dumps(census))
