import Collatz.PersistentOddPrefixBarrier

namespace CollatzFinal
namespace SourceProduct

/-!
V185 — MINIMUM SUFFICIENT ORIGINAL-SOURCE AFFINE MULTIPLIER.

The V184 fixed 25/8 odd-step upper factor discarded the original
source identity n. A real G5 187-cycle passes its high-odd
requirements INDEFINITELY. The protected future was therefore
not yet distinguished from an independently verified non-Collatz
countermodel.

The smallest lawful refinement RETAINS the exact +1 and the
unchanged original lower-bound source n at EVERY actual clock:

  For any real x>=n with x odd,
  2*n*T(x) = n*(3*x+1) <= (3*n+1)*x.

Consequently, IF every real prefix <=k remains >=n, then

  2^k*n^a*T^k(n) <= n*(3*n+1)^a,
  2^k*n^a <=(3*n+1)^a,  a=oddCount(n,k).

This no-longer requires a source height threshold OR a coarse
8-based factor; it is an exact integer all-source, all-clock
future-dependent theorem.

More importantly, if the exact second inequality FAILS for a
source and prefix length, Lean constructs a genuine POSITIVE
STRICTLY SMALLER original-source future meeting within that
prefix. This is a reusable, executable-consequence specification
rather than a new convergence oracle.

An explicit 27-clock signature of the independent G5 187-cycle
VIOLATES the true +1 inequality, while it satisfies V184's
coarse high-odd 3/5 necessity indefinitely. That is the
CERTIFIED separating distinction the Metalogic minimal repair
requires.

No all-source prefix-excess production is proved. In particular,
no theorem guarantees that any hypothetical least bad source
eventually violates the barrier. GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- The original positive source n must survive as a distinct
parameter. Collapsing n to 8 loses exactly the +1 discriminator. -/
theorem v185_actual_odd_source_factor
    (n x : Nat) (hSource : n<=x) (hOdd : x%2≠0) :
    2*n*shortcut x <= (3*n+1)*x := by
  have hStep : 2*shortcut x=3*x+1 := by
    simpa [hOdd] using double_shortcut x
  calc
    2*n*shortcut x = n*(2*shortcut x) := by ac_rfl
    _ = n*(3*x+1) := by rw [hStep]
    _ = 3*n*x+n := by
      simp only [Nat.mul_add,Nat.mul_one]
      ac_rfl
    _ <= 3*n*x+x := Nat.add_le_add_left hSource _
    _ = (3*n+1)*x := by
      simp only [Nat.add_mul,Nat.one_mul]
      ac_rfl

/-- Finite-clock source HEIGHT only: all real prefixes up to k must
stay above the ACTUAL ORIGINAL source n. No assumption about clocks
greater than k is made or needed. -/
theorem v185_source_exact_prefix_product (n : Nat) :
    ∀ k : Nat,
      (∀ t : Nat, t<=k → n<=iter shortcut t n) →
      2^k*n^(oddCount n k)*iter shortcut k n <=
        n*(3*n+1)^(oddCount n k) := by
  intro k
  induction k with
  | zero =>
      intro _
      simp [oddCount,iter]
  | succ k ih =>
      intro hProtected
      have hPrev : ∀ t : Nat, t<=k → n<=iter shortcut t n := by
        intro t ht
        exact hProtected t (by omega)
      have hIH := ih hPrev
      let x := iter shortcut k n
      have hx : n<=x := hProtected k (by omega)
      have hNext : iter shortcut (k+1) n=shortcut x := by
        dsimp [x]
        rw [iter_succ_last]
      by_cases hEven : x%2=0
      · have hOddCount :
          oddCount n (k+1)=oddCount n k := by
            simp [oddCount,hEven,x]
        have hStep :
            2*shortcut x=x :=
          v184_true_even_shortcut_identity x hEven
        calc
          2^(k+1)*n^(oddCount n (k+1))*
              iter shortcut (k+1) n =
            (2^k*n^(oddCount n k))*(2*shortcut x) := by
              rw [hNext,hOddCount]
              simp only [Nat.pow_succ]
              ac_rfl
          _ = 2^k*n^(oddCount n k)*x := by rw [hStep]
          _ <= n*(3*n+1)^(oddCount n k) := hIH
          _ = n*(3*n+1)^(oddCount n (k+1)) := by
              rw [hOddCount]
      · have hOddCount :
          oddCount n (k+1)=oddCount n k+1 := by
            simp [oddCount,hEven,x]
        have hStep :
            2*n*shortcut x <= (3*n+1)*x :=
          v185_actual_odd_source_factor n x hx hEven
        have hLift :
            (2^k*n^(oddCount n k))*(2*n*shortcut x) <=
              (2^k*n^(oddCount n k))*((3*n+1)*x) :=
          Nat.mul_le_mul_left _ hStep
        have hUpper :
            (2^k*n^(oddCount n k))*((3*n+1)*x) <=
              n*(3*n+1)^(oddCount n (k+1)) := by
          calc
            (2^k*n^(oddCount n k))*((3*n+1)*x) =
              (2^k*n^(oddCount n k)*x)*(3*n+1) := by ac_rfl
            _ <= (n*(3*n+1)^(oddCount n k))*(3*n+1) :=
              Nat.mul_le_mul_right _ hIH
            _ = n*(3*n+1)^(oddCount n (k+1)) := by
              rw [hOddCount]
              simp [Nat.pow_succ,Nat.mul_assoc]
        calc
          2^(k+1)*n^(oddCount n (k+1))*
              iter shortcut (k+1) n =
            (2^k*n^(oddCount n k))*(2*n*shortcut x) := by
              rw [hNext,hOddCount]
              simp only [Nat.pow_succ]
              ac_rfl
          _ <= (2^k*n^(oddCount n k))*((3*n+1)*x) := hLift
          _ <= n*(3*n+1)^(oddCount n (k+1)) := hUpper

