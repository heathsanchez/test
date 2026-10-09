import Collatz.OneOddCycleObstruction

namespace CollatzFinal
namespace SourceProduct

/-!
V145 — EXCLUDE BOTH TWO-ODD AND FOUR-ODD NONTERMINAL PERIOD CLASSES.

For a true positive shortcut orbit with no terminal 1 at any clock,
every ODD state is at least 3. Hence at each odd step x:
  3 * (2 * shortcut x) = 3 * (3*x+1) <= 10*x;
at each even step, 2 * shortcut x = x.

Multiplying this exact bound over an arbitrary prefix gives
   3^alpha * 2^k * T^k(n) <= 10^alpha * n,
where alpha=oddCount(n,k) is the ACTUAL number of odd steps.

For a genuine positive period, T^k(n)=n, cancel n>0 to obtain
  3^alpha * 2^k <= 10^alpha.
V141 independently proves the STRICT lower bound 3^alpha < 2^k.

With alpha=2, the constraints are 9<2^k and 9*2^k<=100,
which no natural k satisfies.
With alpha=4, 81<2^k and 81*2^k<=10000, likewise impossible.

This eliminates nonterminal cycle periods of arbitrary length with
exactly two or four odd visits, not just a finite period census.
The source remains the unchanged original source; the explicit
nonterminal-future hypothesis is separately obtained from a
hypothetical least positive bad source and its true tail clocks.

No claim about periods with 3,5,6... odd visits, and no exclusion of
unbounded no-merge orbits. GLOBAL COLLATZ UNKNOWN.
-/

/-- Exact rearrangement of the four actual factors in an odd step. -/
private theorem odd_step_factors (a b c : Nat) :
    (a * 3) * (b * 2) * c = (a * b) * (3 * (2 * c)) := by
  calc
    (a * 3) * (b * 2) * c = a * (3 * (b * (2 * c))) := by
      simp only [Nat.mul_assoc]
    _ = a * (b * (3 * (2 * c))) := by
      rw [Nat.mul_left_comm 3 b]
    _ = (a * b) * (3 * (2 * c)) := by
      simp only [Nat.mul_assoc]

/-- A parity-exact multiplier upper bound for every genuine prefix
    whose actual orbit never hits the terminal odd source 1. -/
theorem never_one_prefix_multiplicative_bound
    (n k : Nat)
    (hnever : ∀ j : Nat, iter shortcut j n ≠ 1) :
    3 ^ oddCount n k * 2 ^ k * iter shortcut k n ≤
      10 ^ oddCount n k * n := by
  induction k with
  | zero =>
    simp [oddCount, iter]
  | succ k ih =>
    let x := iter shortcut k n
    by_cases he : x % 2 = 0
    · have ha : oddCount n (k + 1) = oddCount n k := by
        simp [oddCount, x, he]
      have hstep : 2 * shortcut x = x := by
        simpa [he] using double_shortcut x
      calc
        3 ^ oddCount n (k + 1) * 2 ^ (k + 1) *
            iter shortcut (k + 1) n =
            (3 ^ oddCount n k * 2 ^ k) * (2 * shortcut x) := by
              rw [ha, iter_succ_last]
              simp only [Nat.pow_succ]
              dsimp [x]
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ = 3 ^ oddCount n k * 2 ^ k *
            iter shortcut k n := by
              rw [hstep]
        _ ≤ 10 ^ oddCount n k * n := ih
        _ = 10 ^ oddCount n (k + 1) * n := by rw [ha]
    · have ha : oddCount n (k + 1) = oddCount n k + 1 := by
        simp [oddCount, he, x]
      have hnotone : x ≠ 1 := hnever k
      have hx3 : 3 ≤ x := by omega
      have hstep : 3 * (2 * shortcut x) ≤ 10 * x := by
        rw [double_shortcut x]
        simp [he]
        omega
      have hmult := Nat.mul_le_mul_left
        (3 ^ oddCount n k * 2 ^ k) hstep
      calc
        3 ^ oddCount n (k + 1) * 2 ^ (k + 1) *
            iter shortcut (k + 1) n =
            (3 ^ oddCount n k * 2 ^ k) *
              (3 * (2 * shortcut x)) := by
              rw [ha, iter_succ_last]
              simpa only [Nat.pow_succ] using
                odd_step_factors (3 ^ oddCount n k) (2 ^ k) (shortcut x)
        _ ≤ (3 ^ oddCount n k * 2 ^ k) * (10 * x) := hmult
        _ = 10 * (3 ^ oddCount n k * 2 ^ k *
            iter shortcut k n) := by
              dsimp [x]
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ ≤ 10 * (10 ^ oddCount n k * n) :=
          Nat.mul_le_mul_left 10 ih
        _ = 10 ^ (oddCount n k + 1) * n := by
          simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ = 10 ^ oddCount n (k + 1) * n := by rw [ha]

