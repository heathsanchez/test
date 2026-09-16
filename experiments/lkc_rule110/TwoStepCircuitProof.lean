import Submission

namespace TwoStepCircuit

open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

def rotL1 (m : Nat) : Nat :=
  (((m <<< 1) ||| (m >>> 255)) &&& M)

def rotR1 (m : Nat) : Nat :=
  (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)

def rotL2 (m : Nat) : Nat :=
  (((m <<< 2) ||| (m >>> 254)) &&& M)

def rotR2 (m : Nat) : Nat :=
  (((m >>> 2) ||| ((m &&& 3) <<< 254)) &&& M)

theorem rotL1_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotL1 m).testBit i = m.testBit ((i + 255) % 256) := by
  simpa [rotL1] using (testBit_rotL hm hi)

theorem rotR1_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotR1 m).testBit i = m.testBit ((i + 1) % 256) := by
  simpa [rotR1] using (testBit_rotR hm hi)

theorem rotL2_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotL2 m).testBit i = m.testBit ((i + 254) % 256) := by
  unfold rotL2
  rw [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftLeft,
      Nat.testBit_shiftRight, testBit_M]
  simp only [hi, decide_true, Bool.and_true]
  by_cases h0 : i = 0
  · subst i
    simp
  · by_cases h1 : i = 1
    · subst i
      simp
    · have hi2 : 2 ≤ i := by omega
      have hmod : (i + 254) % 256 = i - 2 := by omega
      have hhigh : m.testBit (254 + i) = false :=
        testBit_high hm (by omega)
      simp [hi2, hmod, hhigh]

theorem rotR2_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (rotR2 m).testBit i = m.testBit ((i + 2) % 256) := by
  unfold rotR2
  rw [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftRight,
      Nat.testBit_shiftLeft, testBit_M]
  simp only [hi, decide_true, Bool.and_true, Nat.testBit_and]
  by_cases hlo : i < 254
  · have hmod : (i + 2) % 256 = i + 2 := by omega
    have hnot : ¬ 254 ≤ i := by omega
    simpa [hmod, hnot, Nat.add_comm]
  · by_cases h254 : i = 254
    · subst i
      have hh : m.testBit 256 = false := testBit_high hm (by decide)
      simp [hh]
    · have h255 : i = 255 := by omega
      subst i
      have hh : m.testBit 257 = false := testBit_high hm (by decide)
      have h3 : (3 : Nat).testBit 1 = true := by decide
      simp [hh, h3]

theorem bstep_lt (m : Nat) : bstep m < 2 ^ 256 := by
  have hM : M < 2 ^ 256 := by
    rw [M_eq]
    omega
  unfold bstep
  exact Nat.lt_of_le_of_lt Nat.and_le_right hM

theorem bstep_bit {m i : Nat} (hm : m < 2 ^ 256) (hi : i < 256) :
    (bstep m).testBit i =
      rule110 (m.testBit ((i + 255) % 256))
              (m.testBit i)
              (m.testBit ((i + 1) % 256)) := by
  simp only [bstep, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_or,
             testBit_M, testBit_rotL hm hi, testBit_rotR hm hi,
             hi, decide_true, Bool.and_true]
  generalize m.testBit ((i + 255) % 256) = a
  generalize m.testBit i = b
  generalize m.testBit ((i + 1) % 256) = c
  cases a <;> cases b <;> cases c <;> decide

/-- Exact radius-2 circuit for two Rule110 steps.
    Truth function: (d & b) XOR ((c XOR (e OR d)) OR (e & (d OR (b & a)))). -/
def bstep2 (m : Nat) : Nat :=
  let a := rotL2 m
  let b := rotL1 m
  let c := m
  let d := rotR1 m
  let e := rotR2 m
  ((d &&& b) ^^^ ((c ^^^ (e ||| d)) ||| (e &&& (d ||| (b &&& a))))) &&& M

theorem bstep2_lt (m : Nat) : bstep2 m < 2 ^ 256 := by
  have hM : M < 2 ^ 256 := by
    rw [M_eq]
    omega
  unfold bstep2
  exact Nat.lt_of_le_of_lt Nat.and_le_right hM

theorem bstep2_eq (m : Nat) (hm : m < 2 ^ 256) :
    bstep2 m = bstep (bstep m) := by
  apply Nat.eq_of_testBit_eq
  intro i
  by_cases hi : i < 256
  · have hil : (i + 255) % 256 < 256 := Nat.mod_lt _ (by decide)
    have hir : (i + 1) % 256 < 256 := Nat.mod_lt _ (by decide)
    have hll : (((i + 255) % 256) + 255) % 256 = (i + 254) % 256 := by omega
    have hlr : (((i + 255) % 256) + 1) % 256 = i := by omega
    have hrl : (((i + 1) % 256) + 255) % 256 = i := by omega
    have hrr : (((i + 1) % 256) + 1) % 256 = (i + 2) % 256 := by omega
    rw [bstep_bit (bstep_lt m) hi]
    rw [bstep_bit hm hil, bstep_bit hm hi, bstep_bit hm hir]
    rw [hll, hlr, hrl, hrr]
    simp only [bstep2, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_or,
               testBit_M, hi, decide_true, Bool.and_true,
               rotL2_bit hm hi, rotL1_bit hm hi, rotR1_bit hm hi, rotR2_bit hm hi]
    generalize m.testBit ((i + 254) % 256) = a
    generalize m.testBit ((i + 255) % 256) = b
    generalize m.testBit i = c
    generalize m.testBit ((i + 1) % 256) = d
    generalize m.testBit ((i + 2) % 256) = e
    cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> decide
  · unfold bstep2 bstep
    simp [Nat.testBit_and, testBit_M, hi]

end TwoStepCircuit
