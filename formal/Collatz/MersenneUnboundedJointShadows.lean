import Collatz.MersenneJointResidualBarrier
import Collatz.JointProtectedFutureResidual

namespace CollatzFinal
namespace SourceProduct

/-!
V187 — REAL POSITIVE UNBOUNDED FINITE PREFIX SHADOWS.

This is an adversarial test of the V186 "protected future" constraints,
not Collatz QED and NOT a divergent positive source.

For any finite H, choose the genuine positive Mersenne original source
n=2^(H+1)-1. The first H real shortcut steps stay at least n and
have EVERY step odd, so all V184 high-odd requirements at 5r<=H
and all V185 exact source-specific +1 coefficient conditions hold.

No FIXED positive source is thereby shown to satisfy the property
for every horizon. Different H require different positive sources.

A separately source-locked exact CRT audit shows the stronger
specific integer family n_t=2^(21+2430t)-1, t>=0, escapes BOTH
the 205 V178 and 29 V180 certified reduction rule grammars.
That finite-bank modular claim is NOT silently asserted as a Lean
theorem here; the Lean proofs cover the universal genuine Mersenne
prefix facts and protected source-specific inequality.

This establishes an explicit nonvacuity negative control for
prospective finite-horizon elimination, identifying an essential
quantifier split. GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- Exact, elementary arithmetic positivity and order of the
two growth factors, with no stochastic parity assumption. -/
theorem v187_two_power_le_three_power (k : Nat) :
    2^k <= 3^k := by
  induction k with
  | zero => decide
  | succ k ih =>
      calc
        2^(k+1)=2^k*2 := by simp [Nat.pow_succ]
        _ <= 3^k*2 := Nat.mul_le_mul_right 2 ih
        _ <= 3^k*3 := Nat.mul_le_mul_left _ (by decide)
        _ = 3^(k+1) := by simp [Nat.pow_succ]

/-- Every genuine original-source Mersenne orbit stays at least its
original source over its ENTIRE initial all-odd finite corridor.
No statement after K clocks is made. -/
theorem v187_positive_mersenne_prefix_never_descends
    (K k : Nat) (hk : k<=K) :
    2^K-1 <= iter shortcut k (2^K-1) := by
  rw [v182_mersenne_true_initial_prefix K k hk]
  have hK : K=k+(K-k) := by omega
  have hPow : 2^K=2^k*2^(K-k) := by
    calc
      2^K=2^(k+(K-k)) := congrArg (fun v : Nat => 2^v) hK
      _=2^k*2^(K-k) := Nat.pow_add 2 k (K-k)
  have hMon :=
    Nat.mul_le_mul_right (2^(K-k))
      (v187_two_power_le_three_power k)
  rw [hPow]
  omega

/-- For EVERY chosen finite research clock horizon, a genuine
POSITIVE integer satisfies ALL of the protected never-descent,
ALL odd-step, and +1 coefficient conditions for that horizon.
This is not an immortal positive orbit. -/
theorem v187_each_finite_clock_has_positive_joint_shadow
    (H : Nat) :
    ∃ n : Nat, 0<n ∧
      (∀ k : Nat, k<=H →
        n<=iter shortcut k n ∧
        oddCount n k=k ∧
        2^k*n^k <= (3*n+1)^k) := by
  let K : Nat := H+1
  let n : Nat := 2^K-1
  have hPowPos : 0<2^H := Nat.pow_pos (by decide)
  have hn : 0<n := by
    dsimp [n,K]
    rw [Nat.pow_succ]
    omega
  refine ⟨n,hn,?_⟩
  intro k hk
  have hK : k<=K := by dsimp [K]; omega
  have hN : n<=iter shortcut k n := by
    dsimp [n]
    exact v187_positive_mersenne_prefix_never_descends K k hK
  have hO : oddCount n k=k := by
    dsimp [n]
    exact v182_mersenne_all_odd_count K k hK
  have hPrefix : ∀ t : Nat, t<=k →
       n<=iter shortcut t n := by
    intro t ht
    have htK : t<=K := by omega
    dsimp [n]
    exact v187_positive_mersenne_prefix_never_descends K t htK
  have hGuard :=
    v185_nondecreasing_prefix_source_exact_power n k hn hPrefix
  refine ⟨hN,hO,?_⟩
  simpa only [hO] using hGuard

/-- It is not enough to check that the first H genuine source
clocks do not descend. A valid future-closure theorem must account
for the change of SOURCE when the horizon grows. -/
theorem v187_each_clock_has_a_not_yet_descending_source
    (H : Nat) :
    ∃ n : Nat, 0<n ∧
      ∀ k : Nat, k<=H → n<=iter shortcut k n := by
  obtain ⟨n,hn,h⟩ :=
    v187_each_finite_clock_has_positive_joint_shadow H
  exact ⟨n,hn,fun k hk => (h k hk).1⟩

#print axioms v187_two_power_le_three_power
#print axioms v187_positive_mersenne_prefix_never_descends
#print axioms v187_each_finite_clock_has_positive_joint_shadow
#print axioms v187_each_clock_has_a_not_yet_descending_source

end SourceProduct
end CollatzFinal
