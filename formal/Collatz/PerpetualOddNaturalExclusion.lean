import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-!
V140 — EXCLUDE THE PERPETUAL-ODD 2-ADIC GHOST FOR EVERY ACTUAL
NATURAL SOURCE, WITHOUT ASSUMING A LOWER-SOURCE MEETING.

The exact V116 all-ones corridor shows arbitrarily long FINITE
positive-Nat odd prefixes, as the source changes with the horizon.

A fixed natural n has n+1=2^m*u with positive ODD u.
The actual shortcut orbit then obeys:
   iter shortcut m n = 3^m*u-1,
which is EVEN. Therefore no eventual tail is all odd forever.

This excludes ONE genuine infinite symbolic escape type on the
positive natural domain. It does NOT exclude trajectories with
infinitely many odd and even steps, nonterminal cycles, or unbounded
no-merge orbits. No universal Collatz result.
-/

/-- Requalification of the elementary V116 odd-step rewrite.
    The source value remains an actual natural, never negative. -/
theorem positive_odd_step_normal_form (z : Nat) (hz : 0 < z) :
    shortcut (2 * z - 1) = 3 * z - 1 := by
  have hodd : (2 * z - 1) % 2 = 1 := by omega
  simp [shortcut, hodd]
  omega

/-- Every strictly positive natural has a finite, source-coupled
    factorization as a power of two times an odd positive natural.
    No unbounded valuation or compactness assumption is used. -/
theorem positive_natural_twopower_odd_factor :
    ∀ x : Nat, 0 < x →
      ∃ m u : Nat,
        0 < u ∧ u % 2 = 1 ∧ x = 2 ^ m * u := by
  intro x
  induction x using Nat.strongRecOn with
  | ind x ih =>
      intro hx
      by_cases heven : x % 2 = 0
      · have hy : 0 < x / 2 := by omega
        have hlt : x / 2 < x := by omega
        obtain ⟨m, u, hu, hodd, hfact⟩ := ih (x / 2) hlt hy
        refine ⟨m + 1, u, hu, hodd, ?_⟩
        calc
          x = 2 * (x / 2) := by omega
          _ = 2 * (2 ^ m * u) := by rw [hfact]
          _ = 2 ^ (m + 1) * u := by
                simp [Nat.pow_succ, Nat.mul_assoc,
                  Nat.mul_comm, Nat.mul_left_comm]
      · refine ⟨0, x, hx, ?_, ?_⟩
        · omega
        · simp

/-- Exact all-odd corridor in the useful generality u>0.
    This generalizes V116's u=1 Mersenne source identity
    WITHOUT pretending the corridor lasts indefinitely. -/
theorem general_odd_prefix_exact (k u : Nat) (hu : 0 < u) :
    iter shortcut k (2 ^ k * u - 1) = 3 ^ k * u - 1 := by
  induction k generalizing u with
  | zero => simp [iter]
  | succ k ih =>
      have hz : 0 < 2 ^ k * u :=
        Nat.mul_pos (Nat.pow_pos (by decide)) hu
      have hpow : 2 ^ (k + 1) * u = 2 * (2 ^ k * u) := by
        simp [Nat.pow_succ, Nat.mul_assoc,
          Nat.mul_comm, Nat.mul_left_comm]
      calc
        iter shortcut (k + 1) (2 ^ (k + 1) * u - 1) =
            iter shortcut k (shortcut (2 * (2 ^ k * u) - 1)) := by
              change iter shortcut k
                (shortcut (2 ^ (k + 1) * u - 1)) = _
              rw [hpow]
        _ = iter shortcut k (3 * (2 ^ k * u) - 1) := by
              rw [positive_odd_step_normal_form _ hz]
        _ = iter shortcut k (2 ^ k * (3 * u) - 1) := by
              congr 1
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ = 3 ^ k * (3 * u) - 1 := ih (3 * u) (by omega)
        _ = 3 ^ (k + 1) * u - 1 := by
              simp [Nat.pow_succ, Nat.mul_assoc,
                Nat.mul_comm, Nat.mul_left_comm]

/-- Powers of three are odd for every natural exponent. -/
theorem three_power_odd_mod_two (m : Nat) : 3 ^ m % 2 = 1 := by
  induction m with
  | zero => decide
  | succ m ih =>
      rw [Nat.pow_succ]
      omega

/-- Every ACTUAL natural shortcut orbit has an even-valued iterate.
    The witness clock is the finite 2-adic valuation of n+1,
    constructed via positive_natural_twopower_odd_factor.

    This is NOT a stopping-time, lower-merge, or convergence theorem. -/
theorem every_natural_shortcut_orbit_reaches_even (n : Nat) :
    ∃ m : Nat, iter shortcut m n % 2 = 0 := by
  obtain ⟨m, u, hu, hodd, hfactor⟩ :=
    positive_natural_twopower_odd_factor (n + 1) (by omega)
  have hpositive : 0 < 2 ^ m * u :=
    Nat.mul_pos (Nat.pow_pos (by decide)) hu
  have hn : n = 2 ^ m * u - 1 := by omega
  refine ⟨m, ?_⟩
  rw [hn, general_odd_prefix_exact m u hu]
  have hm : (3 ^ m * u) % 2 = 1 := by
    rw [Nat.mul_mod]
    simp [three_power_odd_mod_two m, hodd]
  omega

/-- An eventually all-odd infinite 2-adic parity stream cannot be
    the *actual* future of ANY natural number. Source identity matters:
    arbitrarily long Mersenne shadows change the source with k. -/
def PerpetualOddNaturalTail (n : Nat) : Prop :=
  ∃ i : Nat, ∀ k : Nat, (iter shortcut (i + k) n) % 2 = 1

theorem no_perpetual_odd_tail_from_any_natural (n : Nat) :
    ¬ PerpetualOddNaturalTail n := by
  intro h
  obtain ⟨i, htail⟩ := h
  obtain ⟨k, heven⟩ :=
    every_natural_shortcut_orbit_reaches_even (iter shortcut i n)
  have hactual : iter shortcut (i + k) n =
      iter shortcut k (iter shortcut i n) :=
    iter_add shortcut i k n
  have hodd := htail k
  rw [hactual] at hodd
  omega

#print axioms positive_odd_step_normal_form
#print axioms positive_natural_twopower_odd_factor
#print axioms general_odd_prefix_exact
#print axioms three_power_odd_mod_two
#print axioms every_natural_shortcut_orbit_reaches_even
#print axioms no_perpetual_odd_tail_from_any_natural

end SourceProduct
end CollatzFinal
