from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('divcore_step/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivCoreStep
'''
footer = '\nend GaloistoolsDivCoreStep\n'

probes = {
'mod_lemma_inventory': r'''
#check Int.emod_eq_of_lt
#check Int.emod_eq_of_lt_of_nonneg
#check Int.ofNat_pos
''',
'euclid_one_mod': r'''
theorem euclid_one_mod (p : Nat) (hp : 1 < p) :
    ((1 : Int) % (Int.ofNat p)) = 1 := by
  have hpos : (0 : Int) ≤ 1 := by omega
  have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
  exact Int.emod_eq_of_lt hpos hlt
''',
'egcd_p_one': r'''
theorem egcd_p_one (p : Nat) (hp : 1 < p) :
    Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := by
  have hp0 : (Int.ofNat p) ≠ 0 := by
    exact_mod_cast (show p ≠ 0 by omega)
  have hp1 : ((Int.ofNat p) % (1 : Int)) = 0 := by simp
  have hdiv : ((Int.ofNat p) / (1 : Int)) = Int.ofNat p := by simp
  cases p with
  | zero => omega
  | succ p =>
      simp [Galoistools.egcdInt, hp0, hp1, hdiv]
''',
'egcd_one_p': r'''
theorem egcd_one_p (p : Nat) (hp : 1 < p) :
    Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
  have hp0 : (Int.ofNat p) ≠ 0 := by
    exact_mod_cast (show p ≠ 0 by omega)
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
    exact Int.emod_eq_of_lt (by omega) hlt
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
    have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
    exact Int.ediv_eq_zero_of_lt (by omega) hlt
  simp [Galoistools.egcdInt, hp0, h1p, hdiv]
''',
'invmod_one': r'''
theorem invmod_one (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  have hp0 : p ≠ 0 := by omega
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
    exact Int.emod_eq_of_lt (by omega) hlt
  have heg : Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
    have hpI0 : (Int.ofNat p) ≠ 0 := by exact_mod_cast hp0
    have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
      have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
      exact Int.ediv_eq_zero_of_lt (by omega) hlt
    simp [Galoistools.egcdInt, hpI0, h1p, hdiv]
  simp [Galoistools.invMod, hp0, h1p, heg]
''',
'monic_step_coefficient_reduced': r'''
theorem monic_step_coefficient_reduced (cur g : List Nat) (p : Nat)
    (hp : 1 < p) (hg : Galoistools.refLeadCoeff g = 1)
    (hlc : Galoistools.leadCoeff cur < p) :
    (Galoistools.leadCoeff cur * Galoistools.invMod (Galoistools.leadCoeff g) p) % p =
      Galoistools.leadCoeff cur := by
  have hbridge : Galoistools.leadCoeff g = Galoistools.refLeadCoeff g := by
    cases g <;> rfl
  rw [hbridge, hg]
  have hi : Galoistools.invMod 1 p = 1 := by
    have hp0 : p ≠ 0 := by omega
    have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
      have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
      exact Int.emod_eq_of_lt (by omega) hlt
    have heg : Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
      have hpI0 : (Int.ofNat p) ≠ 0 := by exact_mod_cast hp0
      have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
        have hlt : (1 : Int) < Int.ofNat p := by exact_mod_cast hp
        exact Int.ediv_eq_zero_of_lt (by omega) hlt
      simp [Galoistools.egcdInt, hpI0, h1p, hdiv]
    simp [Galoistools.invMod, hp0, h1p, heg]
  rw [hi]
  simp [Nat.mod_eq_of_lt hlc]
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+70]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-320:])}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    print(item['raw_tail'])

outdir=Path('divcore_step'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIVCORE_STEP_CENSUS',json.dumps(census))
