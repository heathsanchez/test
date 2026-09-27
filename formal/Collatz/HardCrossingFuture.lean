import Collatz.FirstCrossingGap
import Collatz.StrictDescentReduction

namespace CollatzFinal
namespace SourceProduct

/-- An odd shortcut step always lands in residue 2 modulo 3. -/
theorem shortcut_odd_mod3_two
    {x : Nat}
    (hodd : x % 2 ≠ 0) :
    shortcut x % 3 = 2 := by
  unfold shortcut
  rw [if_neg hodd]
  omega

/-- An even shortcut step cannot create divisibility by 3. -/
theorem shortcut_even_mod3_ne_zero
    {x : Nat}
    (heven : x % 2 = 0)
    (h3 : x % 3 ≠ 0) :
    shortcut x % 3 ≠ 0 := by
  unfold shortcut
  rw [if_pos heven]
  intro hz
  have h2 := Nat.mod_add_div x 2
  have h3q := Nat.mod_add_div (x / 2) 3
  omega

/-- Once an orbit has taken at least one odd step, no later iterate is
divisible by 3. -/
theorem iter_mod3_ne_zero_of_oddCount_pos
    (n : Nat) :
    ∀ d, 0 < oddCount n d →
      iter shortcut d n % 3 ≠ 0 := by
  intro d
  induction d with
  | zero =>
      simp [oddCount]
  | succ d ih =>
      intro hq
      rw [iter_succ_last]
      by_cases he : iter shortcut d n % 2 = 0
      · have hprev : 0 < oddCount n d := by
          simpa [oddCount, he] using hq
        exact shortcut_even_mod3_ne_zero he (ih hprev)
      · have htwo := shortcut_odd_mod3_two he
        omega

/-- On a hypothetical minimal bad orbit, any current value strictly below
twice the source must be odd; an even step would immediately descend. -/
theorem minimal_bad_below_double_forces_odd
    {n d : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hlt : iter shortcut d n < 2 * n) :
    iter shortcut d n % 2 ≠ 0 := by
  intro he
  have hnd := minimal_bad_nondescending_all_depths hmin (d + 1)
  rw [iter_succ_last] at hnd
  unfold shortcut at hnd
  rw [if_pos he] at hnd
  omega

/-- Large-source hard first crossings have a forced residue/future-parity
signature.  The endpoint is 1 mod 3, is odd, and its next iterate is also odd. -/
theorem minimal_bad_hard_crossing_large_source_signature
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hlarge : oddCount n (k + 1) < n) :
    let y := iter shortcut (k + 1) n
    y % 3 = 1 ∧
    y % 2 = 1 ∧
    shortcut y % 2 = 1 := by
  let y := iter shortcut (k + 1) n
  have hn : 0 < n := hmin.1.1
  have hhard : HardFirstCrossing n k :=
    minimal_bad_first_crossing_is_hard hmin hfirst
  have hgap := hard_first_crossing_additive_gap hn hhard
  have hqpos : 0 < oddCount n (k + 1) := by
    omega
  have h3ne : y % 3 ≠ 0 := by
    dsimp [y]
    exact iter_mod3_ne_zero_of_oddCount_pos n (k + 1) hqpos
  have h3ne2 : y % 3 ≠ 2 := by
    dsimp [y]
    exact hard_first_crossing_not_mod3_two_of_q_le_source
      hn hhard (Nat.le_of_lt hlarge)
  have h3 : y % 3 = 1 := by
    have hm := Nat.mod_lt y (by omega : 0 < 3)
    omega
  have hylt : y < 2 * n := by
    have hge := hard_first_crossing_endpoint_ge_source hn hhard
    dsimp [y] at hge hgap
    dsimp [y]
    omega
  have hyoddne : y % 2 ≠ 0 := by
    dsimp [y]
    exact minimal_bad_below_double_forces_odd hmin hylt
  have hyodd : y % 2 = 1 := by
    have hm := Nat.mod_lt y (by omega : 0 < 2)
    omega
  let z := shortcut y
  have hdouble : 2 * z = 3 * y + 1 := by
    dsimp [z]
    have hd := double_shortcut y
    rw [if_neg hyoddne] at hd
    exact hd
  have hzlt : z < 2 * n := by
    dsimp [y] at hgap
    dsimp [z, y]
    omega
  have hzoddne : z % 2 ≠ 0 := by
    have hziter : z = iter shortcut ((k + 1) + 1) n := by
      dsimp [z, y]
      rw [iter_succ_last]
    rw [hziter]
    exact minimal_bad_below_double_forces_odd hmin (by
      simpa [hziter] using hzlt)
  have hzodd : z % 2 = 1 := by
    have hm := Nat.mod_lt z (by omega : 0 < 2)
    omega
  exact ⟨h3, hyodd, by simpa [z] using hzodd⟩

#print axioms shortcut_odd_mod3_two
#print axioms shortcut_even_mod3_ne_zero
#print axioms iter_mod3_ne_zero_of_oddCount_pos
#print axioms minimal_bad_below_double_forces_odd
#print axioms minimal_bad_hard_crossing_large_source_signature

end SourceProduct
end CollatzFinal
