import Collatz.GuardedDyadicSwitch

namespace CollatzFinal
namespace SourceProduct

/-- Prefix-depth plus local dyadic defect order: the exact integer form of the
pulled-centre source precision used by V60. -/
def pulledPrecision (prefixDepth defectOrder : Nat) : Nat :=
  prefixDepth + defectOrder

/-- Reusing one affine centre consumes exactly D units of local dyadic reserve.

The fixed-centre transport identity gives
  2^D * Δ(m') = A * Δ(m).
For odd A and nonzero Δ(m), exact divisibility therefore lowers the defect
order from v to v-D. -/
theorem same_centre_return_defect_drop
    {A B P m m' : Int} {D v : Nat}
    (hP : P = (2 : Int) ^ D)
    (hA : A % 2 = 1)
    (hstep : P * m' = A * m + B)
    (hdef : DyadicOrder (returnDefect A B P m) v) :
    D ≤ v ∧
      DyadicOrder (returnDefect A B P m') (v - D) := by
  have ht :
      (2 : Int) ^ D * returnDefect A B P m' =
        A * returnDefect A B P m := by
    rw [← hP]
    exact returnDefect_self_scale A B P m m' hstep
  exact dyadic_switch_zero_injection hdef hA ht

/-- Consequently the pulled precision is conserved across a same-centre
return: prefix depth gains D exactly while local reserve loses D. -/
theorem same_centre_preserves_pulled_precision
    {A B P m m' : Int} {H D v : Nat}
    (hP : P = (2 : Int) ^ D)
    (hA : A % 2 = 1)
    (hstep : P * m' = A * m + B)
    (hdef : DyadicOrder (returnDefect A B P m) v) :
    pulledPrecision (H + D) (v - D) = pulledPrecision H v := by
  have hd := (same_centre_return_defect_drop hP hA hstep hdef).1
  unfold pulledPrecision
  omega

/-- Every positive-depth same-centre nonzero-defect return strictly consumes
the local reserve. -/
theorem same_centre_strict_reserve_drop
    {A B P m m' : Int} {D v : Nat}
    (hD : 0 < D)
    (hP : P = (2 : Int) ^ D)
    (hA : A % 2 = 1)
    (hstep : P * m' = A * m + B)
    (hdef : DyadicOrder (returnDefect A B P m) v) :
    v - D < v := by
  have hd := (same_centre_return_defect_drop hP hA hstep hdef).1
  omega

/-- Complete algebraic same-centre classification.

At positive return depth, there are only two cases:
  * zero defect: the return is an exact fixed point;
  * nonzero defect: an exact dyadic reserve exists and strictly decreases,
    while pulled precision is conserved.

This discharges the same-centre branch once a source-admitted affine return
event has been produced. -/
theorem same_centre_return_classification
    {A B P m m' : Int} {D H : Nat}
    (hD : 0 < D)
    (hP : P = (2 : Int) ^ D)
    (hA : A % 2 = 1)
    (hPne : P ≠ 0)
    (hstep : P * m' = A * m + B) :
    (returnDefect A B P m = 0 ∧ m' = m) ∨
      ∃ v,
        DyadicOrder (returnDefect A B P m) v ∧
        DyadicOrder (returnDefect A B P m') (v - D) ∧
        v - D < v ∧
        pulledPrecision (H + D) (v - D) = pulledPrecision H v := by
  rcases dyadic_input_cases (returnDefect A B P m) with hz | ⟨v, hv⟩
  · exact Or.inl ⟨hz, return_zero_defect_fixed_point A B P m m' hPne hstep hz⟩
  · refine Or.inr ⟨v, hv, ?_, ?_, ?_⟩
    · exact (same_centre_return_defect_drop hP hA hstep hv).2
    · exact same_centre_strict_reserve_drop hD hP hA hstep hv
    · exact same_centre_preserves_pulled_precision hP hA hstep hv

#print axioms same_centre_return_defect_drop
#print axioms same_centre_preserves_pulled_precision
#print axioms same_centre_strict_reserve_drop
#print axioms same_centre_return_classification

end SourceProduct
end CollatzFinal
