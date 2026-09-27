import Collatz.HardCrossingFuture
import Collatz.ReverseTargetBoundary

namespace CollatzFinal
namespace SourceProduct

/-- Odd count never exceeds elapsed depth. -/
theorem oddCount_le_depth (n : Nat) :
    ∀ d, oddCount n d ≤ d := by
  intro d
  induction d with
  | zero =>
      simp [oddCount]
  | succ d ih =>
      by_cases h : iter shortcut d n % 2 = 0
      · simp [oddCount, h]
        omega
      · simp [oddCount, h]
        omega

/-- The large-source signature is exactly the endpoint congruence
y ≡ 7 (mod 12).  Mod 24 is too strong: both 7 and 19 mod 24 satisfy the
same scalar signature. -/
theorem large_source_signature_mod12
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hlarge : oddCount n (k + 1) < n) :
    iter shortcut (k + 1) n % 12 = 7 := by
  have hs := minimal_bad_hard_crossing_large_source_signature
    hmin hfirst hlarge
  exact (scalar_large_signature_iff_mod12
    (iter shortcut (k + 1) n)).1 hs

/-- Exact hard-first-crossing split for a hypothetical minimal bad source.
Either the source itself lies in the linear origin window n≤depth, or the
first-crossing endpoint lies in the rigid scalar residue 7 mod 12. -/
theorem minimal_bad_first_crossing_origin_or_mod12
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    n ≤ k + 1 ∨ iter shortcut (k + 1) n % 12 = 7 := by
  by_cases hsmall : n ≤ oddCount n (k + 1)
  · left
    exact Nat.le_trans hsmall (oddCount_le_depth n (k + 1))
  · right
    have hlarge : oddCount n (k + 1) < n := by omega
    exact large_source_signature_mod12 hmin hfirst hlarge

/-- Sharper version retaining the consequential split variable q itself. -/
theorem minimal_bad_first_crossing_origin_or_large_signature
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    n ≤ oddCount n (k + 1) ∨
      (oddCount n (k + 1) < n ∧
       iter shortcut (k + 1) n % 12 = 7) := by
  by_cases hsmall : n ≤ oddCount n (k + 1)
  · exact Or.inl hsmall
  · have hlarge : oddCount n (k + 1) < n := by omega
    exact Or.inr ⟨hlarge,
      large_source_signature_mod12 hmin hfirst hlarge⟩

#print axioms oddCount_le_depth
#print axioms large_source_signature_mod12
#print axioms minimal_bad_first_crossing_origin_or_mod12
#print axioms minimal_bad_first_crossing_origin_or_large_signature

end SourceProduct
end CollatzFinal
