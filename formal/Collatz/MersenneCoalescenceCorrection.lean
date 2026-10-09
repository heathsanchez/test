import Collatz.ThreeCongruenceMerger
import Collatz.OrdinaryExitReduction

namespace CollatzFinal
namespace SourceProduct
namespace MersenneCorrection

set_option exponentiation.threshold 512

/- Exact separation of two bounded observations: absence of a capped
   ternary hit is NOT absence of an already certified earlier-source merger.
   This module does not assert universal Collatz termination. -/

def exponent (t : Nat) : Nat := 20 + 486 * t
def source (t : Nat) : Nat := 2 ^ exponent t - 1
def parameter (t : Nat) : Nat := source t / 1458
def predecessor (t : Nat) : Nat := 191 + 1024 * parameter t

theorem power_residue (t : Nat) :
    2 ^ (20 + 486 * t) % 1458 = 274 := by
  induction t with
  | zero => decide
  | succ t ih =>
      have he : 20 + 486 * (t + 1) = (20 + 486 * t) + 486 := by omega
      rw [he, Nat.pow_add, Nat.mul_mod, ih]
      decide

theorem source_residue (t : Nat) : source t % 1458 = 273 := by
  have hd := Nat.mod_add_div (2 ^ (20 + 486 * t)) 1458
  rw [power_residue t] at hd
  have hs : 2 ^ (20 + 486 * t) - 1 =
      273 + 1458 * (2 ^ (20 + 486 * t) / 1458) := by omega
  unfold source exponent
  rw [hs]
  simp [Nat.add_mod, Nat.mul_mod]

theorem source_decomposition (t : Nat) :
    source t = 273 + 1458 * parameter t := by
  have h := Nat.mod_add_div (source t) 1458
  rw [source_residue] at h
  exact h.symm

theorem source_gt_one (t : Nat) : 1 < source t := by
  have h := source_decomposition t
  omega

theorem predecessor_positive (t : Nat) : 0 < predecessor t := by
  unfold predecessor
  omega

theorem predecessor_lt_source (t : Nat) : predecessor t < source t := by
  rw [source_decomposition]
  unfold predecessor
  omega

/-- This is reuse of the existing V113 universal merger constructor. -/
theorem source_lower_merge (t : Nat) :
    LowerMerge shortcut (source t) (predecessor t) := by
  rw [source_decomposition]
  exact v113_a_source_merge (parameter t)

/-- Keep the explicit meeting clocks, not only existential coalescence. -/
theorem family_meeting_clocks (q : Nat) :
    iter shortcut 1 (273 + 1458 * q) =
      iter shortcut 10 (191 + 1024 * q) := by
  have hr := affine_reverse_sound v113_a_reverse_word q
  have ho : (273 + 1458 * q) % 2 ≠ 0 := by omega
  have hf : shortcut (273 + 1458 * q) = 410 + 2187 * q := by
    simp only [shortcut, ho, ite_false]
    omega
  change shortcut (273 + 1458 * q) = _
  rw [hf, hr]

theorem source_meeting_clocks (t : Nat) :
    iter shortcut 1 (source t) = iter shortcut 10 (predecessor t) := by
  rw [source_decomposition]
  exact family_meeting_clocks (parameter t)

/-- Every later endpoint is already on the same earlier positive orbit. -/
theorem persistent_clock (t j : Nat) :
    iter shortcut (1 + j) (source t) =
      iter shortcut (10 + j) (predecessor t) := by
  rw [iter_add, iter_add, source_meeting_clocks]

theorem persistent_ordinary_exit (t j : Nat) :
    OrdinaryExit (source t) (iter shortcut (1 + j) (source t)) := by
  exact Or.inr (Or.inr
    ⟨predecessor t, 10 + j, predecessor_positive t,
      predecessor_lt_source t, (persistent_clock t j).symm⟩)

theorem not_live_after_first_step (t j : Nat) :
    ¬ Live (stateAt (source t) (1 + j)) := by
  intro h
  apply h.2
  exact (exit_stateAt_iff_ordinary (source t) (1 + j)).mpr
    (persistent_ordinary_exit t j)

