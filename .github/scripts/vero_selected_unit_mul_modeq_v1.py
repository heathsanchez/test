from pathlib import Path
import subprocess, json, re
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('selected_unit_mul_modeq_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

ss = Path('../.github/scripts/vero_monic_scalar_probe_v4.py').read_text()
ms = re.search(r"probe = r'''(.*)'''\n\np = out", ss, re.S)
if not ms:
    raise RuntimeError('could not extract scalar block')
scalar = ms.group(1)

extra = r'''

def selectedUnit (p a : Nat) : Nat :=
  if a = 1 then 1 else Galoistools.invMod a p

theorem selectedUnit_mul_modeq
    (p a b : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (hb0 : b ≠ 0) (ha : a < p) (hb : b < p) :
    NatModEq p
      (selectedUnit p ((a*b)%p))
      (selectedUnit p a * selectedUnit p b) := by
  unfold selectedUnit
  by_cases ha1 : a = 1
  · subst a
    have hbmod : b % p = b := Nat.mod_eq_of_lt hb
    simp [hbmod]
    rfl
  · by_cases hb1 : b = 1
    · subst b
      have hamod : a % p = a := Nat.mod_eq_of_lt ha
      simp [hamod]
      rfl
    · by_cases hc1 : (a*b)%p = 1
      · simp [ha1, hb1, hc1]
        have hpair : ((a*b) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p = 1 := by
          have hp1 : 1 < p := hp.1
          have hcopA : Nat.gcd a p = 1 := by
            have h := primefield_coprime_lt_local2 p a hp ha0 ha
            simpa [Nat.coprime_comm] using h
          have hcopB : Nat.gcd b p = 1 := by
            have h := primefield_coprime_lt_local2 p b hp hb0 hb
            simpa [Nat.coprime_comm] using h
          have hia := inv_correct_nonone p a hp1 ha1 hcopA
          have hib := inv_correct_nonone p b hp1 hb1 hcopB
          calc
            ((a*b) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p
                = ((a * Galoistools.invMod a p) * (b * Galoistools.invMod b p)) % p := by
                    congr 1
                    ac_rfl
            _ = (((a * Galoistools.invMod a p) % p) *
                   ((b * Galoistools.invMod b p) % p)) % p := by
                    rw [Nat.mul_mod]
            _ = 1 := by simp [hia, hib, Nat.mod_eq_of_lt hp1]
        have hpair' : (((a*b)%p) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p = 1 := by
          simpa [Nat.mul_mod] using hpair
        rw [hc1] at hpair'
        have hprod : (Galoistools.invMod a p * Galoistools.invMod b p) % p = 1 := by
          simpa [Nat.mod_eq_of_lt hp.1] using hpair'
        unfold NatModEq
        simpa [Nat.mod_eq_of_lt hp.1] using hprod.symm
      · simpa [ha1, hb1, hc1] using
          inv_product_modeq p a b hp ha0 hb0 ha hb ha1 hb1 hc1
'''

probe = scalar + extra
p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('SELECTED_UNIT_MUL_MODEQ_V2_EXIT',cp.returncode)
print(raw[-26000:])
Path('selected_unit_mul_modeq_v1').mkdir(exist_ok=True)
Path('selected_unit_mul_modeq_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-36000:]},indent=2))
