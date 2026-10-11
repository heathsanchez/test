import Collatz.MersenneUnboundedJointShadows

namespace CollatzFinal
namespace SourceProduct

/-!
V188 — SHARP UNIVERSAL TWO-CLOCK PREDECESSOR HEIGHT BARRIER.

For the TRUE +1 shortcut, every genuine one-clock step has
   2*(T(x)+1) <= 3*(x+1).
Odd steps ATTAIN equality; even steps are strict.

The verified all-clock consequence:
   2^j*(T^j(p)+1) <= 3^j*(p+1) for ALL Nat p,j.

The real Mersenne source n=2^K-1 has a certified all-odd
K-clock prefix:
   T^i(n)+1 = 3^i*2^(K-i), 0<=i<=K.

It follows for ANY real source p and ANY clocks 0<=j<=i<=K:
if T^j(p)=T^i(n), then p>=n.

This excludes an ENTIRE CATEGORY OF BAD PROOF SEARCH:
no smaller positive source can meet any of the initial K
genuine Mersenne endpoints unless its independent companion
clock is STRICTLY LATER than the original clock, or the original
orbit goes beyond K.

The theorem is a necessary clock-asymmetry obstruction, NOT
an actual Collatz convergence argument. Its sharpness comes
from equality along the original all-odd Mersenne trajectory.

GLOBAL COLLATZ UNKNOWN. NO QED.
-/

/-- The original +1 law alone gives the certified one-step
source-height lower bound for all genuine predecessors. -/
theorem v188_true_one_step_inverse_height (x : Nat) :
    2*(shortcut x + 1) <= 3*(x+1) := by
  have hD := double_shortcut x
  have hStep : 2*shortcut x <= 3*x+1 := by
    rw [hD]
    split <;> omega
  omega

/-- A genuine source/clock invariant. The inequality is
source-attached and TRUE for every natural source and clock;
it does not assume future convergence. -/
theorem v188_all_clock_inverse_height
    (p j : Nat) :
    2^j*(iter shortcut j p+1) <= 3^j*(p+1) := by
  induction j with
  | zero => simp [iter]
  | succ j ih =>
      have hStep :=
        v188_true_one_step_inverse_height
          (iter shortcut j p)
      have hScaled :
          2^j*(2*(shortcut(iter shortcut j p)+1)) <=
            2^j*(3*(iter shortcut j p+1)) :=
        Nat.mul_le_mul_left _ hStep
      have hIH :
          3*(2^j*(iter shortcut j p+1)) <=
            3*(3^j*(p+1)) :=
        Nat.mul_le_mul_left 3 ih
      calc
        2^(j+1)*(iter shortcut (j+1) p+1) =
          2^j*(2*(shortcut(iter shortcut j p)+1)) := by
            rw [iter_succ_last]
            simp only [Nat.pow_succ]
            ac_rfl
        _ <= 2^j*(3*(iter shortcut j p+1)) := hScaled
        _ = 3*(2^j*(iter shortcut j p+1)) := by ac_rfl
        _ <= 3*(3^j*(p+1)) := hIH
        _ = 3^(j+1)*(p+1) := by
            simp only [Nat.pow_succ]
            ac_rfl

/-- Exact REAL source-locked two-clock obstacle:
ANY meeting of p with a Mersenne's FIRST K endpoints with
independent companion clock j<=original clock i requires p
AT LEAST the original Mersenne source n=2^K-1.