theorem not_minimal_bad (t : Nat) :
    ¬ MinimalBad PositiveBad (source t) := by
  intro h
  exact positive_minimal_no_lower_merge h (predecessor t)
    (predecessor_positive t) (source_lower_merge t)

theorem shortcut_two_mul_sub_one (z : Nat) (hz : 0 < z) :
    shortcut (2 * z - 1) = 3 * z - 1 := by
  have ho : (2 * z - 1) % 2 ≠ 0 := by omega
  simp only [shortcut, ho, ite_false]
  omega

theorem corridor_step (j m : Nat) :
    shortcut (3 ^ j * 2 ^ (m + 1) - 1) =
      3 ^ (j + 1) * 2 ^ m - 1 := by
  have hp : 0 < 3 ^ j * 2 ^ m :=
    Nat.mul_pos (Nat.pow_pos (by decide)) (Nat.pow_pos (by decide))
  simpa [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using
    shortcut_two_mul_sub_one (3 ^ j * 2 ^ m) hp

theorem all_ones_prefix (j m : Nat) :
    iter shortcut j (2 ^ (j + m) - 1) = 3 ^ j * 2 ^ m - 1 := by
  induction j generalizing m with
  | zero => simp [iter]
  | succ j ih =>
      have he : j + 1 + m = j + (m + 1) := by omega
      rw [iter_succ_last, he, ih, corridor_step]

/-- Positive-time endpoints in this corridor are all above the fixed cap. -/
theorem corridor_above_cap (i m : Nat) :
    3 * (2 ^ ((i + 1) + m) - 1) ≤
      2 * iter shortcut (i + 1) (2 ^ ((i + 1) + m) - 1) - 1 := by
  rw [all_ones_prefix]
  have hpow : (2 : Nat) ^ i ≤ 3 ^ i := Nat.pow_le_pow_left (by decide : (2 : Nat) ≤ 3) i
  have hmul := Nat.mul_le_mul_right (2 ^ m) hpow
  have he : 2 ^ ((i + 1) + m) = 2 * (2 ^ i * 2 ^ m) := by
    simp [Nat.pow_add, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hy : 3 ^ (i + 1) * 2 ^ m = 3 * (3 ^ i * 2 ^ m) := by
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  rw [he, hy]
  omega

theorem no_capped_hit_in_corridor (t j : Nat) (hj : j ≤ exponent t) :
    ¬ ((iter shortcut j (source t)) % 3 = 2 ∧
      2 * iter shortcut j (source t) - 1 < 3 * source t) := by
  intro h
  cases j with
  | zero =>
      have hd := source_decomposition t
      have hm : source t % 3 = 2 := h.1
      omega
  | succ i =>
      have he : exponent t = (i + 1) + (exponent t - (i + 1)) := by omega
      have hb := corridor_above_cap i (exponent t - (i + 1))
      have hn : source t = 2 ^ ((i + 1) + (exponent t - (i + 1))) - 1 := by
        exact congrArg (fun k : Nat => 2 ^ k - 1) he
      rw [← hn] at hb
      exact Nat.not_lt_of_ge hb h.2

/-- For ANY requested finite delay there is a source with no capped
hit during that delay, while EVERY endpoint after its first step has
already acquired a genuine ordinary earlier-source exit. -/
theorem arbitrary_delay_with_certified_exit (L : Nat) :
    ∃ n K : Nat, 1 < n ∧ L ≤ K ∧
      (∀ j, j ≤ K → ¬ ((iter shortcut j n) % 3 = 2 ∧
        2 * iter shortcut j n - 1 < 3 * n)) ∧
      (∀ j, OrdinaryExit n (iter shortcut (1 + j) n)) := by
  refine ⟨source L, exponent L, source_gt_one L, ?_,
    no_capped_hit_in_corridor L, persistent_ordinary_exit L⟩
  unfold exponent
  omega

#print axioms power_residue
#print axioms source_lower_merge
#print axioms source_meeting_clocks
#print axioms persistent_ordinary_exit
#print axioms not_live_after_first_step
#print axioms not_minimal_bad
#print axioms no_capped_hit_in_corridor
#print axioms arbitrary_delay_with_certified_exit

end MersenneCorrection
end SourceProduct
end CollatzFinal
