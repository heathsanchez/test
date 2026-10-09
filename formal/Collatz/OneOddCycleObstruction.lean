import Collatz.ParityCycleResidual

namespace CollatzFinal
namespace SourceProduct

/-!
V144 — UNBOUNDED-LENGTH EXCLUSION OF POSITIVE COLLatz CYCLES WITH
ZERO OR ONE ODD VISIT IN AN ACTUAL PERIOD.

For a true shortcut period T^k(n)=n, k>0, the exact source-affine
identity is 2^k*n=3^alpha*n+bias.

If alpha=0, the bias is 0; positivity forbids 2^k*n=n.
If alpha=1, exactly one odd visit occurs at some s<k. Exact bias
is then 2^s. The positive integer equation becomes
  (2^k-3)*n = 2^s.
The denominator (2^k-3) is ODD and positive, so as an integer divisor
of a pure power of 2 it MUST equal 1. Hence k=2 and n=2^s, s=0 or 1:
the existing terminal 1<->2 shortcut period.

Consequently any NONTERMINAL positive actual period requires at least
TWO odd steps, with no finite search horizon or source cap.

This closes an infinite CYCLE CLASS, but cannot exclude periods with
>=2 odd visits, nor unbounded no-merge positive orbits. NO COLLATZ QED.
-/

/-- An initial zero odd count forces the exact accumulated bias to zero. -/
theorem zero_odd_prefix_has_zero_bias
    (n k : Nat) (ho : oddCount n k = 0) :
    bias n k = 0 := by
  induction k with
  | zero => rfl
  | succ k ih =>
    by_cases he : iter shortcut k n % 2 = 0
    · have hprev : oddCount n k = 0 := by
        simpa [oddCount, he] using ho
      simpa [bias, he] using ih hprev
    · have hcontrad : oddCount n k + 1 = 0 := by
        simpa [oddCount, he] using ho
      omega

/-- If exactly one odd visit occurs in an actual k-step prefix, its
    location s is a genuine time coordinate and bias is precisely 2^s.
    No assumption that the odd step occurs at clock zero. -/
theorem one_odd_prefix_bias_is_power_two
    (n k : Nat) (ho : oddCount n k = 1) :
    ∃ s : Nat, s < k ∧ bias n k = 2 ^ s := by
  induction k with
  | zero =>
    simp [oddCount] at ho
  | succ k ih =>
    by_cases he : iter shortcut k n % 2 = 0
    · have hprev : oddCount n k = 1 := by
        simpa [oddCount, he] using ho
      obtain ⟨s, hs, hb⟩ := ih hprev
      refine ⟨s, by omega, ?_⟩
      simpa [bias, he] using hb
    · have hprev : oddCount n k = 0 := by
        have hh : oddCount n (k + 1) = oddCount n k + 1 := by
          simp [oddCount, he]
        omega
      have hb : bias n k = 0 :=
        zero_odd_prefix_has_zero_bias n k hprev
      refine ⟨k, by omega, ?_⟩
      simp [bias, he, hb]

/-- A positive ODD natural divisor of a pure 2-power is 1.
    Induction strips a factor 2 from the other positive factor,
    preserving exact integer arithmetic. -/
theorem odd_factor_in_power_two_is_one
    (d s : Nat) (hd : d % 2 = 1) :
    ∀ n : Nat, 0 < n → d * n = 2 ^ s → d = 1 := by
  induction s with
  | zero =>
    intro n hn he
    have hdiv : d ∣ 1 := ⟨n, by simpa using he.symm⟩
    exact Nat.dvd_one.mp hdiv
  | succ s ih =>
    intro n hn he
    have heven : (d * n) % 2 = 0 := by
      rw [he, Nat.pow_succ]
      omega
    have hneven : n % 2 = 0 := by
      rw [Nat.mul_mod, hd] at heven
      omega
    have hfactor : n = 2 * (n / 2) := by omega
    have hn2 : 0 < n / 2 := by omega
    have hhalf : d * (n / 2) = 2 ^ s := by
      have hscaled : 2 * (d * (n / 2)) = 2 * (2 ^ s) := by
        calc
          2 * (d * (n / 2)) = d * (2 * (n / 2)) := by
            simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
          _ = d * n := by rw [← hfactor]
          _ = 2 ^ (s + 1) := he
          _ = 2 * 2 ^ s := by simp [Nat.pow_succ, Nat.mul_comm]
      omega
    exact ih (n / 2) hn2 hhalf

