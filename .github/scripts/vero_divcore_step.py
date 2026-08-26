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
'euclid_one_mod': r'''
theorem euclid_one_mod (p : Nat) (hp : 1 < p) :
    ((1 : Int) % (Int.ofNat p)) = 1 := by
  obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
  apply Int.emod_eq_of_lt (by omega)
  norm_num
  omega
''',
'egcd_zero_right': r'''
theorem egcd_zero_right (fuel : Nat) (a : Int) :
    Galoistools.egcdInt fuel a 0 = (a, 1, 0) := by
  cases fuel <;> simp [Galoistools.egcdInt]
''',
'egcd_p_one': r'''
theorem egcd_zero_right_local (fuel : Nat) (a : Int) :
    Galoistools.egcdInt fuel a 0 = (a, 1, 0) := by
  cases fuel <;> simp [Galoistools.egcdInt]

theorem egcd_p_one (p : Nat) :
    Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := by
  have hz : Galoistools.egcdInt p 1 0 = (1, 1, 0) := egcd_zero_right_local p 1
  rw [show 1 + p = p + 1 by omega]
  simp [Galoistools.egcdInt, hz]
''',
'egcd_one_p': r'''
theorem egcd_zero_right_local2 (fuel : Nat) (a : Int) :
    Galoistools.egcdInt fuel a 0 = (a, 1, 0) := by
  cases fuel <;> simp [Galoistools.egcdInt]

theorem egcd_p_one_local2 (p : Nat) :
    Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := by
  have hz : Galoistools.egcdInt p 1 0 = (1, 1, 0) := egcd_zero_right_local2 p 1
  rw [show 1 + p = p + 1 by omega]
  simp [Galoistools.egcdInt, hz]

theorem egcd_one_p (p : Nat) (hp : 1 < p) :
    Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
  have hpI0 : (Int.ofNat p) ≠ 0 := by
    intro h
    have : p = 0 := by simpa using h
    omega
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    apply Int.emod_eq_of_lt (by omega)
    norm_num
    omega
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    norm_num
  have hmid : Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) :=
    egcd_p_one_local2 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  simp [Galoistools.egcdInt, hpI0, h1p, hdiv, hmid]
''',
'invmod_one': r'''
theorem egcd_zero_right_local3 (fuel : Nat) (a : Int) :
    Galoistools.egcdInt fuel a 0 = (a, 1, 0) := by
  cases fuel <;> simp [Galoistools.egcdInt]

theorem egcd_p_one_local3 (p : Nat) :
    Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := by
  have hz : Galoistools.egcdInt p 1 0 = (1, 1, 0) := egcd_zero_right_local3 p 1
  rw [show 1 + p = p + 1 by omega]
  simp [Galoistools.egcdInt, hz]

theorem egcd_one_p_local3 (p : Nat) (hp : 1 < p) :
    Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
  have hpI0 : (Int.ofNat p) ≠ 0 := by
    intro h
    have : p = 0 := by simpa using h
    omega
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    apply Int.emod_eq_of_lt (by omega)
    norm_num
    omega
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    norm_num
  have hmid := egcd_p_one_local3 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  simp [Galoistools.egcdInt, hpI0, h1p, hdiv, hmid]

theorem invmod_one (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    apply Int.emod_eq_of_lt (by omega)
    norm_num
    omega
  have heg := egcd_one_p_local3 p hp
  unfold Galoistools.invMod
  rw [h1p]
  rw [show 1 + p + 1 = 2 + p by omega]
  rw [heg]
  simp [h1p]
''',
'monic_step_coefficient_reduced': r'''
theorem egcd_zero_right_local4 (fuel : Nat) (a : Int) :
    Galoistools.egcdInt fuel a 0 = (a, 1, 0) := by
  cases fuel <;> simp [Galoistools.egcdInt]

theorem egcd_p_one_local4 (p : Nat) :
    Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := by
  have hz : Galoistools.egcdInt p 1 0 = (1, 1, 0) := egcd_zero_right_local4 p 1
  rw [show 1 + p = p + 1 by omega]
  simp [Galoistools.egcdInt, hz]

theorem egcd_one_p_local4 (p : Nat) (hp : 1 < p) :
    Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := by
  have hpI0 : (Int.ofNat p) ≠ 0 := by
    intro h
    have : p = 0 := by simpa using h
    omega
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    apply Int.emod_eq_of_lt (by omega)
    norm_num
    omega
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    norm_num
  have hmid := egcd_p_one_local4 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  simp [Galoistools.egcdInt, hpI0, h1p, hdiv, hmid]

theorem invmod_one_local4 (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  have h1p : ((1 : Int) % Int.ofNat p) = 1 := by
    obtain ⟨k, rfl⟩ : ∃ k, p = k + 2 := by omega
    apply Int.emod_eq_of_lt (by omega)
    norm_num
    omega
  have heg := egcd_one_p_local4 p hp
  unfold Galoistools.invMod
  rw [h1p]
  rw [show 1 + p + 1 = 2 + p by omega]
  rw [heg]
  simp [h1p]

theorem monic_step_coefficient_reduced (cur g : List Nat) (p : Nat)
    (hp : 1 < p) (hg : Galoistools.refLeadCoeff g = 1)
    (hlc : Galoistools.leadCoeff cur < p) :
    (Galoistools.leadCoeff cur * Galoistools.invMod (Galoistools.leadCoeff g) p) % p =
      Galoistools.leadCoeff cur := by
  have hbridge : Galoistools.leadCoeff g = Galoistools.refLeadCoeff g := by
    cases g <;> rfl
  rw [hbridge, hg, invmod_one_local4 p hp]
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
