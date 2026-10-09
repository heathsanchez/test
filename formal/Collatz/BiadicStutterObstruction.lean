import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- Exact actual shortcut step inside the long all-ones corridor.
    This is not a claim of termination or a source-capped return. -/
theorem v116_shortcut_two_mul_sub_one (z : Nat) (hz : 0 < z) :
    shortcut (2 * z - 1) = 3 * z - 1 := by
  have hodd : (2 * z - 1) % 2 = 1 := by omega
  simp [shortcut, hodd]
  omega

/-- Each odd all-ones-corridor step trades one factor 2 for one factor 3. -/
theorem v116_corridor_step (j m : Nat) :
    shortcut (3 ^ j * 2 ^ (m + 1) - 1) =
      3 ^ (j + 1) * 2 ^ m - 1 := by
  have hz : 0 < 3 ^ j * 2 ^ m := by positivity
  have hr : 3 ^ j * 2 ^ (m + 1) = 2 * (3 ^ j * 2 ^ m) := by
    simp [pow_succ]
    ring
  calc
    shortcut (3 ^ j * 2 ^ (m + 1) - 1) =
        shortcut (2 * (3 ^ j * 2 ^ m) - 1) := by rw [hr]
    _ = 3 * (3 ^ j * 2 ^ m) - 1 := v116_shortcut_two_mul_sub_one _ hz
    _ = 3 ^ (j + 1) * 2 ^ m - 1 := by
      congr 1
      simp [pow_succ]
      ring

/-- For every j,m, an actual positive source 2^(j+m)-1 follows exactly
    the parametric all-ones corridor for its first j shortcut steps. -/
theorem v116_all_ones_actual_prefix (j m : Nat) :
    iter shortcut j (2 ^ (j + m) - 1) =
      3 ^ j * 2 ^ m - 1 := by
  induction j generalizing m with
  | zero =>
      simp [iter]
  | succ j ih =>
      have hsum : j + 1 + m = j + (m + 1) := by omega
      calc
        iter shortcut (j + 1) (2 ^ (j + 1 + m) - 1) =
            shortcut (iter shortcut j (2 ^ (j + (m + 1)) - 1)) := by
              rw [hsum, iter_succ_last]
        _ = shortcut (3 ^ j * 2 ^ (m + 1) - 1) := by
              rw [ih (m + 1)]
        _ = 3 ^ (j + 1) * 2 ^ m - 1 := v116_corridor_step j m

#print axioms v116_shortcut_two_mul_sub_one
#print axioms v116_corridor_step
#print axioms v116_all_ones_actual_prefix

end SourceProduct
end CollatzFinal
