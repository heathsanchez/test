from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_unit_zero_bridge_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

probe = r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

namespace GaloistoolsMSIUnitZeroBridgeV1

theorem map_mod_forall_lt (p : Nat) (hp : 0 < p) (xs : List Nat) :
    (xs.map (fun x => x % p)).Forall (fun z => z < p) := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
      simp [ih, Nat.mod_lt _ hp]

theorem zipAddPad_forall_lt (p : Nat) (hp : 0 < p) :
    ∀ xs ys : List Nat,
      (Galoistools.zipAddPad p xs ys).Forall (fun z => z < p) := by
  intro xs
  induction xs with
  | nil =>
      intro ys
      simpa [Galoistools.zipAddPad] using map_mod_forall_lt p hp ys
  | cons x xs ih =>
      intro ys
      cases ys with
      | nil =>
          simpa [Galoistools.zipAddPad] using map_mod_forall_lt p hp (x :: xs)
      | cons y ys =>
          simp [Galoistools.zipAddPad, Nat.mod_lt _ hp, ih ys]

theorem convolve_forall_lt (p : Nat) (hp : 0 < p) (xs ys : List Nat) :
    (Galoistools.convolve p xs ys).Forall (fun z => z < p) := by
  cases xs with
  | nil => simp [Galoistools.convolve]
  | cons x xs =>
      simp only [Galoistools.convolve]
      exact zipAddPad_forall_lt p hp _ _

theorem mul_left_reduce (p a k : Nat) :
    (((a%p)*k)%p) = (a*k)%p := by
  calc
    (((a%p)*k)%p) = ((((a%p)%p)*(k%p))%p) := Nat.mul_mod (a%p) k p
    _ = (((a%p)*(k%p))%p) := by rw [Nat.mod_mod]
    _ = (a*k)%p := (Nat.mul_mod a k p).symm

theorem unit_zero_exact_of_lt
    (p k c z : Nat) (hp : 0 < p) (hz : z < p)
    (hunit : (k*c)%p = 1) :
    ((z*k)%p = 0 ↔ z = 0) := by
  constructor
  · intro hzk
    have hzmod : z % p = z := Nat.mod_eq_of_lt hz
    have hkc : ((z*k)*c)%p = 0 := by
      calc
        ((z*k)*c)%p = (((z*k)%p)*c)%p := (mul_left_reduce p (z*k) c).symm
        _ = 0 := by rw [hzk]; simp
    have hzunit : (z*(k*c))%p = 0 := by
      calc
        (z*(k*c))%p = ((z*k)*c)%p := by congr 1 <;> ac_rfl
        _ = 0 := hkc
    have hz1 : (z*1)%p = 0 := by
      simpa [hunit] using hzunit
    simpa [hzmod] using hz1
  · intro hz0
    subst z
    simp

end GaloistoolsMSIUnitZeroBridgeV1
'''

p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MSI_UNIT_ZERO_BRIDGE_V1_EXIT',cp.returncode)
print(raw[-24000:])
Path('msi_unit_zero_bridge_v1').mkdir(exist_ok=True)
Path('msi_unit_zero_bridge_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-32000:]},indent=2))
