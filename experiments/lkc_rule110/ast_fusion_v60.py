#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v58.lean").read_text()

marker = '''namespace Submission

/-- Scored-path Rule110 step with masks deleted where the 256-bit state
invariant already makes them semantically redundant. -/
def bstepBare (m : Nat) : Nat :=
'''

fusion = r'''namespace WideFast

set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

/-- V60: same V58 initializer arithmetic, but with the scored reduction spine
flattened into one definition so kernel replay traverses fewer delta/application
nodes. No algorithmic or semantic change. -/
def fastPayloadFused (x : Nat) : Nat :=
  let p := x * WideProgression.laneOnes256 +
    Submission.stepConst * WideProgression.laneIndex256
  let u := (p ^^^ (p >>> 16)) &&& wideMask
  let y := (u * Submission.Vec8.c1) &&& wideMask
  let v := (y ^^^ (y >>> 15)) &&& wideMask
  let raw := v * Submission.Vec8.c2
  let sparse := (raw >>> 31) &&& WideProgression.laneOnes256
  let q1 := (sparse ||| (sparse >>> 63)) &&& compactMask1
  let q2 := (q1 ||| (q1 >>> 126)) &&& compactMask2
  let q3 := (q2 ||| (q2 >>> 252)) &&& compactMask3
  (q3 % gatherMod8) &&& payloadMask254

theorem fastPayloadFused_eq (x : Nat) :
    fastPayloadFused x = fastPayload x := by
  rfl

def fastInitFused (seed : Nat) : Nat :=
  let x := seed + initBias3
  1 + 4 * fastPayloadFused x

theorem fastInitFused_eq (seed : Nat) :
    fastInitFused seed = fastInit seed := by
  unfold fastInitFused fastInit
  simp only [fastPayloadFused_eq]

end WideFast

'''

if marker not in base:
    raise SystemExit("Submission insertion marker not found")
base = base.replace(marker, fusion + marker, 1)

old_impl = '''def impl : Nat → Nat := fun n =>
  biterFastBare (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n
'''

new_impl = '''def impl : Nat → Nat := fun n =>
  biterFastBare (caSteps n) (WideFast.fastInitFused (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [WideFast.fastInitFused_eq]
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n
'''

if old_impl not in base:
    raise SystemExit("final v58 impl block not found")
base = base.replace(old_impl, new_impl, 1)

path = ROOT / "generated" / "Submission_v60.lean"
path.write_text(base)
print(f"generated {path} bytes={len(base)}")
