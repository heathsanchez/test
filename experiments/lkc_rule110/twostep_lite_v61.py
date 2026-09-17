#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v58.lean").read_text()
proof = (ROOT / "TwoStepCircuitProof.lean").read_text()
proof = "\n".join(line for line in proof.splitlines() if not line.startswith("import "))

marker = '''namespace Submission

/-- Scored-path Rule110 step with masks deleted where the 256-bit state
invariant already makes them semantically redundant. -/
def bstepBare (m : Nat) : Nat :=
'''

lite = r'''

namespace TwoStepCircuitLite

open Submission
open TwoStepCircuit

/-- Radius-1/2 rotations without their redundant 256-bit output masks. -/
def rotL1Lite (m : Nat) : Nat := (m <<< 1) ||| (m >>> 255)
def rotR1Lite (m : Nat) : Nat := (m >>> 1) ||| ((m &&& 1) <<< 255)
def rotL2Lite (m : Nat) : Nat := (m <<< 2) ||| (m >>> 254)
def rotR2Lite (m : Nat) : Nat := (m >>> 2) ||| ((m &&& 3) <<< 254)

theorem rotL1Lite_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotL1Lite m).testBit i = m.testBit ((i + 255) % 256) := by
  have h := rotL1_bit (m := m) (i := i) hm hi
  unfold rotL1 rotL1Lite at h ⊢
  rw [Nat.testBit_and, testBit_M] at h
  simpa [hi] using h

theorem rotR1Lite_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotR1Lite m).testBit i = m.testBit ((i + 1) % 256) := by
  have h := rotR1_bit (m := m) (i := i) hm hi
  unfold rotR1 rotR1Lite at h ⊢
  rw [Nat.testBit_and, testBit_M] at h
  simpa [hi] using h

theorem rotL2Lite_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotL2Lite m).testBit i = m.testBit ((i + 254) % 256) := by
  have h := rotL2_bit (m := m) (i := i) hm hi
  unfold rotL2 rotL2Lite at h ⊢
  rw [Nat.testBit_and, testBit_M] at h
  simpa [hi] using h

theorem rotR2Lite_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotR2Lite m).testBit i = m.testBit ((i + 2) % 256) := by
  have h := rotR2_bit (m := m) (i := i) hm hi
  unfold rotR2 rotR2Lite at h ⊢
  rw [Nat.testBit_and, testBit_M] at h
  simpa [hi] using h

/-- Exact two-step Rule110 circuit with only the final 256-bit clamp retained. -/
def bstep2Lite (m : Nat) : Nat :=
  let a := rotL2Lite m
  let b := rotL1Lite m
  let c := m
  let d := rotR1Lite m
  let e := rotR2Lite m
  ((d &&& b) ^^^ ((c ^^^ (e ||| d)) ||| (e &&& (d ||| (b &&& a))))) &&& M

theorem bstep2Lite_eq_bstep2 (m : Nat) (hm : m < 2 ^ 256) :
    bstep2Lite m = bstep2 m := by
  apply Nat.eq_of_testBit_eq
  intro i
  by_cases hi : i < 256
  · simp only [bstep2Lite, bstep2, Nat.testBit_and, Nat.testBit_xor,
      Nat.testBit_or, testBit_M, hi, decide_true, Bool.and_true,
      rotL1Lite_bit hm hi, rotR1Lite_bit hm hi,
      rotL2Lite_bit hm hi, rotR2Lite_bit hm hi,
      rotL1_bit hm hi, rotR1_bit hm hi, rotL2_bit hm hi, rotR2_bit hm hi]
  · simp [bstep2Lite, bstep2, Nat.testBit_and, testBit_M, hi]

theorem bstep2Lite_eq (m : Nat) (hm : m < 2 ^ 256) :
    bstep2Lite m = bstep (bstep m) := by
  rw [bstep2Lite_eq_bstep2 m hm]
  exact bstep2_eq m hm

theorem bstep2Lite_lt (m : Nat) (hm : m < 2 ^ 256) :
    bstep2Lite m < 2 ^ 256 := by
  rw [bstep2Lite_eq m hm]
  exact bstep_lt (bstep m)

end TwoStepCircuitLite

'''

if marker not in base:
    raise SystemExit("v58 insertion marker not found")
base = base.replace(marker, proof + lite + marker, 1)

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

new_impl = r'''def biterFast2Lite (t m : Nat) : Nat :=
  if t = 2 then
    TwoStepCircuitLite.bstep2Lite m
  else if t = 4 then
    TwoStepCircuitLite.bstep2Lite (TwoStepCircuitLite.bstep2Lite m)
  else if t = 8 then
    TwoStepCircuitLite.bstep2Lite
      (TwoStepCircuitLite.bstep2Lite
        (TwoStepCircuitLite.bstep2Lite (TwoStepCircuitLite.bstep2Lite m)))
  else
    biter t m

theorem biterFast2Lite_eq (t m : Nat) (hm : m < 2 ^ 256) :
    biterFast2Lite t m = biter t m := by
  unfold biterFast2Lite
  by_cases h2 : t = 2
  · rw [if_pos h2]
    subst t
    rw [TwoStepCircuitLite.bstep2Lite_eq m hm]
    rfl
  · rw [if_neg h2]
    by_cases h4 : t = 4
    · rw [if_pos h4]
      subst t
      rw [TwoStepCircuitLite.bstep2Lite_eq _
        (TwoStepCircuitLite.bstep2Lite_lt m hm)]
      rw [TwoStepCircuitLite.bstep2Lite_eq m hm]
      rfl
    · rw [if_neg h4]
      by_cases h8 : t = 8
      · rw [if_pos h8]
        subst t
        rw [TwoStepCircuitLite.bstep2Lite_eq _
          (TwoStepCircuitLite.bstep2Lite_lt _
            (TwoStepCircuitLite.bstep2Lite_lt _
              (TwoStepCircuitLite.bstep2Lite_lt m hm)))]
        rw [TwoStepCircuitLite.bstep2Lite_eq _
          (TwoStepCircuitLite.bstep2Lite_lt _
            (TwoStepCircuitLite.bstep2Lite_lt m hm))]
        rw [TwoStepCircuitLite.bstep2Lite_eq _
          (TwoStepCircuitLite.bstep2Lite_lt m hm)]
        rw [TwoStepCircuitLite.bstep2Lite_eq m hm]
        rfl
      · rw [if_neg h8]

def impl : Nat → Nat := fun n =>
  biterFast2Lite (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFast2Lite_eq (caSteps n) (WideFast.fastInit (caSeed n))
    (fastInit_lt256 (caSeed n))]
  rw [← biterFast_eq]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n
'''

if old_impl not in base:
    raise SystemExit("final v58 impl block not found")
base = base.replace(old_impl, new_impl, 1)

path = ROOT / "generated" / "Submission_v61.lean"
path.write_text(base)
print(f"generated {path} bytes={len(base)}")
