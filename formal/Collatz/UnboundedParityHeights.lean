import Collatz.PerpetualOddNaturalExclusion
import Collatz.ActualOrbitDichotomy

namespace CollatzFinal
namespace SourceProduct

/-!
V142 — ACTUAL UNBOUNDED POSITIVE ORBITS MUST GROW IN BOTH PARITIES.

This is a source-coupled necessary condition, not a proof that
unbounded orbits exist or do not exist.

V140 says every natural has a finite FIRST-EVEN clock m encoded by
n+1 = 2^m * u, u odd, with T^m(n) = 3^m*u-1. Since 3^m >= 2^m,
the even endpoint does not fall below the original positive source.

Conversely, if ALL odd endpoints are bounded by B, then EVERY
endpoint is bounded by n+3*B+1: even steps halve; odd steps may grow,
but only from an endpoint <=B. Thus a genuinely unbounded orbit has
arbitrarily high odd endpoints.

Together: arbitrarily high EVEN and ODD endpoints are necessary for
the V139 unbounded positive-natural alternative. If the original
source is a hypothetical LEAST bad source, V139 adds that both
parity extrema must remain >= that unchanged source and can never
merge with any smaller positive source.

No nonterminal cycle exclusion, no unbounded-orbit exclusion, no QED.
-/

/-- Elementary, non-probabilistic power inequality. -/
theorem two_power_le_three_power (m : Nat) :
    (2 : Nat) ^ m ≤ 3 ^ m := by
  induction m with
  | zero => decide
  | succ m ih =>
    rw [Nat.pow_succ, Nat.pow_succ]
    have h1 : (2 : Nat) ^ m * 2 ≤ (3 : Nat) ^ m * 2 :=
      Nat.mul_le_mul_right 2 ih
    have h2 : (3 : Nat) ^ m * 2 ≤ (3 : Nat) ^ m * 3 :=
      Nat.mul_le_mul_left (3 ^ m) (by decide : (2 : Nat) ≤ 3)
    exact Nat.le_trans h1 h2

/-- For EVERY positive actual natural state, the first-even endpoint
    from the canonical 2-adic finite odd corridor is not smaller than
    that state. A source that is already even has clock 0. -/
theorem positive_source_has_later_even_not_below
    (n : Nat) (hn : 0 < n) :
    ∃ m : Nat,
      iter shortcut m n % 2 = 0 ∧
      n ≤ iter shortcut m n := by
  obtain ⟨m,u,hu,huOdd,hfac⟩ :=
    positive_natural_twopower_odd_factor (n + 1) (by omega)
  have hnsource : n = 2 ^ m * u - 1 := by
    omega
  have heval : iter shortcut m n = 3 ^ m * u - 1 := by
    rw [hnsource]
    exact general_odd_prefix_exact m u hu
  have hoddproduct : (3 ^ m * u) % 2 = 1 := by
    rw [Nat.mul_mod]
    simp [three_power_odd_mod_two m, huOdd]
  have hpositiveproduct : 0 < 3 ^ m * u :=
    Nat.mul_pos (Nat.pow_pos (by decide)) hu
  have heven : iter shortcut m n % 2 = 0 := by
    rw [heval]
    omega
  have hmult : 2 ^ m * u ≤ 3 ^ m * u :=
    Nat.mul_le_mul_right u (two_power_le_three_power m)
  have hsourcele : n ≤ iter shortcut m n := by
    rw [heval, hnsource]
    omega
  exact ⟨m, heven, hsourcele⟩

/-- Contrapositive odd growth barrier. If a trajectory's odd values
    never exceed B, ALL its positive/zero values are bounded by
    M=n+3B+1. This preserves the SAME starting source n. -/
theorem bounded_odd_endpoints_bound_whole_orbit
    (n B : Nat)
    (hodd : ∀ k : Nat,
      iter shortcut k n % 2 = 1 →
      iter shortcut k n ≤ B) :
    ∀ k : Nat, iter shortcut k n ≤ n + 3 * B + 1 := by
  intro k
  induction k with
  | zero =>
    simp only [iter]
    omega
  | succ k ih =>
    rw [iter_succ_last]
    let x := iter shortcut k n
    by_cases heven : x % 2 = 0
    · have hs : shortcut x = x / 2 := by
        simp [shortcut, heven]
      rw [hs]
      change x / 2 ≤ n + 3 * B + 1
      omega
    · have hoddx : x % 2 = 1 := by omega
      have hx : x ≤ B := hodd k hoddx
      have hs : shortcut x = (3 * x + 1) / 2 := by
        simp [shortcut, hoddx]
      rw [hs]
      change (3 * x + 1) / 2 ≤ n + 3 * B + 1
      omega

