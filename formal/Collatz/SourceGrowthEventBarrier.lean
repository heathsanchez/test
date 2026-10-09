import Collatz.UnboundedParityHeights

namespace CollatzFinal
namespace SourceProduct

/-!
V143 — EXACT SOURCE-ATTACHED TWO-STEP GROWTH-EVENT BARRIER.

The V139 unbounded orbit branch and V142 unbounded odd/even heights
do not yet expose WHERE genuine large-step growth must originate.

For the ACTUAL shortcut map T, if x % 4 != 3 then T^2(x) <= x.
For x % 4 = 3, both genuine shortcut steps are odd and
  4 * T^2(x) = 9*x+5 > 4*x.

Consequently, if the ORIGINAL source n has all T^k(n) ≡ 3 (mod 4)
bounded by B, its whole infinite ACTUAL orbit is bounded by
  2*n + 6*B + 5.
(The proof bounds even-time and odd-time positions separately.)

Therefore any hypothetical unbounded positive orbit must contain
arbitrarily large ACTUAL 3-mod-4 growth events. A least positive bad
source cannot avoid this and preserves the original-source no-merge
guards inherited from V139.

This is a NECESSARY source-coupled constraint. Mersenne initial
sources 2^K-1 exhibit arbitrarily long finite 3-mod-4 growth
corridors as K varies. No infinite actual divergent source is
constructed, no cycle excluded, and no Collatz QED is claimed.
-/

/-- In every residue except 3 mod 4, two actual shortcut steps
    are nonexpanding (including the terminal 1↔2 cycle). -/
theorem two_shortcuts_nonexpanding_except_three_mod_four
    (x : Nat) (hnot : x % 4 ≠ 3) :
    iter shortcut 2 x ≤ x := by
  have hres : x % 4 = 0 ∨ x % 4 = 1 ∨ x % 4 = 2 := by omega
  rcases hres with h0 | h1 | h2
  · have heven : x % 2 = 0 := by omega
    have hhalfEven : (x / 2) % 2 = 0 := by omega
    have hs : shortcut x = x / 2 := by
      simp [shortcut, heven]
    have ht : iter shortcut 2 x = (x / 2) / 2 := by
      change shortcut (shortcut x) = (x / 2) / 2
      rw [hs]
      simp [shortcut, hhalfEven]
    rw [ht]
    omega
  · have hodd : x % 2 = 1 := by omega
    have hs : shortcut x = (3 * x + 1) / 2 := by
      simp [shortcut, hodd]
    have hhalfEven : ((3 * x + 1) / 2) % 2 = 0 := by omega
    have ht : iter shortcut 2 x = ((3 * x + 1) / 2) / 2 := by
      change shortcut (shortcut x) = _
      rw [hs]
      simp [shortcut, hhalfEven]
    rw [ht]
    omega
  · have heven : x % 2 = 0 := by omega
    have hs : shortcut x = x / 2 := by
      simp [shortcut, heven]
    have hhalfOdd : (x / 2) % 2 = 1 := by omega
    have ht : iter shortcut 2 x = (3 * (x / 2) + 1) / 2 := by
      change shortcut (shortcut x) = _
      rw [hs]
      simp [shortcut, hhalfOdd]
    rw [ht]
    omega

/-- Only residue 3 mod 4 permits a genuine TWO-step increase.
    Exact arithmetic rather than floating-point average drift. -/
theorem two_shortcuts_exact_growth_three_mod_four
    (x : Nat) (hthree : x % 4 = 3) :
    4 * iter shortcut 2 x = 9 * x + 5 := by
  have hodd : x % 2 = 1 := by omega
  have hs : shortcut x = (3 * x + 1) / 2 := by
    simp [shortcut, hodd]
  have hnextOdd : ((3 * x + 1) / 2) % 2 = 1 := by omega
  have ht : iter shortcut 2 x =
      (3 * ((3 * x + 1) / 2) + 1) / 2 := by
    change shortcut (shortcut x) = _
    rw [hs]
    simp [shortcut, hnextOdd]
  rw [ht]
  omega

/-- An absolute one-step upper bound with no parity assumption. -/
theorem shortcut_le_two_times_plus_one (x : Nat) :
    shortcut x ≤ 2 * x + 1 := by
  by_cases heven : x % 2 = 0
  · have hs : shortcut x = x / 2 := by
      simp [shortcut, heven]
    rw [hs]
    omega
  · have hodd : x % 2 = 1 := by omega
    have hs : shortcut x = (3 * x + 1) / 2 := by
      simp [shortcut, hodd]
    rw [hs]
    omega

