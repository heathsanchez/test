#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v54.lean").read_text()

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

new = '''namespace Submission

/-- Scored-path Rule110 step with masks deleted where the 256-bit state
invariant already makes them semantically redundant. -/
def bstepBare (m : Nat) : Nat :=
  let l := (m <<< 1) ||| (m >>> 255)
  let r := (m >>> 1) ||| ((m &&& 1) <<< 255)
  (m ||| r) ^^^ (l &&& m &&& r)

theorem bstep_lt256 (m : Nat) : bstep m < 2 ^ 256 := by
  unfold bstep
  have hM : M < 2 ^ 256 := by
    rw [M_eq]
    omega
  exact Nat.lt_of_le_of_lt Nat.and_le_right hM

theorem bstepBare_eq (m : Nat) (hm : m < 2 ^ 256) :
    bstepBare m = bstep m := by
  apply Nat.eq_of_testBit_eq
  intro i
  by_cases hi : i < 256
  · unfold bstepBare bstep
    simp only [Nat.testBit_xor, Nat.testBit_or, Nat.testBit_and,
      Nat.testBit_shiftLeft, Nat.testBit_shiftRight]
    simp [testBit_M, hi]
  · have hge : 256 ≤ i := by omega
    have h255 : 255 ≤ i := by omega
    have hmi : m.testBit i = false := testBit_high hm hge
    have hmip1 : m.testBit (1 + i) = false := testBit_high hm (by omega)
    have hsub : i - 255 ≠ 0 := by omega
    have hone : (1 : Nat).testBit (i - 255) = false := by
      cases hb : (1 : Nat).testBit (i - 255) with
      | false => rfl
      | true =>
          have hz := Nat.testBit_one_eq_true_iff_self_eq_zero.mp hb
          exact (hsub hz).elim
    unfold bstepBare bstep
    simp only [Nat.testBit_xor, Nat.testBit_or, Nat.testBit_and,
      Nat.testBit_shiftLeft, Nat.testBit_shiftRight]
    simp [testBit_M, hi, hge, h255, hmi, hmip1, hone]

theorem bstepBare_lt256 (m : Nat) (hm : m < 2 ^ 256) :
    bstepBare m < 2 ^ 256 := by
  rw [bstepBare_eq m hm]
  exact bstep_lt256 m

/-- Keep the generic fallback untouched; only the scored 2/4/8-step paths
use the maskless primitive. -/
def biterFastBare (t m : Nat) : Nat :=
  if t = 2 then
    bstepBare (bstepBare m)
  else if t = 4 then
    bstepBare (bstepBare (bstepBare (bstepBare m)))
  else if t = 8 then
    bstepBare (bstepBare (bstepBare (bstepBare
      (bstepBare (bstepBare (bstepBare (bstepBare m)))))))
  else
    biter t m

theorem biterFastBare_eq_biterFast (t m : Nat) (hm : m < 2 ^ 256) :
    biterFastBare t m = biterFast t m := by
  unfold biterFastBare biterFast
  by_cases h2 : t = 2
  · simp [h2, bstepBare_eq, bstep_lt256, hm]
  · by_cases h4 : t = 4
    · simp [h2, h4, bstepBare_eq, bstep_lt256, hm]
    · by_cases h8 : t = 8
      · simp [h2, h4, h8, bstepBare_eq, bstep_lt256, hm]
      · simp [h2, h4, h8]

theorem fastInit_lt256 (seed : Nat) :
    WideFast.fastInit seed < 2 ^ 256 := by
  dsimp [WideFast.fastInit]
  have hp :
      WideFast.fastPayload (seed + WideFast.initBias3) ≤
        WideFast.payloadMask254 := by
    unfold WideFast.fastPayload
    exact Nat.and_le_right
  rw [WideFast.payloadMask254_eq] at hp
  have hmul := Nat.mul_le_mul_left 4 hp
  have hclosed : 1 + 4 * (2 ^ 254 - 1) < 2 ^ 256 := by decide
  exact Nat.lt_of_le_of_lt (Nat.add_le_add_left hmul 1) hclosed

def impl : Nat → Nat := fun n =>
  biterFastBare (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n

end Submission
'''

if old not in base:
    raise SystemExit("final Submission block not found")
out = base.replace(old, new, 1)
path = ROOT / "generated" / "Submission_v58.lean"
path.write_text(out)
print(f"generated {path} bytes={len(out)}")