/-- An unbounded true Nat trajectory MUST attain arbitrarily large
    ODD values. This is not a random parity-density assumption. -/
theorem unbounded_source_has_unbounded_odd_values
    (n : Nat) (hu : ActualOrbitUnbounded n)
    (B : Nat) :
    ∃ k : Nat,
      B < iter shortcut k n ∧
      iter shortcut k n % 2 = 1 := by
  apply Classical.byContradiction
  intro hnone
  have hodd : ∀ k : Nat,
      iter shortcut k n % 2 = 1 →
      iter shortcut k n ≤ B := by
    intro k hk
    have hnot : ¬ B < iter shortcut k n := by
      intro hgt
      exact hnone ⟨k, hgt, hk⟩
    omega
  obtain ⟨k, hgt⟩ := hu (n + 3 * B + 1)
  have hbound := bounded_odd_endpoints_bound_whole_orbit n B hodd k
  omega

/-- Any large ACTUAL forward state eventually has an even successor
    at least as large. Hence unbounded Nat trajectories also have
    arbitrarily large EVEN values. -/
theorem unbounded_positive_source_has_unbounded_even_values
    (n : Nat) (hn : 0 < n)
    (hu : ActualOrbitUnbounded n) (B : Nat) :
    ∃ k : Nat,
      B < iter shortcut k n ∧
      iter shortcut k n % 2 = 0 := by
  obtain ⟨i, hhigh⟩ := hu B
  have hp : 0 < iter shortcut i n :=
    iter_positive shortcut shortcut_positive i n hn
  obtain ⟨j, heven, hge⟩ :=
    positive_source_has_later_even_not_below (iter shortcut i n) hp
  refine ⟨i + j, ?_, ?_⟩
  · rw [iter_add]
    omega
  · simpa only [iter_add] using heven

/-- The exact two-sided height requirement on an actual unbounded
    positive Nat source. No upper bound on gaps is asserted. -/
theorem unbounded_positive_source_has_both_parity_heights
    (n : Nat) (hn : 0 < n)
    (hu : ActualOrbitUnbounded n) :
    ∀ B : Nat,
      (∃ i : Nat, B < iter shortcut i n ∧
        iter shortcut i n % 2 = 0) ∧
      (∃ j : Nat, B < iter shortcut j n ∧
        iter shortcut j n % 2 = 1) := by
  intro B
  exact ⟨unbounded_positive_source_has_unbounded_even_values n hn hu B,
    unbounded_source_has_unbounded_odd_values n hu B⟩

/-- Reuse the V139 TRUE original-source minimality: if a least bad
    source entered the unbounded branch, BOTH parity colour classes
    would reach arbitrarily high ACTUAL values, each >= the original
    source, and no positive smaller source can meet either future. -/
theorem least_positive_bad_unbounded_has_both_high_source_attached
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (hu : ActualOrbitUnbounded n) :
    ∀ B : Nat,
      (∃ i : Nat, B < iter shortcut i n ∧
        n ≤ iter shortcut i n ∧
        iter shortcut i n % 2 = 0) ∧
      (∃ j : Nat, B < iter shortcut j n ∧
        n ≤ iter shortcut j n ∧
        iter shortcut j n % 2 = 1) := by
  intro B
  obtain ⟨⟨i,hi,hie⟩,⟨j,hj,hjo⟩⟩ :=
    unbounded_positive_source_has_both_parity_heights n hmin.1.1 hu B
  exact ⟨⟨i,hi,minimal_positive_bad_never_below_source hmin i,hie⟩,
         ⟨j,hj,minimal_positive_bad_never_below_source hmin j,hjo⟩⟩

#print axioms two_power_le_three_power
#print axioms positive_source_has_later_even_not_below
#print axioms bounded_odd_endpoints_bound_whole_orbit
#print axioms unbounded_source_has_unbounded_odd_values
#print axioms unbounded_positive_source_has_unbounded_even_values
#print axioms unbounded_positive_source_has_both_parity_heights
#print axioms least_positive_bad_unbounded_has_both_high_source_attached

end SourceProduct
end CollatzFinal
