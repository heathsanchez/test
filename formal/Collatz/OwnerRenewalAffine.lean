import Collatz.ValuationPullback

namespace Collatz

/-!
# Source-relative affine accounting for coalescent owner returns

`P * p = A * x + C` records an exact source-changing return from a protected
source `x` to a coalescent owner `p`. The executable qualifier supplies the
Collatz-specific renewal words; these generic lemmas prove their composition
and descent margins at every depth.
-/

theorem coalescentAffine_compose
    (P₁ A₁ C₁ P₂ A₂ C₂ x p q : Int)
    (h₁ : P₁ * p = A₁ * x + C₁)
    (h₂ : P₂ * q = A₂ * p + C₂) :
    (P₁ * P₂) * q = (A₂ * A₁) * x + (A₂ * C₁ + P₁ * C₂) := by
  calc
    (P₁ * P₂) * q = P₁ * (P₂ * q) := by rw [Int.mul_assoc]
    _ = P₁ * (A₂ * p + C₂) := by rw [h₂]
    _ = A₂ * (P₁ * p) + P₁ * C₂ := by
      simp only [Int.mul_add]
      rw [← Int.mul_assoc, Int.mul_comm P₁ A₂, Int.mul_assoc]
    _ = A₂ * (A₁ * x + C₁) + P₁ * C₂ := by rw [h₁]
    _ = (A₂ * A₁) * x + (A₂ * C₁ + P₁ * C₂) := by
      simp only [Int.mul_add, Int.mul_assoc]
      omega

theorem coalescentAffine_lower_margin
    (P A C x p : Int)
    (h : P * p = A * x + C) :
    (P - A) * x - C = P * (x - p) := by
  simp only [Int.sub_mul, Int.mul_sub]
  omega

theorem coalescentAffine_threeQuarter_margin
    (P A C x p : Int)
    (h : P * p = A * x + C) :
    (3 * P - 4 * A) * x - 4 * C = P * (3 * x - 4 * p) := by
  have h3 : P * (3 * x) = 3 * (P * x) := by
    rw [← Int.mul_assoc, Int.mul_comm P 3, Int.mul_assoc]
  have h4 : P * (4 * p) = 4 * (P * p) := by
    rw [← Int.mul_assoc, Int.mul_comm P 4, Int.mul_assoc]
  calc
    (3 * P - 4 * A) * x - 4 * C =
        3 * (P * x) - 4 * (A * x + C) := by
          simp only [Int.sub_mul, Int.mul_add, Int.mul_assoc]
          omega
    _ = 3 * (P * x) - 4 * (P * p) := by rw [h]
    _ = P * (3 * x - 4 * p) := by
          simp only [Int.mul_sub]
          rw [h3, h4]

theorem coalescentAffine_lower_iff
    (P A C x p : Int)
    (hP : 0 < P)
    (h : P * p = A * x + C) :
    p < x ↔ C < (P - A) * x := by
  have hid := coalescentAffine_lower_margin P A C x p h
  constructor
  · intro hp
    have hprod : 0 < P * (x - p) := Int.mul_pos hP (by omega)
    omega
  · intro hmargin
    by_cases hp : p < x
    · exact hp
    · have hprod : P * (x - p) ≤ 0 :=
        Int.mul_nonpos_of_nonneg_of_nonpos (by omega) (by omega)
      omega

theorem coalescentAffine_threeQuarter_iff
    (P A C x p : Int)
    (hP : 0 < P)
    (h : P * p = A * x + C) :
    4 * p ≤ 3 * x ↔ 4 * C ≤ (3 * P - 4 * A) * x := by
  have hid := coalescentAffine_threeQuarter_margin P A C x p h
  constructor
  · intro hp
    have hprod : 0 ≤ P * (3 * x - 4 * p) :=
      Int.mul_nonneg (by omega) (by omega)
    omega
  · intro hmargin
    by_cases hp : 4 * p ≤ 3 * x
    · exact hp
    · have hprod : P * (3 * x - 4 * p) < 0 :=
        Int.mul_neg_of_pos_of_neg hP (by omega)
      omega

#print axioms coalescentAffine_compose
#print axioms coalescentAffine_lower_iff
#print axioms coalescentAffine_threeQuarter_iff

end Collatz
