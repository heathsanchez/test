import Collatz.SourceProductAffine

namespace CollatzFinal
namespace OriginPhaseBarrier

/-- Count a cyclic interval of width W, starting at a. Duplicates are counted;
    the obstruction therefore applies to lists and, in particular, sets. -/
def windowCount (N W a : Nat) : List Nat → Nat
  | [] => 0
  | r :: rs => (if (r + N - a) % N < W then 1 else 0) + windowCount N W a rs

theorem count_positive_of_member {N W a r : Nat} {rs : List Nat}
    (hr : r ∈ rs) (hw : (r + N - a) % N < W) :
    0 < windowCount N W a rs := by
  induction rs with
  | nil => simp at hr
  | cons s ss ih =>
      simp only [List.mem_cons] at hr
      rcases hr with he | ht
      · subst s
        simp only [windowCount, hw, ite_true]
        omega
      · have hp := ih ht
        simp only [windowCount]
        split <;> omega

theorem support_point_has_nonempty_window {N W r : Nat} {rs : List Nat}
    (hr : r ∈ rs) (hW : 0 < W) :
    0 < windowCount N W r rs := by
  apply count_positive_of_member hr
  have he : r + N - r = N := by omega
  simpa only [he, Nat.mod_self] using hW

/-- Any bound valid at every translated window must permit at least one atom.
    The rational envelope is P/Q; no real-analysis or numerical oracle is used. -/
theorem uniform_envelope_not_subunit {N W P Q r : Nat} {rs : List Nat}
    (hr : r ∈ rs) (hrN : r < N) (hW : 0 < W)
    (hupper : ∀ a, a < N → Q * windowCount N W a rs ≤ P) :
    Q ≤ P := by
  have hp := support_point_has_nonempty_window (N := N) hr hW
  have hone : 1 ≤ windowCount N W r rs := by omega
  have hscale := Nat.mul_le_mul_left Q hone
  have hu := hupper r hrN
  simpa only [Nat.mul_one] using Nat.le_trans hscale hu

theorem no_translation_uniform_subunit_bound {N W P Q r : Nat} {rs : List Nat}
    (hr : r ∈ rs) (hrN : r < N) (hW : 0 < W) (hsub : P < Q) :
    ¬ (∀ a, a < N → Q * windowCount N W a rs ≤ P) := by
  intro hu
  have h := uniform_envelope_not_subunit hr hrN hW hu
  omega

end OriginPhaseBarrier
namespace SourceProduct

private theorem two_pow_positive (k : Nat) : 0 < 2 ^ k := by
  induction k with
  | zero => decide
  | succ k ih => simpa only [Nat.pow_succ] using Nat.mul_pos ih (by decide : 0 < 2)

/-- Exact front step of an arbitrary-length all-odd cylinder. -/
theorem shortcut_odd_block (k a : Nat) (ha : 0 < a) :
    shortcut (2 ^ (k + 1) * a - 1) = 2 ^ k * (3 * a) - 1 := by
  have hb : 0 < 2 ^ k * a := Nat.mul_pos (two_pow_positive k) ha
  have he : 2 ^ (k + 1) * a = 2 * (2 ^ k * a) := by
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have ht : 2 ^ k * (3 * a) = 3 * (2 ^ k * a) := by
    simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  rw [he, ht]
  have ho : ¬ (2 * (2 ^ k * a) - 1) % 2 = 0 := by omega
  simp only [shortcut, ho, ite_false]
  omega

theorem iter_odd_block (k a : Nat) (ha : 0 < a) :
    iter shortcut k (2 ^ k * a - 1) = 3 ^ k * a - 1 := by
  induction k generalizing a with
  | zero => simp [iter]
  | succ k ih =>
      rw [iter, shortcut_odd_block k a ha]
      rw [ih (3 * a) (by omega)]
      simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem all_ones_prefix_value (j k : Nat) (hk : k ≤ j) :
    iter shortcut k (2 ^ j - 1) = 3 ^ k * 2 ^ (j - k) - 1 := by
  have hj : k + (j - k) = j := by omega
  have he : 2 ^ j = 2 ^ k * 2 ^ (j - k) := by
    rw [← Nat.pow_add, hj]
  rw [he]
  exact iter_odd_block k (2 ^ (j - k)) (two_pow_positive (j - k))

theorem all_ones_prefix_odd (j k : Nat) (hk : k < j) :
    iter shortcut k (2 ^ j - 1) % 2 = 1 := by
  rw [all_ones_prefix_value j k (by omega)]
  have he : j - k = (j - k - 1) + 1 := by omega
  rw [he, Nat.pow_succ]
  have hp : 0 < 3 ^ k * 2 ^ (j - k - 1) := by
    apply Nat.mul_pos
    · exact Nat.pow_pos (by decide : 0 < 3)
    · exact two_pow_positive _
  have ht : 3 ^ k * (2 ^ (j - k - 1) * 2) =
      2 * (3 ^ k * 2 ^ (j - k - 1)) := by
    simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  rw [ht]
  omega

theorem all_ones_odd_count (j k : Nat) (hk : k ≤ j) :
    oddCount (2 ^ j - 1) k = k := by
  induction k with
  | zero => rfl
  | succ k ih =>
      have ho := all_ones_prefix_odd j k (by omega)
      have hn : ¬ iter shortcut k (2 ^ j - 1) % 2 = 0 := by omega
      simp only [oddCount, hn, ite_false]
      rw [ih (by omega)]

/-- Every positive depth has an actual positive all-odd source cylinder.
    This is a different source at each depth, not a never-crossing positive orbit. -/
theorem all_ones_no_coefficient_crossing (j k : Nat) (hk : k ≤ j) :
    2 ^ k ≤ 3 ^ oddCount (2 ^ j - 1) k := by
  rw [all_ones_odd_count j k hk]
  induction k with
  | zero => decide
  | succ k ih =>
      have hi := ih (by omega)
      simp only [Nat.pow_succ]
      have hm := Nat.mul_le_mul_right 2 hi
      omega

end SourceProduct

#print axioms OriginPhaseBarrier.uniform_envelope_not_subunit
#print axioms OriginPhaseBarrier.no_translation_uniform_subunit_bound
#print axioms SourceProduct.iter_odd_block
#print axioms SourceProduct.all_ones_no_coefficient_crossing

end CollatzFinal
