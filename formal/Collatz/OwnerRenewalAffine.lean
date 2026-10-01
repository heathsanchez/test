import Collatz.ValuationPullback

namespace Collatz

/-!
# Source-relative affine accounting for coalescent owner returns

`P * p = A * x + C` records an exact source-changing return from a protected
source `x` to a coalescent owner `p`. These lemmas are deliberately generic:
the executable qualifier supplies the Collatz-specific renewal words, while
Lean checks the composition and descent margins at every depth.
-/

theorem coalescentAffine_compose
    (P₁ A₁ C₁ P₂ A₂ C₂ x p q : ℤ)
    (h₁ : P₁ * p = A₁ * x + C₁)
    (h₂ : P₂ * q = A₂ * p + C₂) :
    (P₁ * P₂) * q = (A₂ * A₁) * x + (A₂ * C₁ + P₁ * C₂) := by
  calc
    (P₁ * P₂) * q = P₁ * (P₂ * q) := by ring
    _ = P₁ * (A₂ * p + C₂) := by rw [h₂]
    _ = A₂ * (P₁ * p) + P₁ * C₂ := by ring
    _ = A₂ * (A₁ * x + C₁) + P₁ * C₂ := by rw [h₁]
    _ = (A₂ * A₁) * x + (A₂ * C₁ + P₁ * C₂) := by ring

theorem coalescentAffine_lower_margin
    (P A C x p : ℤ)
    (h : P * p = A * x + C) :
    (P - A) * x - C = P * (x - p) := by
  calc
    (P - A) * x - C = P * x - (A * x + C) := by ring
    _ = P * x - P * p := by rw [← h]
    _ = P * (x - p) := by ring

theorem coalescentAffine_threeQuarter_margin
    (P A C x p : ℤ)
    (h : P * p = A * x + C) :
    (3 * P - 4 * A) * x - 4 * C = P * (3 * x - 4 * p) := by
  calc
    (3 * P - 4 * A) * x - 4 * C = 3 * P * x - 4 * (A * x + C) := by ring
    _ = 3 * P * x - 4 * (P * p) := by rw [← h]
    _ = P * (3 * x - 4 * p) := by ring

theorem coalescentAffine_lower_iff
    (P A C x p : ℤ)
    (hP : 0 < P)
    (h : P * p = A * x + C) :
    p < x ↔ C < (P - A) * x := by
  rw [show C < (P - A) * x ↔ 0 < (P - A) * x - C by omega]
  rw [coalescentAffine_lower_margin P A C x p h]
  exact (Int.mul_pos_iff_of_pos_left hP).symm

theorem coalescentAffine_threeQuarter_iff
    (P A C x p : ℤ)
    (hP : 0 < P)
    (h : P * p = A * x + C) :
    4 * p ≤ 3 * x ↔ 4 * C ≤ (3 * P - 4 * A) * x := by
  rw [show 4 * p ≤ 3 * x ↔ 0 ≤ 3 * x - 4 * p by omega]
  rw [show 4 * C ≤ (3 * P - 4 * A) * x ↔
      0 ≤ (3 * P - 4 * A) * x - 4 * C by omega]
  rw [coalescentAffine_threeQuarter_margin P A C x p h]
  exact (Int.mul_nonneg_iff_of_pos_left hP).symm

#print axioms coalescentAffine_compose
#print axioms coalescentAffine_lower_iff
#print axioms coalescentAffine_threeQuarter_iff

end Collatz
