import GenericPackProof

namespace GatherPair

open GenericPack

def lowMask (g : Nat) : Nat := 2 ^ (2 * g) - 1

theorem testBit_lowMask (g i : Nat) :
    (lowMask g).testBit i = decide (i < 2 * g) := by
  unfold lowMask
  rw [Nat.testBit_two_pow_sub_one]

def gatherPair (g p q : Nat) : Nat :=
  orStage (lowMask g) (64 * g - g) (packW (64 * g) p q)

theorem gatherPair_eq
    (g p q : Nat)
    (hg : 0 < g)
    (hp : p < 2 ^ g)
    (hq : q < 2 ^ g) :
    gatherPair g p q = packW g p q := by
  have hp64 : p < 2 ^ (64 * g) := by
    exact Nat.lt_of_lt_of_le hp
      (Nat.pow_le_pow_right (by omega) (by omega))
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW g p q i hp]
  unfold gatherPair orStage
  rw [Nat.testBit_and, testBit_lowMask]
  simp only [Nat.testBit_or, Nat.testBit_shiftRight]
  by_cases h2 : i < 2 * g
  · simp only [h2, decide_true, Bool.and_true]
    by_cases h1 : i < g
    · rw [if_pos h1]
      have hi64 : i < 64 * g := by omega
      have hs64 : 64 * g - g + i < 64 * g := by omega
      rw [testBit_packW (64 * g) p q i hp64]
      rw [testBit_packW (64 * g) p q (64 * g - g + i) hp64]
      have hsrcHigh : g ≤ 64 * g - g + i := by omega
      have hfalse := bit_false_above_pow hp hsrcHigh
      simp [hi64, hs64, hfalse]
    · have hgi : g ≤ i := by omega
      rw [if_neg h1]
      have hi64 : i < 64 * g := by omega
      have hsHigh : 64 * g ≤ 64 * g - g + i := by omega
      have hsNot : ¬ (64 * g - g + i < 64 * g) := by omega
      have hsub : (64 * g - g + i) - 64 * g = i - g := by omega
      rw [testBit_packW (64 * g) p q i hp64]
      rw [testBit_packW (64 * g) p q (64 * g - g + i) hp64]
      have hpi : p.testBit i = false := bit_false_above_pow hp hgi
      simp [hi64, hsNot, hsub, hpi]
  · have h2f : decide (i < 2 * g) = false := by simp [h2]
    rw [h2f, Bool.and_false]
    by_cases h1 : i < g
    · omega
    · rw [if_neg h1]
      have hiq : g ≤ i - g := by omega
      have hqf := bit_false_above_pow hq hiq
      exact hqf.symm

end GatherPair