/-- A real positive period, with an actual no-1 future, has the
    exact upper multiplier bound 3^alpha*2^k <=10^alpha. -/
theorem nonterminal_period_multiplicative_upper_bound
    (n k : Nat)
    (hn : 0 < n)
    (hperiod : iter shortcut k n = n)
    (hnever : ∀ j : Nat, iter shortcut j n ≠ 1) :
    3 ^ oddCount n k * 2 ^ k ≤ 10 ^ oddCount n k := by
  have h := never_one_prefix_multiplicative_bound n k hnever
  have hm :
      (3 ^ oddCount n k * 2 ^ k) * n ≤
        (10 ^ oddCount n k) * n := by
    simpa only [hperiod] using h
  exact Nat.le_of_mul_le_mul_right hm hn

/-- Exact binary gap: a power of two exceeding 9 must be at least 16. -/
theorem power_two_above_nine_at_least_sixteen
    (k : Nat) (h : 9 < (2 : Nat) ^ k) :
    16 ≤ (2 : Nat) ^ k := by
  by_cases hk : k < 4
  · have hc : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 := by omega
    rcases hc with h0 | h1 | h2 | h3
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
  · have hsum : (k - 4) + 4 = k := by omega
    have heq : (2 : Nat) ^ k = (2 : Nat) ^ (k - 4) * 16 := by
      calc
        (2 : Nat) ^ k = 2 ^ ((k - 4) + 4) := by rw [hsum]
        _ = 2 ^ (k - 4) * 2 ^ 4 := Nat.pow_add _ _ _
        _ = 2 ^ (k - 4) * 16 := by simp
    have hp : 0 < (2 : Nat) ^ (k - 4) :=
      Nat.pow_pos (by decide)
    rw [heq]
    omega

/-- The binary gap above 81 jumps directly to 128. -/
theorem power_two_above_eighty_one_at_least_128
    (k : Nat) (h : 81 < (2 : Nat) ^ k) :
    128 ≤ (2 : Nat) ^ k := by
  by_cases hk : k < 7
  · have hc : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 ∨
      k = 4 ∨ k = 5 ∨ k = 6 := by omega
    rcases hc with h0 | h1 | h2 | h3 | h4 | h5 | h6
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
    · subst k
      simp at h
  · have hsum : (k - 7) + 7 = k := by omega
    have heq : (2 : Nat) ^ k = (2 : Nat) ^ (k - 7) * 128 := by
      calc
        (2 : Nat) ^ k = 2 ^ ((k - 7) + 7) := by rw [hsum]
        _ = 2 ^ (k - 7) * 2 ^ 7 := Nat.pow_add _ _ _
        _ = 2 ^ (k - 7) * 128 := by simp
    have hp : 0 < (2 : Nat) ^ (k - 7) :=
      Nat.pow_pos (by decide)
    rw [heq]
    omega

