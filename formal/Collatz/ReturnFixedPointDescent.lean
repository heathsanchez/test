import Collatz.BiadicRankedNormalization

namespace CollatzFinal
namespace SourceProduct

/-- Generic affine-return descent lemma.

If an exact return satisfies
    P * m' = A * m + B
with A < P, and every live state in the declared domain has m >= L, then the
single certificate
    B < (P - A) * L
places the affine fixed point below that live floor and forces m' < m.

This is the theorem-shaped core of the V45 fixed-point audit.  It deliberately
contains no Collatz-specific completeness assumption: discovering/proving that
a future return satisfies the hypotheses remains a separate obligation. -/
theorem affine_return_strict_descent_of_live_floor
    {A B P L m m' : Nat}
    (hA : A < P)
    (hfloor : L ≤ m)
    (hfixed : B < (P - A) * L)
    (heq : P * m' = A * m + B) :
    m' < m := by
  have hgap : (P - A) * L ≤ (P - A) * m := by
    exact Nat.mul_le_mul_left (P - A) hfloor
  have hB : B < (P - A) * m :=
    Nat.lt_of_lt_of_le hfixed hgap
  have hsum : A * m + B < A * m + (P - A) * m :=
    Nat.add_lt_add_left hB (A * m)
  have hAP : A + (P - A) = P := by
    omega
  have hprod : P * m' < P * m := by
    rw [heq]
    calc
      A * m + B < A * m + (P - A) * m := hsum
      _ = (A + (P - A)) * m := by
        rw [Nat.add_mul]
      _ = P * m := by
        rw [hAP]
  exact Nat.lt_of_mul_lt_mul_left hprod

/-- Shortcut-map specialization, with P = 2^D and A = 3^q.

This is the exact coefficient-contracting / fixed-point-below-live-floor
condition used by V45. -/
theorem collatz_affine_return_strict_descent_of_live_floor
    {q D B L m m' : Nat}
    (hcontract : 3 ^ q < 2 ^ D)
    (hfloor : L ≤ m)
    (hfixed : B < (2 ^ D - 3 ^ q) * L)
    (heq : 2 ^ D * m' = 3 ^ q * m + B) :
    m' < m := by
  exact affine_return_strict_descent_of_live_floor
    hcontract hfloor hfixed heq

#print axioms affine_return_strict_descent_of_live_floor
#print axioms collatz_affine_return_strict_descent_of_live_floor

end SourceProduct
end CollatzFinal
