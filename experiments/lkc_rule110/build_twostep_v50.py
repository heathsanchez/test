#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "Submission_v47.lean").read_text()
base = base.replace(
    "set_option linter.unusedVariables false\n",
    "set_option linter.unusedVariables false\nset_option linter.unnecessarySimpa false\n",
    1,
)
proof = (ROOT / "TwoStepCircuitProof.lean").read_text()
proof = "\n".join(line for line in proof.splitlines() if not line.startswith("import "))

old = '''namespace Submission

def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n

end Submission
'''

new = proof + r'''

namespace WideFast

open Submission

theorem fastInit_lt256 (seed : Nat) :
    fastInit seed < 2 ^ 256 := by
  unfold fastInit
  dsimp
  have hp : fastPayload (seed + 3 * stepConst) ≤ 2 ^ 254 - 1 := by
    unfold fastPayload
    exact Nat.and_le_right
  omega

end WideFast

namespace Submission

open TwoStepCircuit

def biterFast2 (t m : Nat) : Nat :=
  if t = 2 then
    bstep2 m
  else if t = 4 then
    bstep2 (bstep2 m)
  else if t = 8 then
    bstep2 (bstep2 (bstep2 (bstep2 m)))
  else
    biter t m

theorem biterFast2_eq (t m : Nat) (hm : m < 2 ^ 256) :
    biterFast2 t m = biter t m := by
  unfold biterFast2
  by_cases h2 : t = 2
  · rw [if_pos h2]
    subst t
    rw [bstep2_eq m hm]
    rfl
  · rw [if_neg h2]
    by_cases h4 : t = 4
    · rw [if_pos h4]
      subst t
      rw [bstep2_eq (bstep2 m) (bstep2_lt m)]
      rw [bstep2_eq m hm]
      rfl
    · rw [if_neg h4]
      by_cases h8 : t = 8
      · rw [if_pos h8]
        subst t
        rw [bstep2_eq (bstep2 (bstep2 (bstep2 m))) (bstep2_lt _)]
        rw [bstep2_eq (bstep2 (bstep2 m)) (bstep2_lt _)]
        rw [bstep2_eq (bstep2 m) (bstep2_lt _)]
        rw [bstep2_eq m hm]
        rfl
      · rw [if_neg h8]

def impl : Nat → Nat := fun n =>
  biterFast2 (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFast2_eq (caSteps n) (WideFast.fastInit (caSeed n))
        (WideFast.fastInit_lt256 (caSeed n))]
  rw [← biterFast_eq]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n

end Submission
'''

if old not in base:
    raise SystemExit("final Submission block not found")
out = base.replace(old, new, 1)
out_path = ROOT / "generated" / "Submission_v50.lean"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(out)
print(f"generated {out_path} bytes={len(out)}")
