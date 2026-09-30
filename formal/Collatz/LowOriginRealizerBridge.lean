import Collatz.SourceProductZeroTail
import Collatz.DoubleDepthCorridor
import Collatz.CoefficientDynamics

namespace CollatzFinal
namespace SourceProduct

/-- If the fixed source is already below 2^K and the source-product depth has
reached K, no nonzero source tail can remain. This is the universal source-freeze
lemma used by the V55 ordinary-to-accelerated adapter. -/
theorem tail_eq_zero_of_source_lt_pow
    {s : State} {K : Nat}
    (hs : Valid s)
    (hK : K ≤ s.depth)
    (hsrc : s.source < 2 ^ K) :
    s.tail = 0 := by
  by_contra htail
  have ht1 : 1 ≤ s.tail := by omega
  have hpow : 2 ^ K ≤ 2 ^ s.depth :=
    Nat.pow_le_pow_right (by decide : 0 < 2) hK
  have hmul : 2 ^ s.depth ≤ 2 ^ s.depth * s.tail := by
    have h := Nat.mul_le_mul_left (2 ^ s.depth) ht1
    simpa using h
  have hdecomp := hs.2.2.2
  have hdepth_source : 2 ^ s.depth ≤ s.source := by
    omega
  omega

/-- Consequently the canonical source residue has frozen to the actual source. -/
theorem sourceResidue_eq_source_of_source_lt_pow
    {s : State} {K : Nat}
    (hs : Valid s)
    (hK : K ≤ s.depth)
    (hsrc : s.source < 2 ^ K) :
    s.sourceResidue = s.source := by
  exact zero_tail_source_residue hs
    (tail_eq_zero_of_source_lt_pow hs hK hsrc)

/-- Along an actual source path, once depth K is reached beyond the bit length
of the source, tail zero and source-residue identity persist. -/
theorem stateAt_source_freeze
    {n j K : Nat}
    (hn : 0 < n)
    (hK : K ≤ j)
    (hsrc : n < 2 ^ K) :
    (stateAt n j).tail = 0 ∧
      (stateAt n j).sourceResidue = n := by
  have hv : Valid (stateAt n j) := at_valid hn j
  have hd : (stateAt n j).depth = j := at_depth n j
  have hs : (stateAt n j).source = n := at_source n j
  have hz : (stateAt n j).tail = 0 := by
    apply tail_eq_zero_of_source_lt_pow hv
    · simpa [hd] using hK
    · simpa [hs] using hsrc
  refine ⟨hz, ?_⟩
  simpa [hs] using zero_tail_source_residue hv hz

/-- If every orbit position strictly after K and before j is even, the number
of odd shortcut steps through depth j is at most K+1. -/
theorem oddCount_le_succ_of_even_after
    {n j K : Nat}
    (heven :
      ∀ p, K < p → p < j → iter shortcut p n % 2 = 0) :
    oddCount n j ≤ K + 1 := by
  induction j with
  | zero =>
      simp [oddCount]
  | succ j ih =>
      by_cases hjK : j ≤ K
      · exact le_trans (oddCount_le_depth n (j + 1)) (by omega)
      · have hjodd : iter shortcut j n % 2 = 0 :=
          heven j (by omega) (by omega)
        simp only [oddCount, hjodd, ite_true]
        apply ih
        intro p hpK hpj
        exact heven p hpK (by omega)

/-- More than K+1 odd steps force an odd orbit state strictly after depth K.
This is the combinatorial last-odd-boundary existence used by V55. -/
theorem exists_odd_after_of_succ_lt_oddCount
    {n j K : Nat}
    (hq : K + 1 < oddCount n j) :
    ∃ p, K < p ∧ p < j ∧ iter shortcut p n % 2 = 1 := by
  by_contra hnone
  have heven :
      ∀ p, K < p → p < j → iter shortcut p n % 2 = 0 := by
    intro p hpK hpj
    have hmodlt : iter shortcut p n % 2 < 2 :=
      Nat.mod_lt _ (by decide)
    by_cases hodd : iter shortcut p n % 2 = 1
    · exact False.elim (hnone ⟨p, hpK, hpj, hodd⟩)
    · omega
  have hb := oddCount_le_succ_of_even_after heven
  omega

/-- Coefficient survival at depth j plus qmin(j) > K+1 therefore forces a
completed odd boundary beyond K. This is the source-product side of the V55
realizer adapter. -/
theorem exists_odd_after_of_coefficient_survival
    {n j K : Nat}
    (hsurv : qmin j ≤ oddCount n j)
    (hK : K + 1 < qmin j) :
    ∃ p, K < p ∧ p < j ∧ iter shortcut p n % 2 = 1 := by
  apply exists_odd_after_of_succ_lt_oddCount
  omega

#print axioms tail_eq_zero_of_source_lt_pow
#print axioms sourceResidue_eq_source_of_source_lt_pow
#print axioms stateAt_source_freeze
#print axioms oddCount_le_succ_of_even_after
#print axioms exists_odd_after_of_succ_lt_oddCount
#print axioms exists_odd_after_of_coefficient_survival

end SourceProduct
end CollatzFinal
