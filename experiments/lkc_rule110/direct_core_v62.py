#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v58.lean").read_text()

marker = '''namespace Submission

/-- Scored-path Rule110 step with masks deleted where the 256-bit state
invariant already makes them semantically redundant. -/
def bstepBare (m : Nat) : Nat :=
'''

helpers = r'''namespace WideFast

set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

/-- Proof-side name for the direct initializer expression used by V62. -/
def fastPayloadDirect (x : Nat) : Nat :=
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

theorem fastPayloadDirect_eq (x : Nat) :
    fastPayloadDirect x = fastPayload x := by
  rfl

def fastInitDirect (seed : Nat) : Nat :=
  let x := seed + initBias3
  1 + 4 * fastPayloadDirect x

theorem fastInitDirect_eq (seed : Nat) :
    fastInitDirect seed = fastInit seed := by
  unfold fastInitDirect fastInit
  simp only [fastPayloadDirect_eq]

end WideFast

'''

if marker not in base:
    raise SystemExit("v58 insertion marker not found")
base = base.replace(marker, helpers + marker, 1)

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

new_impl = r'''set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

/-- V62 direct scored core: initializer and scored dispatcher are in the body of
`impl`, deleting intermediate delta-reduction layers from target replay. -/
def impl : Nat → Nat := fun n =>
  let seed := caSeed n
  let x := seed + WideFast.initBias3
  let p := x * WideProgression.laneOnes256 +
    stepConst * WideProgression.laneIndex256
  let u := (p ^^^ (p >>> 16)) &&& WideFast.wideMask
  let y := (u * Vec8.c1) &&& WideFast.wideMask
  let v := (y ^^^ (y >>> 15)) &&& WideFast.wideMask
  let raw := v * Vec8.c2
  let sparse := (raw >>> 31) &&& WideProgression.laneOnes256
  let q1 := (sparse ||| (sparse >>> 63)) &&& WideFast.compactMask1
  let q2 := (q1 ||| (q1 >>> 126)) &&& WideFast.compactMask2
  let q3 := (q2 ||| (q2 >>> 252)) &&& WideFast.compactMask3
  let payload := (q3 % WideFast.gatherMod8) &&& WideFast.payloadMask254
  let m := 1 + 4 * payload
  let t := caSteps n
  if t = 2 then
    bstepBare (bstepBare m)
  else if t = 4 then
    bstepBare (bstepBare (bstepBare (bstepBare m)))
  else if t = 8 then
    bstepBare (bstepBare (bstepBare (bstepBare
      (bstepBare (bstepBare (bstepBare (bstepBare m)))))))
  else
    biter t m

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  change biterFastBare (caSteps n) (WideFast.fastInitDirect (caSeed n)) = caSpecN n
  rw [WideFast.fastInitDirect_eq]
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n
'''

if old_impl not in base:
    raise SystemExit("final v58 impl block not found")
base = base.replace(old_impl, new_impl, 1)

path = ROOT / "generated" / "Submission_v62.lean"
path.write_text(base)
print(f"generated {path} bytes={len(base)}")
