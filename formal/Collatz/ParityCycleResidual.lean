import Collatz.PerpetualOddNaturalExclusion
import Collatz.ActualOrbitDichotomy

namespace CollatzFinal
namespace SourceProduct

/-!
V141 — SOURCE-ATTACHED PARITY AND PERIODIC-IMBALANCE NECESSITY.

V139 independently qualified an ACTUAL positive minimal-bad orbit as
nonterminal periodic OR unbounded with no true lower-source merge.
V140 proved that NO genuine natural orbit has an eventually all-odd tail.

New small universal deductions:
(1) No positive actual orbit can have an eventually all-even tail.
(2) Every positive natural orbit visits BOTH parities arbitrarily late.
    No statistical parity density or bounded gap is claimed.
(3) A genuine positive-time positive periodic orbit must have
        3^(oddCount n k) < 2^k.
    The STRICT arithmetic inequality comes from the independent exact
    affine identity and incompatible power parities; it does NOT
    exclude nonterminal positive cycles.
(4) Any hypothetical least positive bad source n obeys n % 4 = 3.
    That excludes only a narrow source grammar, not all residuals.

The Mersenne sources exhibit arbitrarily long finite odd prefixes;
there is NO source-uniform bound on next parity change.
GLOBAL COLLATZ remains UNKNOWN.
-/

/-- A positive actual shortcut trajectory cannot remain even forever:
    halving would generate an infinite strictly descending positive Nat
    chain. Crucially this invokes positivity at the original source. -/
theorem positive_shortcut_orbit_not_all_even :
    ∀ n : Nat, 0 < n →
      ¬ (∀ k : Nat, iter shortcut k n % 2 = 0) := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
    intro hn heven
    have hnEven : n % 2 = 0 := by
      simpa only [iter] using heven 0
    have hs : shortcut n = n / 2 := by
      simp [shortcut, hnEven]
    have hsPos : 0 < shortcut n := shortcut_positive n hn
    have hlt : shortcut n < n := by
      rw [hs]
      omega
    have hfuture : ∀ k : Nat,
        iter shortcut k (shortcut n) % 2 = 0 := by
      intro k
      simpa only [iter] using heven (k + 1)
    exact ih (shortcut n) hlt hsPos hfuture

/-- The same excludes all-even FUTURE tails, at arbitrary source clock.
    It is distinct from V140's independently proved no-all-odd result. -/
theorem no_eventually_all_even_positive_tail
    (n : Nat) (hn : 0 < n) :
    ¬ (∃ i : Nat, ∀ k : Nat,
        iter shortcut (i + k) n % 2 = 0) := by
  intro ht
  obtain ⟨i, hi⟩ := ht
  have hp : 0 < iter shortcut i n :=
    iter_positive shortcut shortcut_positive i n hn
  have hfuture : ∀ k : Nat,
      iter shortcut k (iter shortcut i n) % 2 = 0 := by
    intro k
    simpa only [iter_add] using hi k
  exact positive_shortcut_orbit_not_all_even
    (iter shortcut i n) hp hfuture

/-- Both parity colours recur arbitrarily late along every positive
    source orbit. This gives neither bounded return clocks nor positive
    lower-source mergers. -/
theorem every_positive_source_revisits_both_parities
    (n : Nat) (hn : 0 < n) :
    (∀ i : Nat, ∃ j : Nat,
       i ≤ j ∧ iter shortcut j n % 2 = 0) ∧
    (∀ i : Nat, ∃ j : Nat,
       i ≤ j ∧ iter shortcut j n % 2 = 1) := by
  constructor
  · intro i
    apply Classical.byContradiction
    intro hnone
    have hodd : ∀ k : Nat,
        iter shortcut (i + k) n % 2 = 1 := by
      intro k
      have hnotEven : iter shortcut (i + k) n % 2 ≠ 0 := by
        intro he
        exact hnone ⟨i + k, by omega, he⟩
      omega
    exact no_perpetual_odd_tail_from_any_natural n ⟨i, hodd⟩
  · intro i
    apply Classical.byContradiction
    intro hnone
    have heven : ∀ k : Nat,
        iter shortcut (i + k) n % 2 = 0 := by
      intro k
      have hnotOdd : iter shortcut (i + k) n % 2 ≠ 1 := by
        intro ho
        exact hnone ⟨i + k, by omega, ho⟩
      omega
    exact no_eventually_all_even_positive_tail n hn ⟨i, heven⟩

/-- Positive actual periodic cycles satisfy an exact arity imbalance.
    2^k * n = 3^alpha * n + bias, with nonnegative exact bias.
    Consequently 3^alpha <= 2^k; equality is impossible at positive
    clock since the first power is odd and the second is even. -/
theorem positive_shortcut_cycle_strict_multiplier_defect
    (n k : Nat)
    (hn : 0 < n)
    (hk : 0 < k)
    (hperiod : iter shortcut k n = n) :
    3 ^ oddCount n k < 2 ^ k := by
  have heq :
      2 ^ k * n = 3 ^ oddCount n k * n + bias n k := by
    simpa only [hperiod] using exact_affine n k
  have hm : 3 ^ oddCount n k * n ≤ 2 ^ k * n := by
    omega
  have hle : 3 ^ oddCount n k ≤ 2 ^ k :=
    Nat.le_of_mul_le_mul_right hm hn
  have hodd : 3 ^ oddCount n k % 2 = 1 :=
    three_power_odd_mod_two (oddCount n k)
  have heven : 2 ^ k % 2 = 0 := by
    cases k with
    | zero => omega
    | succ t =>
      rw [Nat.pow_succ]
      omega
  omega

/-- Direct source guard for the least positive bad natural.
    Any even n>0 descends at the next actual shortcut step.
    Any odd n%4=1, n>1 descends strictly within two actual steps.
    Therefore a hypothetical least positive bad n must be 3 mod 4.
    This is not a complete classification of all survivor cylinders. -/
theorem least_positive_bad_source_three_mod_four
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    n % 4 = 3 := by
  have hn : 0 < n := hmin.1.1
  have hne1 : n ≠ 1 := by
    intro h
    subst n
    exact hmin.1.2 ⟨0, Or.inl rfl⟩
  have hgt : 1 < n := by omega
  have hnotEven : n % 2 ≠ 0 := by
    intro he
    have hs : shortcut n = n / 2 := by
      simp [shortcut, he]
    have hdec : iter shortcut 1 n < n := by
      change shortcut n < n
      rw [hs]
      omega
    have hno := minimal_positive_bad_never_below_source hmin 1
    omega
  have hcases : n % 4 = 1 ∨ n % 4 = 3 := by omega
  rcases hcases with hbad | hgood
  · have hodd : n % 2 = 1 := by omega
    have hs : shortcut n = (3 * n + 1) / 2 := by
      simp [shortcut, hodd]
    have hevenNext : (shortcut n) % 2 = 0 := by
      rw [hs]
      omega
    have htwo : iter shortcut 2 n = (shortcut n) / 2 := by
      change shortcut (shortcut n) = (shortcut n) / 2
      simp [shortcut, hevenNext]
    have hdec : iter shortcut 2 n < n := by
      rw [htwo, hs]
      omega
    have hno := minimal_positive_bad_never_below_source hmin 2
    omega
  · exact hgood

#print axioms positive_shortcut_orbit_not_all_even
#print axioms no_eventually_all_even_positive_tail
#print axioms every_positive_source_revisits_both_parities
#print axioms positive_shortcut_cycle_strict_multiplier_defect
#print axioms least_positive_bad_source_three_mod_four

end SourceProduct
end CollatzFinal
