from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_unit_zero_bridge_v2/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

probe = r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

namespace GaloistoolsMSIUnitZeroBridgeV2

theorem map_mod_all_lt (p : Nat) (hp : 0 < p) (xs : List Nat) :
    ∀ z ∈ xs.map (fun x => x % p), z < p := by
  intro z hz
  simp only [List.mem_map] at hz
  obtain ⟨x, hx, rfl⟩ := hz
  exact Nat.mod_lt _ hp

theorem zipAddPad_all_lt (p : Nat) (hp : 0 < p) :
    ∀ xs ys : List Nat, ∀ z ∈ Galoistools.zipAddPad p xs ys, z < p := by
  intro xs
  induction xs with
  | nil =>
      intro ys z hz
      exact map_mod_all_lt p hp ys z (by simpa [Galoistools.zipAddPad] using hz)
  | cons x xs ih =>
      intro ys z hz
      cases ys with
      | nil =>
          exact map_mod_all_lt p hp (x :: xs) z (by simpa [Galoistools.zipAddPad] using hz)
      | cons y ys =>
          simp only [Galoistools.zipAddPad, List.mem_cons] at hz
          rcases hz with rfl | hz
          · exact Nat.mod_lt _ hp
          · exact ih ys z hz

theorem convolve_all_lt (p : Nat) (hp : 0 < p) (xs ys : List Nat) :
    ∀ z ∈ Galoistools.convolve p xs ys, z < p := by
  intro z hz
  cases xs with
  | nil => simp [Galoistools.convolve] at hz
  | cons x xs =>
      simp only [Galoistools.convolve] at hz
      exact zipAddPad_all_lt p hp _ _ z hz

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
    have hkc : ((z*k)*c)%p = 0 := by
      calc
        ((z*k)*c)%p = (((z*k)%p)*c)%p := (mul_left_reduce p (z*k) c).symm
        _ = 0 := by rw [hzk]; simp
    have hzunit : (z*(k*c))%p = 0 := by
      calc
        (z*(k*c))%p = ((z*k)*c)%p := by congr 1 <;> ac_rfl
        _ = 0 := hkc
    have hzmodzero : z % p = 0 := by
      calc
        z % p = ((z % p) * 1) % p := by simp
        _ = ((z % p) * ((k*c)%p)) % p := by rw [hunit]
        _ = (z*(k*c))%p := (Nat.mul_mod z (k*c) p).symm
        _ = 0 := hzunit
    rw [Nat.mod_eq_of_lt hz] at hzmodzero
    exact hzmodzero
  · intro hz0
    subst z
    simp

end GaloistoolsMSIUnitZeroBridgeV2
'''

p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MSI_UNIT_ZERO_BRIDGE_V2_EXIT',cp.returncode)
print(raw[-24000:])
Path('msi_unit_zero_bridge_v2').mkdir(exist_ok=True)
Path('msi_unit_zero_bridge_v2/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-32000:]},indent=2))
