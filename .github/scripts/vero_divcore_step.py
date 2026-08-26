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
'egcd_one_p_residual': r'''
theorem egcd_one_p_residual
    (p : Nat)
    (h1p : ((1 : Int) % Int.ofNat p) = 1)
    (hdiv : ((1 : Int) / Int.ofNat p) = 0)
    (hmid : Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1)) :
    (Galoistools.egcdInt (1 + p) (Int.ofNat p)
      ((1 : Int) % Int.ofNat p)).fst = 1 ∧
    (Galoistools.egcdInt (1 + p) (Int.ofNat p)
      ((1 : Int) % Int.ofNat p)).snd.snd = 1 ∧
    (Galoistools.egcdInt (1 + p) (Int.ofNat p)
      ((1 : Int) % Int.ofNat p)).snd.fst -
      ((1 : Int) / Int.ofNat p) *
        (Galoistools.egcdInt (1 + p) (Int.ofNat p)
          ((1 : Int) % Int.ofNat p)).snd.snd = 0 := by
  rw [h1p, hmid, hdiv]
  simp
''',
'invmod_one_body': r'''
theorem invmod_one_body (p : Nat)
    (h1p : ((1 : Int) % Int.ofNat p) = 1)
    (heg : Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0)) :
    (have r := Galoistools.egcdInt (2 + p) (Int.ofNat 1) (Int.ofNat p)
     (r.snd.fst % Int.ofNat p).toNat) = 1 := by
  change (have r := Galoistools.egcdInt (2 + p) 1 (Int.ofNat p)
          (r.snd.fst % Int.ofNat p).toNat) = 1
  rw [heg]
  change (((1 : Int) % Int.ofNat p).toNat = 1)
  rw [h1p]
  rfl
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
  have hpI0 : (Int.ofNat p) ≠ 0 := by simpa using (show p ≠ 0 by omega)
  have h1p : ((1 : Int) % Int.ofNat p) = 1 :=
    Int.emod_eq_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 :=
    Int.ediv_eq_zero_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hmid : Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) :=
    egcd_p_one_local2 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  rw [Galoistools.egcdInt]
  rw [if_neg hpI0]
  rw [h1p, hmid, hdiv]
  rfl
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
  have hpI0 : (Int.ofNat p) ≠ 0 := by simpa using (show p ≠ 0 by omega)
  have h1p : ((1 : Int) % Int.ofNat p) = 1 :=
    Int.emod_eq_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 :=
    Int.ediv_eq_zero_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hmid : Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := egcd_p_one_local3 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  rw [Galoistools.egcdInt]
  rw [if_neg hpI0]
  rw [h1p, hmid, hdiv]
  rfl

theorem invmod_one (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  have hnat : 1 % p = 1 := Nat.mod_eq_of_lt hp
  have h1p : ((1 : Int) % Int.ofNat p) = 1 :=
    Int.emod_eq_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have heg : Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := egcd_one_p_local3 p hp
  unfold Galoistools.invMod
  rw [hnat]
  rw [show 1 + p + 1 = 2 + p by omega]
  change (have r := Galoistools.egcdInt (2 + p) 1 (Int.ofNat p)
          (r.snd.fst % Int.ofNat p).toNat) = 1
  rw [heg]
  change (((1 : Int) % Int.ofNat p).toNat = 1)
  rw [h1p]
  rfl
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
  have hpI0 : (Int.ofNat p) ≠ 0 := by simpa using (show p ≠ 0 by omega)
  have h1p : ((1 : Int) % Int.ofNat p) = 1 :=
    Int.emod_eq_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hdiv : ((1 : Int) / Int.ofNat p) = 0 :=
    Int.ediv_eq_zero_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have hmid : Galoistools.egcdInt (1 + p) (Int.ofNat p) 1 = (1, 0, 1) := egcd_p_one_local4 p
  rw [show 2 + p = (1 + p) + 1 by omega]
  rw [Galoistools.egcdInt]
  rw [if_neg hpI0]
  rw [h1p, hmid, hdiv]
  rfl

theorem invmod_one_local4 (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p = 1 := by
  have hnat : 1 % p = 1 := Nat.mod_eq_of_lt hp
  have h1p : ((1 : Int) % Int.ofNat p) = 1 :=
    Int.emod_eq_of_lt (by omega) (Int.ofNat_lt.2 hp)
  have heg : Galoistools.egcdInt (2 + p) 1 (Int.ofNat p) = (1, 1, 0) := egcd_one_p_local4 p hp
  unfold Galoistools.invMod
  rw [hnat]
  rw [show 1 + p + 1 = 2 + p by omega]
  change (have r := Galoistools.egcdInt (2 + p) 1 (Int.ofNat p)
          (r.snd.fst % Int.ofNat p).toNat) = 1
  rw [heg]
  change (((1 : Int) % Int.ofNat p).toNat = 1)
  rw [h1p]
  rfl

theorem monic_step_coefficient_reduced (cur g : List Nat) (p : Nat)
    (hp : 1 < p) (hg : Galoistools.refLeadCoeff g = 1)
    (hlc : Galoistools.leadCoeff cur < p) :
    (Galoistools.leadCoeff cur * Galoistools.invMod (Galoistools.leadCoeff g) p) % p =
      Galoistools.leadCoeff cur := by
  have hbridge : Galoistools.leadCoeff g = Galoistools.refLeadCoeff g := by cases g <;> rfl
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
    if cp.returncode: print(item['raw_tail'])

outdir=Path('divcore_step'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIVCORE_STEP_CENSUS',json.dumps(census))