/-- Source-attached true nonterminal positive period with TWO odd
    steps is mathematically impossible, for arbitrary clock length k. -/
theorem never_one_positive_period_cannot_have_two_odds
    (n k : Nat)
    (hn : 0 < n) (hk : 0 < k)
    (hperiod : iter shortcut k n = n)
    (hnever : ∀ j : Nat, iter shortcut j n ≠ 1)
    (hodd : oddCount n k = 2) : False := by
  have upper := nonterminal_period_multiplicative_upper_bound
    n k hn hperiod hnever
  have hu : 9 * 2 ^ k ≤ 100 := by
    simpa [hodd] using upper
  have lower := positive_shortcut_cycle_strict_multiplier_defect
    n k hn hk hperiod
  have hl : 9 < 2 ^ k := by
    simpa [hodd] using lower
  have h16 := power_two_above_nine_at_least_sixteen k hl
  omega

/-- The same exact construction eliminates arbitrary period lengths
    with FOUR odd visits, not merely two. -/
theorem never_one_positive_period_cannot_have_four_odds
    (n k : Nat)
    (hn : 0 < n) (hk : 0 < k)
    (hperiod : iter shortcut k n = n)
    (hnever : ∀ j : Nat, iter shortcut j n ≠ 1)
    (hodd : oddCount n k = 4) : False := by
  have upper := nonterminal_period_multiplicative_upper_bound
    n k hn hperiod hnever
  have hu : 81 * 2 ^ k ≤ 10000 := by
    simpa [hodd] using upper
  have lower := positive_shortcut_cycle_strict_multiplier_defect
    n k hn hk hperiod
  have hl : 81 < 2 ^ k := by
    simpa [hodd] using lower
  have h128 := power_two_above_eighty_one_at_least_128 k hl
  omega

/-- A hypothetical least positive bad source has no terminal event
    anywhere in its ACTUAL original-source trajectory. -/
theorem minimal_positive_bad_never_hits_one
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ∀ i : Nat, iter shortcut i n ≠ 1 := by
  intro i hone
  exact hmin.1.2 ⟨i, Or.inl hone⟩

/-- A TRUE future period of the same hypothetical least positive bad
    original source can have neither TWO nor FOUR odd visits.
    This does not exclude all actual periods. -/
theorem least_positive_bad_future_period_not_two_or_four_odds
    {n : Nat}
    (hmin : MinimalBad PositiveBad n)
    (i k : Nat) (hk : 0 < k)
    (hperiod :
       iter shortcut k (iter shortcut i n) = iter shortcut i n) :
    oddCount (iter shortcut i n) k ≠ 2 ∧
    oddCount (iter shortcut i n) k ≠ 4 := by
  let x := iter shortcut i n
  have hx : 0 < x :=
    iter_positive shortcut shortcut_positive i n hmin.1.1
  have hnever : ∀ j, iter shortcut j x ≠ 1 := by
    intro j hhit
    have hmain : iter shortcut (i + j) n = 1 := by
      simpa only [x, iter_add] using hhit
    exact minimal_positive_bad_never_hits_one hmin (i + j) hmain
  constructor
  · intro h2
    exact never_one_positive_period_cannot_have_two_odds
      x k hx hk hperiod hnever h2
  · intro h4
    exact never_one_positive_period_cannot_have_four_odds
      x k hx hk hperiod hnever h4

#print axioms never_one_prefix_multiplicative_bound
#print axioms nonterminal_period_multiplicative_upper_bound
#print axioms power_two_above_nine_at_least_sixteen
#print axioms power_two_above_eighty_one_at_least_128
#print axioms never_one_positive_period_cannot_have_two_odds
#print axioms never_one_positive_period_cannot_have_four_odds
#print axioms minimal_positive_bad_never_hits_one
#print axioms least_positive_bad_future_period_not_two_or_four_odds

end SourceProduct
end CollatzFinal