/-- A nonzero positive natural period cannot contain ZERO odd steps. -/
theorem positive_period_cannot_have_zero_odd_visits
    (n k : Nat)
    (hn : 0 < n) (hk : 0 < k)
    (hp : iter shortcut k n = n)
    (hc : oddCount n k = 0) : False := by
  have hb := zero_odd_prefix_has_zero_bias n k hc
  have heq : 2 ^ k * n = n := by
    have h := exact_affine n k
    rw [hp, hc, hb] at h
    simpa using h
  have hpow : 2 ≤ (2 : Nat) ^ k := by
    have hr : k = (k - 1) + 1 := by omega
    rw [hr, Nat.pow_add]
    have hp2 : 0 < (2 : Nat) ^ (k - 1) :=
      Nat.pow_pos (by decide)
    change 2 ≤ 2 ^ (k - 1) * 2
    omega
  have hm : 2 * n ≤ 2 ^ k * n :=
    Nat.mul_le_mul_right n hpow
  omega

/-- Exactly ONE odd visit in a positive actual period forces that
    period to be terminal (1 or 2). No fixed period length is assumed;
    the unique odd clock s is preserved, rather than normalized away. -/
theorem positive_period_one_odd_visit_is_terminal
    (n k : Nat)
    (hn : 0 < n) (hk : 0 < k)
    (hp : iter shortcut k n = n)
    (hc : oddCount n k = 1) :
    Terminal n := by
  obtain ⟨s, hs, hb⟩ := one_odd_prefix_bias_is_power_two n k hc
  have hexact : 2 ^ k * n = 3 * n + 2 ^ s := by
    have h := exact_affine n k
    rw [hp, hc, hb] at h
    simpa using h
  have hcycle :
      3 ^ oddCount n k < 2 ^ k :=
    positive_shortcut_cycle_strict_multiplier_defect n k hn hk hp
  have hstrict : 3 < 2 ^ k := by
    simpa [hc] using hcycle
  have htwoeven : 2 ^ k % 2 = 0 := by
    cases k with
    | zero => omega
    | succ t =>
      rw [Nat.pow_succ]
      omega
  have hfactorodd : (2 ^ k - 3) % 2 = 1 := by omega
  have hsubadd : (2 ^ k - 3) + 3 = 2 ^ k := by omega
  have hcombined :
      (2 ^ k - 3) * n + 3 * n = 3 * n + 2 ^ s := by
    calc
      (2 ^ k - 3) * n + 3 * n =
          ((2 ^ k - 3) + 3) * n := by
            simp [Nat.add_mul]
      _ = 2 ^ k * n := by rw [hsubadd]
      _ = 3 * n + 2 ^ s := hexact
  have hfactor :
      (2 ^ k - 3) * n = 2 ^ s := by omega
  have hunit : 2 ^ k - 3 = 1 :=
    odd_factor_in_power_two_is_one (2 ^ k - 3) s
      hfactorodd n hn hfactor
  have hfour : 2 ^ k = 4 := by omega
  have hk_le : k ≤ 2 := by
    apply Classical.byContradiction
    intro hnot
    have hgt : 3 ≤ k := by omega
    have hr : k = (k - 3) + 3 := by omega
    have hpos : 0 < (2 : Nat) ^ (k - 3) :=
      Nat.pow_pos (by decide)
    rw [hr, Nat.pow_add] at hfour
    have hp3 : (2 : Nat) ^ 3 = 8 := by decide
    rw [hp3] at hfour
    omega
  have hk2 : k = 2 := by
    cases k with
    | zero => omega
    | succ k =>
      cases k with
      | zero =>
        simp at hfour
      | succ k => omega
  have hn2 : n = 2 ^ s := by
    rw [hunit] at hfactor
    simpa using hfactor
  have hs12 : s = 0 ∨ s = 1 := by omega
  change n = 1 ∨ n = 2
  rcases hs12 with h0 | h1
  · left
    rw [hn2, h0]
    decide
  · right
    rw [hn2, h1]
    decide

/-- A genuine nonterminal positive shortcut period has at least
    TWO actual odd visits, regardless of how large its period is. -/
theorem nonterminal_positive_period_requires_two_odd_visits
    (n k : Nat)
    (hn : 0 < n) (hk : 0 < k)
    (hp : iter shortcut k n = n)
    (hnotTerminal : ¬ Terminal n) :
    2 ≤ oddCount n k := by
  apply Classical.byContradiction
  intro hnot
  have hcases : oddCount n k = 0 ∨ oddCount n k = 1 := by omega
  rcases hcases with hzero | hone
  · exact positive_period_cannot_have_zero_odd_visits n k hn hk hp hzero
  · exact hnotTerminal
      (positive_period_one_odd_visit_is_terminal n k hn hk hp hone)

#print axioms zero_odd_prefix_has_zero_bias
#print axioms one_odd_prefix_bias_is_power_two
#print axioms odd_factor_in_power_two_is_one
#print axioms positive_period_cannot_have_zero_odd_visits
#print axioms positive_period_one_odd_visit_is_terminal
#print axioms nonterminal_positive_period_requires_two_odd_visits

end SourceProduct
end CollatzFinal
