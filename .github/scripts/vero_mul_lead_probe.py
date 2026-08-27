from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
out = Path('mul_lead_probe/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

src = r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulLeadProbe

theorem convolve_last_v1 (p : Nat) : ∀ xs ys : List Nat,
    xs ≠ [] → ys ≠ [] →
    (Galoistools.convolve p xs ys).getLast? =
      match xs.getLast?, ys.getLast? with
      | some a, some b => some ((a * b) % p)
      | _, _ => none := by
  intro xs
  induction xs with
  | nil => simp
  | cons x xs ih =>
      intro ys hxs hys
      cases ys with
      | nil => contradiction
      | cons y ys =>
        by_cases hx : xs = []
        · subst xs
          induction ys with
          | nil => simp [Galoistools.convolve, Galoistools.zipAddPad]
          | cons z zs ihy =>
            simp [Galoistools.convolve, Galoistools.zipAddPad, ihy, Nat.mod_mod]
        · simp only [Galoistools.convolve]
          rw [ih (y :: ys) hx (by simp)]
          simp [Galoistools.zipAddPad, hx, Nat.mod_mod]

end GaloistoolsMulLeadProbe
'''
probe = out/'Probe.lean'; probe.write_text(src)
cp = subprocess.run(['lake','lean',probe.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print(raw)
Path('mul_lead_probe').mkdir(exist_ok=True)
Path('mul_lead_probe/result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(0)
