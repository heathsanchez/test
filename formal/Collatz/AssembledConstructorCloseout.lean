import Collatz.SourceCoherenceAudit
import Collatz.HardCrossingFuture
import Collatz.FinalExcursion

namespace CollatzFinal
namespace SourceProduct

/-- Exact constructor-domain decomposition of a first crossing on a hypothetical
minimal positive bad source.

Nothing is abstracted away:
* the crossing is hard (no exit at the crossing);
* either the source lies in the origin branch n <= q;
* or q < n, in which case the endpoint is in the rigid large-source window
  3*y < 4*n and the warranted scalar signature y = 7 mod 12.

This is the domain split that a lower-source constructor compiler must cover. -/
theorem minimal_bad_first_crossing_constructor_domains
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    let q := oddCount n (k + 1)
    let y := iter shortcut (k + 1) n
    HardFirstCrossing n k ∧
      (n ≤ q ∨
        (q < n ∧ 3 * y < 4 * n ∧ y % 12 = 7)) := by
  let q := oddCount n (k + 1)
  let y := iter shortcut (k + 1) n
  have hhard : HardFirstCrossing n k :=
    minimal_bad_first_crossing_is_hard hmin hfirst
  refine ⟨hhard, ?_⟩
  by_cases horigin : n ≤ q
  · exact Or.inl horigin
  · have hq : q < n := by omega
    have hwin : 3 * y < 4 * n := by
      dsimp [y]
      exact first_crossing_three_y_lt_four_n hmin.1.1 hfirst hq
    have hsig := minimal_bad_hard_crossing_large_source_signature
      hmin hfirst hq
    have hmod : y % 12 = 7 := by
      apply (scalar_large_signature_iff_mod12 y).1
      simpa [y] using hsig
    exact Or.inr ⟨hq, hwin, hmod⟩

/-- A large-source hard first crossing is forced into the upper half of
the pre-cross coefficient band.  If the coefficient ratio were at most 3/2,
the elementary affine-bias budget could not keep the forced even pre-cross
endpoint at or above 2*n.

This is an exact integer inequality; no logarithm estimate is used. -/
theorem hard_large_previous_coefficient_gt_three_halves
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hq : oddCount n (k + 1) < n) :
    3 * 2 ^ k < 2 * 3 ^ oddCount n k := by
  have heven := hard_first_crossing_last_step_even hhard
  have hqeq : oddCount n (k + 1) = oddCount n k := by
    simp [oddCount, heven]
  have hqk : oddCount n k < n := by
    simpa [hqeq] using hq
  have hpre0 := first_crossing_previous_survival_bound hhard.1
  have hpre : ∀ i, i < k → 2 ^ i ≤ 3 ^ oddCount n i := by
    intro i hi
    exact hpre0 i (Nat.lt_trans hi (Nat.lt_succ_self k))
  have hb := elementary_bias_bound_of_no_earlier_crossing n k hpre
  have hy := hard_first_crossing_previous_ge_double hn hhard
  have ha := exact_affine n k
  have hs := Nat.mul_le_mul_left (2 ^ k) hy
  rw [ha] at hs
  have hpowpos : 0 < 3 ^ oddCount n k := Nat.pow_pos (by decide)
  have hqn :
      oddCount n k * 3 ^ oddCount n k <
        n * 3 ^ oddCount n k := by
    exact Nat.mul_lt_mul_right (3 ^ oddCount n k) hqk
  by_contra hnot
  have hcoef : 2 * 3 ^ oddCount n k ≤ 3 * 2 ^ k := by
    omega
  have hcoefN := Nat.mul_le_mul_right n hcoef
  have hs3 := Nat.mul_le_mul_left 3 hs
  have hqn' :
      oddCount n k * 3 ^ oddCount n k <
        3 ^ oddCount n k * n := by
    simpa [Nat.mul_comm] using hqn
  have hcoefN' :
      2 * (3 ^ oddCount n k * n) ≤
        3 * (2 ^ k * n) := by
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hcoefN
  have hs3' :
      3 * (2 * (2 ^ k * n)) ≤
        3 * (3 ^ oddCount n k * n + bias n k) := by
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hs3
  omega

/-- Constructor coverage needed only on the eternal-survival branch. -/
def EternalConstructorCoverage : Prop :=
  ∀ n, 1 < n → EternalCoefficientSurvival n →
    ∃ k, OrdinaryExit n (iter shortcut k n)

/-- Constructor coverage needed only on hard first crossings in the origin
branch.  Coverage may fire at any later depth and may be direct descent,
terminal reach, or any lower-source coalescence. -/
def OriginCrossingConstructorCoverage : Prop :=
  ∀ n k, 1 < n → HardFirstCrossing n k →
    n ≤ oddCount n (k + 1) →
    ∃ j, OrdinaryExit n (iter shortcut ((k + 1) + j) n)

/-- Constructor coverage needed only on the rigid large-source hard-crossing
branch.  The residue/window assumptions are consequences of minimal badness,
not extra conjectures. -/
def LargeCrossingConstructorCoverage : Prop :=
  ∀ n k, 1 < n → HardFirstCrossing n k →
    oddCount n (k + 1) < n →
    3 * iter shortcut (k + 1) n < 4 * n →
    iter shortcut (k + 1) n % 12 = 7 →
    ∃ j, OrdinaryExit n (iter shortcut ((k + 1) + j) n)

/-- Full assembly theorem.

The old proof search has been reduced to three goal-relative constructor
coverage interfaces.  If Crystal supplies an exact OrdinaryExit constructor on
each of these domains, the existing source-order/minimal-bad kernel closes
Collatz immediately.  No time-indexed rank, uniform block bound, or universal
first-crossing descent theorem is required. -/
theorem reaches_one_of_assembled_constructor_coverage
    (hEternal : EternalConstructorCoverage)
    (hOrigin : OriginCrossingConstructorCoverage)
    (hLarge : LargeCrossingConstructorCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      have hn : 0 < n := hmin.1.1
      have hne : n ≠ 1 := by
        intro heq
        apply hmin.1.2
        subst n
        exact ⟨0, by simp [iter, Terminal]⟩
      omega
    rcases coefficient_survival_or_first_crossing n with hsurv | ⟨d, hfirst⟩
    · obtain ⟨k, hexit⟩ := hEternal n hgt hsurv
      exact minimal_bad_has_no_ordinary_exit hmin k hexit
    · cases d with
      | zero =>
          have hc : CoefficientCrossingAt n 0 := hfirst.1
          unfold CoefficientCrossingAt at hc
          simp at hc
      | succ k =>
          have hhard : HardFirstCrossing n k :=
            minimal_bad_first_crossing_is_hard hmin hfirst
          rcases minimal_bad_first_crossing_constructor_domains
            hmin hfirst with ⟨_, horigin | hlarge⟩
          · obtain ⟨j, hexit⟩ :=
              hOrigin n k hgt hhard horigin
            exact minimal_bad_has_no_ordinary_exit hmin ((k + 1) + j) hexit
          · rcases hlarge with ⟨hq, hwin, hmod⟩
            obtain ⟨j, hexit⟩ :=
              hLarge n k hgt hhard hq hwin hmod
            exact minimal_bad_has_no_ordinary_exit hmin ((k + 1) + j) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms minimal_bad_first_crossing_constructor_domains
#print axioms reaches_one_of_assembled_constructor_coverage

end SourceProduct
end CollatzFinal