/-- If all REAL 3-mod-4 states stay below B, the ENTIRE actual
    two-step subsequence stays below n + 3*B + 2.
    This is a theorem about ONE unchanged starting source n. -/
theorem bounded_growth_events_bound_even_time_orbit
    (n B : Nat)
    (hthree : ∀ k : Nat,
      iter shortcut k n % 4 = 3 → iter shortcut k n ≤ B) :
    ∀ k : Nat,
      iter shortcut (2 * k) n ≤ n + 3 * B + 2 := by
  intro k
  induction k with
  | zero =>
    simp only [Nat.mul_zero, iter]
    omega
  | succ k ih =>
    have hindex : 2 * (k + 1) = 2 * k + 2 := by omega
    rw [hindex, iter_add]
    let x := iter shortcut (2 * k) n
    by_cases hx : x % 4 = 3
    · have hxb : x ≤ B := hthree (2 * k) hx
      have hvalue := two_shortcuts_exact_growth_three_mod_four x hx
      change iter shortcut 2 x ≤ n + 3 * B + 2
      omega
    · have hdrop := two_shortcuts_nonexpanding_except_three_mod_four x hx
      change iter shortcut 2 x ≤ n + 3 * B + 2
      omega

/-- Actual odd-time positions are controlled by the already bounded
    even-time positions. The resulting coarse explicit bound is
    2*n + 6*B + 5, with neither uniform stopping time nor density. -/
theorem bounded_growth_events_bound_full_actual_orbit
    (n B : Nat)
    (hthree : ∀ k : Nat,
      iter shortcut k n % 4 = 3 → iter shortcut k n ≤ B) :
    ∀ k : Nat,
      iter shortcut k n ≤ 2 * n + 6 * B + 5 := by
  intro k
  have htimes :
      k = 2 * (k / 2) ∨ k = 2 * (k / 2) + 1 := by omega
  rcases htimes with he | ho
  · rw [he]
    have h := bounded_growth_events_bound_even_time_orbit
      n B hthree (k / 2)
    omega
  · rw [ho, iter_succ_last]
    have h := bounded_growth_events_bound_even_time_orbit
      n B hthree (k / 2)
    have hstep :=
      shortcut_le_two_times_plus_one
        (iter shortcut (2 * (k / 2)) n)
    omega

/-- V142's unbounded both-parity condition sharpens to an exact
    unbounded GROWTH-GENERATOR requirement: actual 3(mod4) states
    must themselves exceed every B. This is still not a contradiction. -/
theorem actual_unbounded_orbit_has_unbounded_three_mod_four_growth
    (n : Nat) (hu : ActualOrbitUnbounded n) (B : Nat) :
    ∃ k : Nat, B < iter shortcut k n ∧
      iter shortcut k n % 4 = 3 := by
  apply Classical.byContradiction
  intro hnone
  have hbounded : ∀ k : Nat,
      iter shortcut k n % 4 = 3 → iter shortcut k n ≤ B := by
    intro k hk
    have hnot : ¬ B < iter shortcut k n := by
      intro hgt
      exact hnone ⟨k, hgt, hk⟩
    omega
  obtain ⟨k, hgt⟩ := hu (2 * n + 6 * B + 5)
  have hmax :=
    bounded_growth_events_bound_full_actual_orbit n B hbounded k
  omega

/-- Under actual original-source minimal-bad hypotheses, arbitrarily
    large 3mod4 growth generators are necessary and remain >= n.
    V139 already rules out any smaller positive source meeting at
    independent actual clocks; it is NOT proven that no such stream
    exists. -/
theorem least_bad_unbounded_requires_unbounded_true_growth
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (hu : ActualOrbitUnbounded n) (B : Nat) :
    ∃ k : Nat, B < iter shortcut k n ∧
      n ≤ iter shortcut k n ∧
      iter shortcut k n % 4 = 3 := by
  obtain ⟨k, hhigh, hmod⟩ :=
    actual_unbounded_orbit_has_unbounded_three_mod_four_growth n hu B
  exact ⟨k, hhigh,
    minimal_positive_bad_never_below_source hmin k, hmod⟩

#print axioms two_shortcuts_nonexpanding_except_three_mod_four
#print axioms two_shortcuts_exact_growth_three_mod_four
#print axioms shortcut_le_two_times_plus_one
#print axioms bounded_growth_events_bound_even_time_orbit
#print axioms bounded_growth_events_bound_full_actual_orbit
#print axioms actual_unbounded_orbit_has_unbounded_three_mod_four_growth
#print axioms least_bad_unbounded_requires_unbounded_true_growth

end SourceProduct
end CollatzFinal