/-- True natural-number cancellation with an explicit POSITIVE
original source. No hidden rational or negative source aliases. -/
theorem v185_positive_nat_source_cancel
    (A B n : Nat) (hn : 0<n) (h : A*n<=B*n) :
    A<=B := by
  apply Classical.byContradiction
  intro hNot
  have hGap : B+1<=A := by omega
  have hMul := Nat.mul_le_mul_right n hGap
  have hMul' : B*n+n<=A*n := by
    simpa [Nat.add_mul] using hMul
  omega

/-- Exact arithmetic NECESSARY condition for ANY source n>0 whose
genuine future has no smaller positive event until true clock k. -/
theorem v185_nondecreasing_prefix_source_exact_power
    (n k : Nat) (hn : 0<n)
    (hProtected : ∀ t : Nat, t<=k → n<=iter shortcut t n) :
    2^k*n^(oddCount n k) <=
      (3*n+1)^(oddCount n k) := by
  have hProduct := v185_source_exact_prefix_product n k hProtected
  have hLast : n<=iter shortcut k n :=
    hProtected k (Nat.le_refl k)
  have hLower :
      (2^k*n^(oddCount n k))*n <=
        (2^k*n^(oddCount n k))*iter shortcut k n :=
    Nat.mul_le_mul_left _ hLast
  have hTotal :
      (2^k*n^(oddCount n k))*n <=
        ((3*n+1)^(oddCount n k))*n := by
    calc
      (2^k*n^(oddCount n k))*n <=
        (2^k*n^(oddCount n k))*iter shortcut k n := hLower
      _ <= n*(3*n+1)^(oddCount n k) := by
        simpa only [Nat.mul_assoc] using hProduct
      _ = ((3*n+1)^(oddCount n k))*n := by ac_rfl
  exact v185_positive_nat_source_cancel _ _ n hn hTotal

/-- The exact +1 source coefficient signature must hold at EVERY
future clock for a hypothetical least bad natural number.
No arbitrary finite-clock or 8-source threshold is assumed. -/
theorem v185_least_bad_source_exact_all_clock_power
    (n k : Nat) (hBad : MinimalBad PositiveBad n) :
    2^k*n^(oddCount n k) <=
      (3*n+1)^(oddCount n k) := by
  have hProtected :
      ∀ t : Nat, t<=k → n<=iter shortcut t n := by
    intro t _
    exact minimal_positive_bad_never_below_source hBad t
  exact v185_nondecreasing_prefix_source_exact_power
    n k hBad.1.1 hProtected

/-- First-principles CONSEQUENCE compiler:
a source-attached exact odd-count coefficient excess at finite
clock k FORCES a genuine original-source DEScent by some true
clock t<=k; not a guessed descent time or unverified target. -/
theorem v185_source_exact_coefficient_excess_produces_descent
    (n k : Nat) (hn : 0<n)
    (hExcess :
      (3*n+1)^(oddCount n k) <
         2^k*n^(oddCount n k)) :
    ∃ t : Nat, t<=k ∧ 0<iter shortcut t n ∧
      iter shortcut t n<n := by
  have hExists : ∃ t : Nat, t<=k ∧ iter shortcut t n<n := by
    apply Classical.byContradiction
    intro hNo
    have hProtected :
        ∀ t : Nat, t<=k → n<=iter shortcut t n := by
      intro t ht
      apply Classical.byContradiction
      intro hNot
      have hLower : iter shortcut t n<n := by omega
      exact hNo ⟨t,ht,hLower⟩
    have hNecessary :=
      v185_nondecreasing_prefix_source_exact_power
        n k hn hProtected
    omega
  obtain ⟨t,ht,hLess⟩ := hExists
  have hPos : 0<iter shortcut t n :=
    v180_positive_iter n t hn
  exact ⟨t,ht,hPos,hLess⟩

/-- A genuine strictly earlier source and a source-faithful
two-clock FUTURE meeting are compiled from the same arithmetic
violation, without assuming that the earlier source converges. -/
theorem v185_source_exact_coefficient_excess_constructs_lower_meet
    (n k : Nat) (hn : 0<n)
    (hExcess :
      (3*n+1)^(oddCount n k) <
         2^k*n^(oddCount n k)) :
    ∃ p : Nat, 0<p ∧ p<n ∧ V155FutureMeet n p := by
  obtain ⟨t,_ht,hPos,hEarlier⟩ :=
    v185_source_exact_coefficient_excess_produces_descent
      n k hn hExcess
  exact ⟨iter shortcut t n,hPos,hEarlier,
         ⟨t,0,by simp [iter]⟩⟩

/-- Independent adversarial source187+5 CYCLE violates the
positive exact +1 multiplier condition at its 27-clock
return. G5 obeys the coarse V184 3/5 high-odd restriction
forever. Source-dependent +1 is the MINIMAL separator. -/
theorem v185_g5_cycle_187_arithmetic_exposes_missing_plus_one :
    (3*(187:Nat)+1)^17 < 2^27*187^17 := by
  decide

#print axioms v185_actual_odd_source_factor
#print axioms v185_source_exact_prefix_product
#print axioms v185_positive_nat_source_cancel
#print axioms v185_nondecreasing_prefix_source_exact_power
#print axioms v185_least_bad_source_exact_all_clock_power
#print axioms v185_source_exact_coefficient_excess_produces_descent
#print axioms v185_source_exact_coefficient_excess_constructs_lower_meet
#print axioms v185_g5_cycle_187_arithmetic_exposes_missing_plus_one

end SourceProduct
end CollatzFinal
