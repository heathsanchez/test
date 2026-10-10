import Collatz.InverseFibonacciBound

namespace CollatzFinal
namespace SourceProduct

/-!
V163 — INVERSE TERMINAL-COVERAGE HORIZON MASS CEILING.

This is a NONCIRCULAR quantitative theorem about the ACTUAL
shortcut inverse graph. V152 proved that EVERY exact t-step terminal
ancestor is among a list of <= B_t=F_{t+2} paths.

Here we prove a purely integer exponential ceiling
  3^t * v152FibonacciPathBudget t <= 6 * 5^t
for ALL t, using only the true even/odd inverse-branch restrictions.

At dyadic source cutoff 2^k, if a certificate is restricted to an
ACTUAL direct terminal hit in at most k steps, the number of possible
sources is <= budget k <= 6*(5/3)^k. Its relative coverage is <=
6*(5/6)^k and tends to ZERO, rather than one.

This is an exact NO-GO for one particular direct-terminal clock
budget (horizon = source bit length). It does NOT constrain longer
clocks, source-relative coalescence certificates, other proof grammars,
or global Collatz convergence. No terminal-tail hypothesis assumed.
-/

/-- The Fibonacci pair A,B satisfies A<=B<=2*A for all depths. -/
theorem v163_fibonacci_pair_ratio (t : Nat) :
    (v152FibonacciBounds t).1 <=
      (v152FibonacciBounds t).2 ∧
    (v152FibonacciBounds t).2 <=
      2 * (v152FibonacciBounds t).1 := by
  induction t with
  | zero => decide
  | succ t ih =>
      change
        (v152FibonacciBounds t).2 <=
          (v152FibonacciBounds t).1+(v152FibonacciBounds t).2 ∧
        (v152FibonacciBounds t).1+(v152FibonacciBounds t).2 <=
          2*(v152FibonacciBounds t).2
      omega

/-- The exponential base 5/3 strictly dominates the actual
    Fibonacci inverse-branch growth rate. -/
theorem v163_fibonacci_one_step_growth (t : Nat) :
    3 * (v152FibonacciBounds (t+2)).2 <=
    5 * (v152FibonacciBounds (t+1)).2 := by
  have hr := v163_fibonacci_pair_ratio t
  change
    3*((v152FibonacciBounds t).2 +
      ((v152FibonacciBounds t).1+(v152FibonacciBounds t).2)) <=
    5*((v152FibonacciBounds t).1+(v152FibonacciBounds t).2)
  omega

/-- Scaled Fibonacci ceiling with NO rational reals and no limits. -/
theorem v163_scaled_fibonacci_growth (t : Nat) :
    3^t * (v152FibonacciBounds (t+1)).2 <= 2*5^t := by
  induction t with
  | zero => decide
  | succ t ih =>
      have hg : 3*(v152FibonacciBounds (t+1+1)).2 <=
                5*(v152FibonacciBounds (t+1)).2 := by
        simpa [Nat.add_assoc] using v163_fibonacci_one_step_growth t
      calc
        3^(t+1) * (v152FibonacciBounds (t+1+1)).2 =
            3^t * (3*(v152FibonacciBounds (t+1+1)).2) := by
              simp [Nat.pow_succ,Nat.mul_assoc]
        _ <= 3^t * (5*(v152FibonacciBounds (t+1)).2) :=
          Nat.mul_le_mul_left _ hg
        _ = 5*(3^t*(v152FibonacciBounds (t+1)).2) := by ac_rfl
        _ <= 5*(2*5^t) := Nat.mul_le_mul_left 5 ih
        _ = 2*5^(t+1) := by
          simp [Nat.pow_succ,Nat.mul_assoc,Nat.mul_comm,
            Nat.mul_left_comm]

/-- Exact all-depth inverse population path budget: the sum over
    all direct terminal horizons 0..t has exponential rate below 2. -/
theorem v163_scaled_terminal_path_budget (t : Nat) :
    3^t * v152FibonacciPathBudget t <= 6*5^t := by
  induction t with
  | zero => decide
  | succ t ih =>
      have hb := v163_scaled_fibonacci_growth t
      calc
        3^(t+1)*v152FibonacciPathBudget (t+1) =
            3*(3^t*v152FibonacciPathBudget t) +
              6*(3^t*(v152FibonacciBounds (t+1)).2) := by
                simp [v152FibonacciPathBudget,Nat.pow_succ,
                  Nat.mul_add,Nat.mul_assoc,Nat.mul_comm,
                  Nat.mul_left_comm]
        _ <= 3*(6*5^t)+6*(2*5^t) :=
          Nat.add_le_add (Nat.mul_le_mul_left 3 ih)
            (Nat.mul_le_mul_left 6 hb)
        _ = 6*5^(t+1) := by
          simp [Nat.pow_succ]
          omega

/-- Exact ceiling on all reverse terminal paths with horizon t.
    Reuses V152's sound COMPLETE inverse lists and count comparison. -/
theorem v163_actual_terminal_path_scaled_ceiling (t : Nat) :
    3^t * v152TerminalPathBudget t <= 6*5^t := by
  calc
    3^t*v152TerminalPathBudget t <=
      3^t*v152FibonacciPathBudget t :=
        Nat.mul_le_mul_left _ (v152_terminal_path_budget_bounded t)
    _ <= 6*5^t := v163_scaled_terminal_path_budget t

/-- Elementary denominator-clearable inequality:
    6^4 >= 2*5^4. Repeating every four levels gains
    a factor >= 2 relative to 5^k. -/
theorem v163_four_step_exponential_separation (t : Nat) :
    2^t*5^(4*t) <= 6^(4*t) := by
  induction t with
  | zero => simp
  | succ t ih =>
      have hbase : (2:Nat)*5^4 <= 6^4 := by decide
      have h5 : 5^(4*(t+1))=5^(4*t)*5^4 := by
        have he : 4*(t+1)=4*t+4 := by omega
        rw [he,Nat.pow_add]
      have h6 : 6^(4*(t+1))=6^(4*t)*6^4 := by
        have he : 4*(t+1)=4*t+4 := by omega
        rw [he,Nat.pow_add]
      calc
        2^(t+1)*5^(4*(t+1)) =
          (2^t*5^(4*t))*(2*5^4) := by
            rw [h5,Nat.pow_succ]
            ac_rfl
        _ <= 6^(4*t)*(2*5^4) :=
          Nat.mul_le_mul_right _ ih
        _ <= 6^(4*t)*6^4 :=
          Nat.mul_le_mul_left _ hbase
        _ = 6^(4*(t+1)) := by rw [h6]

#print axioms v163_fibonacci_pair_ratio
#print axioms v163_fibonacci_one_step_growth
#print axioms v163_scaled_fibonacci_growth
#print axioms v163_scaled_terminal_path_budget
#print axioms v163_actual_terminal_path_scaled_ceiling
#print axioms v163_four_step_exponential_separation

end SourceProduct
end CollatzFinal
