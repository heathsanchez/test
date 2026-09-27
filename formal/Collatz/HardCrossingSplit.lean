import Collatz.HardCrossingFuture

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

/-- The large-source signature is equivalently the single endpoint congruence
y ≡ 7 (mod 24). -/
theorem large_source_signature_mod24
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hlarge : oddCount n (k + 1) < n) :
    iter shortcut (k + 1) n % 24 = 7 := by
  have hs := minimal_bad_hard_crossing_large_source_signature
    hmin hfirst hlarge
  dsimp at hs
  rcases hs with ⟨h3, h2, hnext2⟩
  have hodd : iter shortcut (k + 1) n % 2 ≠ 0 := by
    omega
  have hnextmod :
      ((3 * iter shortcut (k + 1) n + 1) / 2) % 2 = 1 := by
    unfold shortcut at hnext2
    rw [if_neg hodd] at hnext2
    exact hnext2
  have hmod24 := Nat.mod_lt (iter shortcut (k + 1) n) (by omega : 0 < 24)
  omega

/-- Exact hard-first-crossing split for a hypothetical minimal bad source.
Either the source itself lies in the linear origin window n≤depth, or the
first-crossing endpoint lies in the rigid reverse-tree residue 7 mod 24. -/
theorem minimal_bad_first_crossing_origin_or_mod24
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    n ≤ k + 1 ∨ iter shortcut (k + 1) n % 24 = 7 := by
  by_cases hsmall : n ≤ oddCount n (k + 1)
  · left
    exact Nat.le_trans hsmall (oddCount_le_depth n (k + 1))
  · right
    have hlarge : oddCount n (k + 1) < n := by omega
    exact large_source_signature_mod24 hmin hfirst hlarge

/-- Sharper version retaining the consequential split variable q itself. -/
theorem minimal_bad_first_crossing_origin_or_large_signature
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    n ≤ oddCount n (k + 1) ∨
      (oddCount n (k + 1) < n ∧
       iter shortcut (k + 1) n % 24 = 7) := by
  by_cases hsmall : n ≤ oddCount n (k + 1)
  · exact Or.inl hsmall
  · have hlarge : oddCount n (k + 1) < n := by omega
    exact Or.inr ⟨hlarge,
      large_source_signature_mod24 hmin hfirst hlarge⟩

#print axioms oddCount_le_depth
#print axioms large_source_signature_mod24
#print axioms minimal_bad_first_crossing_origin_or_mod24
#print axioms minimal_bad_first_crossing_origin_or_large_signature

end SourceProduct
end CollatzFinal