This permits genuine earlier-source meetings only with j>i,
or after the original source has progressed beyond K.
Neither such meeting is assumed to exist. -/
theorem v188_mersenne_late_companion_clock_necessary
    (K i j p : Nat) (hi : i<=K) (hj : j<=i)
    (hMeet :
      iter shortcut j p = iter shortcut i (2^K-1)) :
    2^K-1 <= p := by
  have hKi : K=i+(K-i) := by omega
  have hIj : i=(i-j)+j := by omega
  have hPow2K : 2^K=2^i*2^(K-i) := by
    calc
      2^K=2^(i+(K-i)) := congrArg (fun v : Nat => 2^v) hKi
      _=2^i*2^(K-i) := Nat.pow_add 2 i (K-i)
  have hPow2i : 2^i=2^(i-j)*2^j := by
    calc
      2^i=2^((i-j)+j) := congrArg (fun v : Nat => 2^v) hIj
      _=2^(i-j)*2^j := Nat.pow_add 2 (i-j) j
  have hPow3i : 3^i=3^(i-j)*3^j := by
    calc
      3^i=3^((i-j)+j) := congrArg (fun v : Nat => 3^v) hIj
      _=3^(i-j)*3^j := Nat.pow_add 3 (i-j) j
  have hMersenneEndpoint :
      iter shortcut i (2^K-1)+1 =
        3^i*2^(K-i) := by
    rw [v182_mersenne_true_initial_prefix K i hi]
    have hpos : 0<3^i*2^(K-i) :=
      Nat.mul_pos (Nat.pow_pos (by decide))
        (Nat.pow_pos (by decide))
    omega
  have hBack :
      2^j*(3^i*2^(K-i)) <= 3^j*(p+1) := by
    calc
      2^j*(3^i*2^(K-i)) =
          2^j*(iter shortcut i (2^K-1)+1) := by
            rw [hMersenneEndpoint]
      _ = 2^j*(iter shortcut j p+1) := by rw [hMeet]
      _ <= 3^j*(p+1) := v188_all_clock_inverse_height p j
  have hPowGap : 2^(i-j)<=3^(i-j) :=
    v187_two_power_le_three_power (i-j)
  have hMultGap :
      (3^j*2^j*2^(K-i))*2^(i-j) <=
        (3^j*2^j*2^(K-i))*3^(i-j) :=
    Nat.mul_le_mul_left _ hPowGap
  have hLow :
      3^j*2^K <= 2^j*(3^i*2^(K-i)) := by
    calc
      3^j*2^K =
        (3^j*2^j*2^(K-i))*2^(i-j) := by
          rw [hPow2K,hPow2i]
          ac_rfl
      _ <= (3^j*2^j*2^(K-i))*3^(i-j) := hMultGap
      _ = 2^j*(3^i*2^(K-i)) := by
          rw [hPow3i]
          ac_rfl
  have hCombined : 3^j*2^K <=3^j*(p+1) :=
    Nat.le_trans hLow hBack
  have hThreePos : 0<3^j :=
    Nat.pow_pos (by decide)
  have hP : 2^K <= p+1 := by
    apply Classical.byContradiction
    intro hNo
    have hBound : p+2<=2^K := by omega
    have hScaled :=
      Nat.mul_le_mul_left (3^j) hBound
    have hExact :
        (3^j*(p+1))+3^j <= 3^j*2^K := by
      simpa only [Nat.mul_add,Nat.one_mul] using hScaled
    omega
  omega

/-- Source-ordered two-clock consequence: for a strictly smaller
candidate p to meet the Mersenne K-corridor by original clock
i<=K, it MUST pay the larger independent companion clock j>i.
This says NOTHING about whether such a clock exists. -/
theorem v188_source_lower_meeting_requires_clock_surplus
    (K i j p : Nat) (hi : i<=K)
    (hp : p < 2^K-1)
    (hMeet :
      iter shortcut j p=iter shortcut i (2^K-1)) :
    i<j := by
  apply Classical.byContradiction
  intro hNo
  have hj : j<=i := by omega
  have hLower :=
    v188_mersenne_late_companion_clock_necessary
      K i j p hi hj hMeet
  omega

#print axioms v188_true_one_step_inverse_height
#print axioms v188_all_clock_inverse_height
#print axioms v188_mersenne_late_companion_clock_necessary
#print axioms v188_source_lower_meeting_requires_clock_surplus

end SourceProduct
end CollatzFinal
