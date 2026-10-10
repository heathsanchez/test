import Collatz.ActualEpisode

namespace CollatzFinal
namespace SourceProduct

/-!
V167 — UNIVERSAL FIXED-CLOCK RANK OBSTRUCTION.

This is an unconditional arithmetic theorem about the ACTUAL
shortcut T(2x)=x, T(2x+1)=3x+2, NOT a Collatz counterexample.

For each proposed finite fixed horizon H, choose
n=2^(H+2)-1. The first H actual shortcut steps are along
the all-ones odd Mersenne corridor:
  T^j(n)=3^j*2^(H+2-j)-1 >=n>2  for 0<=j<=H.
Thus neither direct terminal nor strict numerical/source-size
descent can be guaranteed within a single UNIVERSAL fixed H.

The conclusion does not refute an unbounded source-dependent
clock, a certified earlier-source two-clock coalescence, or a
genuinely different non-size rank. V156 independently rules out
the stronger OLD V85 hypothesis of a later Live rank decrease
on every state because some states EXIT immediately.

This Lean theorem is the EXACT formal negative control
for V167 portfolio approach C. Global Collatz UNKNOWN.
-/

/-- A single exact odd step through the Mersenne corridor. -/
theorem v167_mersenne_corridor_step (j m : Nat) :
    shortcut (3^j*2^(m+1)-1) =
      3^(j+1)*2^m-1 := by
  have hPos : 0 < 3^j*2^m :=
    Nat.mul_pos (Nat.pow_pos (by decide))
      (Nat.pow_pos (by decide))
  simpa [Nat.pow_succ,Nat.mul_assoc,Nat.mul_comm,
    Nat.mul_left_comm] using
      (shortcut_two_mul_sub_one (z := 3^j*2^m) hPos)

/-- Arbitrarily many odd first steps of a real positive Nat source,
    with EXACT source clock and ordinary numeric values. -/
theorem v167_all_ones_real_prefix (j m : Nat) :
    iter shortcut j (2^(j+m)-1)=3^j*2^m-1 := by
  induction j generalizing m with
  | zero => simp [iter]
  | succ j ih =>
      have hEq : j+1+m = j+(m+1) := by omega
      rw [iter_succ_last,hEq,ih,v167_mersenne_corridor_step]

theorem v167_three_pow_at_least_two (j : Nat) :
    2^j <= 3^j := by
  induction j with
  | zero => decide
  | succ j ih =>
      simp only [Nat.pow_succ]
      omega

/-- Every all-ones corridor source fails strict source-size descent
    for all executed clocks up to its exposed odd run. -/
theorem v167_odd_corridor_no_numerical_descent (j m : Nat) :
    2^(j+m)-1 <=
      iter shortcut j (2^(j+m)-1) := by
  rw [v167_all_ones_real_prefix]
  have hBound :
      2^(j+m) <= 3^j*2^m := by
    rw [Nat.pow_add]
    exact Nat.mul_le_mul_right _ (v167_three_pow_at_least_two j)
  omega

/-- For EVERY finite H there exists a real positive source
    whose entire prefix through H NEVER strictly descends
    below its original source AND never hits {1,2}.
    This DOES NOT construct a divergent trajectory. -/
theorem v167_no_universal_fixed_horizon_size_exit (H : Nat) :
    ∃ n : Nat,
      2<n ∧
      ∀ j : Nat, j<=H →
        n <= iter shortcut j n ∧
        ¬ Terminal (iter shortcut j n) := by
  let n := 2^(H+2)-1
  have hp : 0 < 2^H := Nat.pow_pos (by decide)
  have hScale : 2^(H+2)=4*2^H := by
    rw [show H+2=2+H by omega, Nat.pow_add]
  have hn : 2<n := by
    dsimp [n]
    rw [hScale]
    omega
  refine ⟨n,hn,?_⟩
  intro j hj
  have hjm : j+(H+2-j)=H+2 := by omega
  have hNoDesc :
      n <= iter shortcut j n := by
    dsimp [n]
    simpa only [hjm] using
      (v167_odd_corridor_no_numerical_descent j (H+2-j))
  refine ⟨hNoDesc,?_⟩
  intro hTerminal
  rcases hTerminal with hOne | hTwo
  · omega
  · omega

#print axioms v167_mersenne_corridor_step
#print axioms v167_all_ones_real_prefix
#print axioms v167_three_pow_at_least_two
#print axioms v167_odd_corridor_no_numerical_descent
#print axioms v167_no_universal_fixed_horizon_size_exit

end SourceProduct
end CollatzFinal
