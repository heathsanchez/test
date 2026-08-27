from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_scalar_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

probe = r'''import Galoistools.Proof.Ring

#check Nat.ModEq
#check Nat.ModEq.cancel_left_of_coprime
#check Nat.ModEq.eq_of_lt_of_lt

theorem inv_correct_nonone (p a : Nat) (hp : 1 < p)
    (ha : a ≠ 1) (hcop : Nat.gcd a p = 1) :
    (a * Galoistools.invMod a p) % p = 1 := by
  have h := prove_monic_leadCoeff_one [a] p hp (by simp) hcop
  simpa [canonical, Galoistools.gfMonic, Galoistools.gfQuoGround,
    Galoistools.refLeadCoeff, ha] using h

theorem inv_product_modeq (p a b : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (hb0 : b ≠ 0) (ha : a < p) (hb : b < p)
    (ha1 : a ≠ 1) (hb1 : b ≠ 1)
    (hc1 : (a * b) % p ≠ 1) :
    NatModEq p
      (Galoistools.invMod ((a * b) % p) p)
      (Galoistools.invMod a p * Galoistools.invMod b p) := by
  have hp1 : 1 < p := hp.1
  have hc0 : (a * b) % p ≠ 0 :=
    mul_mod_nonzero_local p a b hp ha0 hb0 ha hb
  have hca : ((a * b) % p) < p := Nat.mod_lt _ (by omega)
  have hcopA : Nat.gcd a p = 1 := by
    have h := primefield_coprime_lt_local2 p a hp ha0 ha
    simpa [Nat.coprime_comm] using h
  have hcopB : Nat.gcd b p = 1 := by
    have h := primefield_coprime_lt_local2 p b hp hb0 hb
    simpa [Nat.coprime_comm] using h
  have hcopC : Nat.gcd ((a*b)%p) p = 1 := by
    have h := primefield_coprime_lt_local2 p ((a*b)%p) hp hc0 hca
    simpa [Nat.coprime_comm] using h
  have hia := inv_correct_nonone p a hp1 ha1 hcopA
  have hib := inv_correct_nonone p b hp1 hb1 hcopB
  have hic := inv_correct_nonone p ((a*b)%p) hp1 hc1 hcopC
  have hpair : ((a*b) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p = 1 := by
    calc
      ((a*b) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p
          = ((a * Galoistools.invMod a p) * (b * Galoistools.invMod b p)) % p := by
              congr 1 <;> omega
      _ = (((a * Galoistools.invMod a p) % p) *
             ((b * Galoistools.invMod b p) % p)) % p := by
              rw [Nat.mul_mod]
      _ = 1 := by simp [hia, hib, Nat.mod_eq_of_lt hp1]
  have hleft : (((a*b)%p) * Galoistools.invMod ((a*b)%p) p) % p = 1 := hic
  have hright : (((a*b)%p) * (Galoistools.invMod a p * Galoistools.invMod b p)) % p = 1 := by
    simpa [Nat.mul_mod] using hpair
  have hm : Nat.ModEq p
      (((a*b)%p) * Galoistools.invMod ((a*b)%p) p)
      (((a*b)%p) * (Galoistools.invMod a p * Galoistools.invMod b p)) := by
    exact hleft.trans hright.symm
  have hcancel := Nat.ModEq.cancel_left_of_coprime hcopC hm
  exact hcancel
'''

p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MONIC_SCALAR_V1_EXIT',cp.returncode)
print(raw[-20000:])
Path('monic_scalar_v1').mkdir(exist_ok=True)
Path('monic_scalar_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-30000:]},indent=2))
