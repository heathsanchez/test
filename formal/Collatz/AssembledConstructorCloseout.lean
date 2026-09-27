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

/-- Exact additive payment forced by any hard first crossing.

The crossing endpoint is nondescending, so its coefficient deficit must be paid
by affine bias.  The elementary pre-cross bias estimate then gives a single
source-relative inequality. -/
theorem hard_first_crossing_bias_payment
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k) :
    3 * (2 ^ (k + 1) - 3 ^ oddCount n (k + 1)) * n ≤
      oddCount n (k + 1) * 3 ^ oddCount n (k + 1) := by
  have hnd := hard_first_crossing_endpoint_ge_source hn hhard
  have hm := margin_nonnegative_of_nondescending hnd
  have hpre := first_crossing_previous_survival_bound hhard.1
  have hb :=
    elementary_bias_bound_of_no_earlier_crossing n (k + 1) hpre
  have hm3 := Nat.mul_le_mul_left 3 hm
  exact Nat.le_trans
    (by simpa [Nat.mul_assoc] using hm3) hb

/-- A large-source hard first crossing is forced into the upper half of
the pre-cross coefficient band.  If the coefficient ratio were at most 3/2,
the contraction deficit alone would already exceed the entire allowed bias
payment because q<n.

This is an exact integer inequality; no logarithm estimate is used. -/
theorem hard_large_previous_coefficient_gt_three_halves
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hq : oddCount n (k + 1) < n) :
    3 * 2 ^ k < 2 * 3 ^ oddCount n (k + 1) := by
  let q := oddCount n (k + 1)
  let P := 3 ^ q
  have hpay := hard_first_crossing_bias_payment hn hhard
  have hPpos : 0 < P := by
    dsimp [P]
    exact Nat.pow_pos (by decide)
  have hqP : q * P < n * P := by
    exact (Nat.mul_lt_mul_right hPpos).2 (by simpa [q] using hq)
  by_cases hcoef : 2 * P ≤ 3 * 2 ^ k
  · have hD : P ≤ 3 * (2 ^ (k + 1) - P) := by
      have hpow : 2 ^ (k + 1) = 2 * 2 ^ k := by
        simp [Nat.pow_succ, Nat.mul_comm]
      rw [hpow]
      omega
    have hDn := Nat.mul_le_mul_right n hD
    have hpay' :
        3 * (2 ^ (k + 1) - P) * n ≤ q * P := by
      simpa [q, P] using hpay
    have hDn' :
        P * n ≤ 3 * (2 ^ (k + 1) - P) * n := by
      simpa [Nat.mul_assoc] using hDn
    have hqP' : q * P < P * n := by
      simpa [Nat.mul_comm] using hqP
    omega
  · change 3 * 2 ^ k < 2 * P
    exact Nat.lt_of_not_ge hcoef

/-- Elementary exponential separation used to force a fixed source into
the high-odd regime under eternal coefficient survival. -/
theorem three_pow_lt_four_pow_succ (m : Nat) :
    3 ^ (m + 1) < 4 ^ (m + 1) := by
  induction m with
  | zero => decide
  | succ m ih =>
      have h3 : 0 < 3 ^ (m + 1) := Nat.pow_pos (by decide)
      have hleft :
          3 * 3 ^ (m + 1) < 4 * 3 ^ (m + 1) :=
        Nat.mul_lt_mul_of_pos_right (by decide : 3 < 4) h3
      have hright :
          4 * 3 ^ (m + 1) < 4 * 4 ^ (m + 1) :=
        Nat.mul_lt_mul_of_pos_left ih (by decide : 0 < 4)
      simpa [Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm,
        Nat.mul_assoc] using Nat.lt_trans hleft hright

/-- At dyadic depth 2*n the deterministic survival threshold already requires
strictly more than n odd steps. -/
theorem source_lt_qmin_double (n : Nat) (hn : 0 < n) :
    n < qmin (2 * n) := by
  obtain ⟨m, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (by omega : n ≠ 0)
  have hp := three_pow_lt_four_pow_succ m
  have hfour : 4 ^ (m + 1) = 2 ^ (2 * (m + 1)) := by
    rw [show 4 = 2 ^ 2 by decide, ← Nat.pow_mul]
  rw [hfour] at hp
  apply Nat.lt_of_not_ge
  intro hnot
  have hq : qmin (2 * (m + 1)) ≤ m + 1 := hnot
  have hpow :
      3 ^ qmin (2 * (m + 1)) ≤ 3 ^ (m + 1) :=
    Nat.pow_le_pow_right (by decide) hq
  have hs := qmin_spec (2 * (m + 1))
  omega

/-- One constructor interface covers both the eternal-survival branch and the
old n<=q origin branch: once a live prefix has accumulated at least n odd
steps, produce any later OrdinaryExit. -/
def HighOddConstructorCoverage : Prop :=
  ∀ n k, 1 < n → CoefficientSurvives n k →
    n ≤ oddCount n k →
    ∃ j, OrdinaryExit n (iter shortcut (k + j) n)

/-- Eternal coefficient survival necessarily enters the high-odd constructor
domain by depth 2*n. -/
theorem eternal_survival_enters_high_odd
    {n : Nat} (hn : 0 < n)
    (hsurv : EternalCoefficientSurvival n) :
    CoefficientSurvives n (2 * n) ∧
      n ≤ oddCount n (2 * n) := by
  have hs := hsurv (2 * n)
  have hq := (coefficientSurvives_iff_qmin_le n (2 * n)).1 hs
  have hstrict := source_lt_qmin_double n hn
  exact ⟨hs, by omega⟩

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

/-- Two-domain closeout.

HighOddConstructorCoverage subsumes both eternal coefficient survival and the
n<=q first-crossing origin branch.  The only separate constructor domain left
is the rigid q<n large-source hard crossing. -/
theorem reaches_one_of_two_constructor_domains
    (hHigh : HighOddConstructorCoverage)
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
    · obtain ⟨hs, hq⟩ :=
        eternal_survival_enters_high_odd hmin.1.1 hsurv
      obtain ⟨j, hexit⟩ := hHigh n (2 * n) hgt hs hq
      exact minimal_bad_has_no_ordinary_exit hmin (2 * n + j) hexit
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
          · have heven := hard_first_crossing_last_step_even hhard
            have hqeq :
                oddCount n (k + 1) = oddCount n k := by
              simp [oddCount, heven]
            have hsurvK : CoefficientSurvives n k := by
              unfold CoefficientSurvives coefficientDenominator coefficientNumerator
              exact first_crossing_previous_survival_bound hfirst k
                (Nat.lt_succ_self k)
            have hqK : n ≤ oddCount n k := by
              simpa [hqeq] using horigin
            obtain ⟨j, hexit⟩ := hHigh n k hgt hsurvK hqK
            exact minimal_bad_has_no_ordinary_exit hmin (k + j) hexit
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

#print axioms source_lt_qmin_double
#print axioms eternal_survival_enters_high_odd
#print axioms minimal_bad_first_crossing_constructor_domains
#print axioms reaches_one_of_two_constructor_domains
#print axioms reaches_one_of_assembled_constructor_coverage

end SourceProduct
end CollatzFinal
