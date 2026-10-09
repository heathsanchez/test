import Collatz.ReducedThreePowerCharts

namespace CollatzFinal

/-!
V137 — CLOSED INTEGER MULTIPLIER SEARCH AT FIXED TWO-CLOCK CHARTS.

Previous V135/V136 proved *sufficient* ways to match the two affine
endpoint slopes:
  3^alpha * u = 3^beta * v,
with original-source offset domination:
  2^j * v <= 2^i * u.

This file proves two exact converses:
1. Every positive integer solution is a positive multiple of the
   reduced pair (3^(beta-alpha),3^(alpha-beta)); there are NO
   other integer multiplier shapes.
2. Such positive matched coefficients with the domination property
   exist IFF the single weighted-clock orientation holds:
      2^j * 3^alpha <= 2^i * 3^beta.

Thus the coefficient-search residual is mathematically EMPTY:
any failure of the fixed-clock inequality is a true obstruction to
this *chart grammar*, not an unresolved search depth. It does NOT
imply that the Collatz source is divergent; search must change clocks,
base join, or semantic constructor.

No universal Collatz proof.
-/

private theorem three_pow_positive (k : Nat) :
    0 < (3 : Nat) ^ k := by
  induction k with
  | zero => decide
  | succ k ih =>
      rw [Nat.pow_succ]
      exact Nat.mul_pos ih (by decide)

private theorem three_pow_split
    (a b : Nat) (hab : a <= b) :
    3 ^ b = 3 ^ a * 3 ^ (b-a) := by
  calc
    3 ^ b = 3 ^ (a + (b-a)) := by
      congr 1
      omega
    _ = 3 ^ a * 3 ^ (b-a) :=
      Nat.pow_add 3 a (b-a)

/-- An exact INTEGER normal form for every positive pair of matched
affine endpoint multipliers. The primitive pair is forced up to one
common positive parameter; no other multipliers can repair a failed
fixed-clock weighted orientation. -/
theorem positive_three_power_matching_normal_form
    (alpha beta u v : Nat)
    (hu : 0 < u) (hv : 0 < v)
    (hmatch : 3 ^ alpha * u = 3 ^ beta * v) :
    ∃ t : Nat,
       0 < t ∧
       u = 3 ^ (beta-alpha) * t ∧
       v = 3 ^ (alpha-beta) * t := by
  by_cases h : alpha <= beta
  · have hp : 3 ^ beta = 3 ^ alpha * 3 ^ (beta-alpha) :=
      three_pow_split alpha beta h
    have hc :
        3 ^ alpha * u =
        3 ^ alpha * (3 ^ (beta-alpha) * v) := by
      calc
        3 ^ alpha * u = 3 ^ beta * v := hmatch
        _ = (3 ^ alpha * 3 ^ (beta-alpha)) * v := by rw [hp]
        _ = 3 ^ alpha * (3 ^ (beta-alpha) * v) := by
          rw [Nat.mul_assoc]
    have hfactor : u = 3 ^ (beta-alpha) * v :=
      Nat.eq_of_mul_eq_mul_left (three_pow_positive alpha) hc
    have hzero : alpha-beta=0 := by omega
    refine ⟨v,hv,hfactor,?_⟩
    simp [hzero]
  · have hle : beta <= alpha := by omega
    have hp : 3 ^ alpha = 3 ^ beta * 3 ^ (alpha-beta) :=
      three_pow_split beta alpha hle
    have hc :
        3 ^ beta * (3 ^ (alpha-beta) * u) =
        3 ^ beta * v := by
      calc
        3 ^ beta * (3 ^ (alpha-beta) * u) =
          (3 ^ beta * 3 ^ (alpha-beta)) * u := by
            rw [Nat.mul_assoc]
        _ = 3 ^ alpha * u := by rw [hp]
        _ = 3 ^ beta * v := hmatch
    have hfactor : 3 ^ (alpha-beta) * u = v :=
      Nat.eq_of_mul_eq_mul_left (three_pow_positive beta) hc
    have hzero : beta-alpha=0 := by omega
    refine ⟨u,hu,?_,?_⟩
    · simp [hzero]
    · exact hfactor.symm

/-- THE missing necessity. If any positive integer coefficient pair
satisfies endpoint matching AND the original-source domination
guard, then the weighted-clock inequality is forced.
Proof cancels the POSITIVE actual integer multiplier, not a
real-valued asymptotic approximation. -/
theorem weighted_clock_guard_necessary
    (alpha beta i j u v : Nat)
    (hu : 0 < u)
    (hmatch : 3 ^ alpha * u = 3 ^ beta * v)
    (hdominate : 2 ^ j * v <= 2 ^ i * u) :
    2 ^ j * 3 ^ alpha <= 2 ^ i * 3 ^ beta := by
  have hscaled :
      3 ^ beta * (2 ^ j * v) <=
      3 ^ beta * (2 ^ i * u) :=
    Nat.mul_le_mul_left (3 ^ beta) hdominate
  have hmult :
      (2 ^ j * 3 ^ alpha) * u <=
      (2 ^ i * 3 ^ beta) * u := by
    calc
      (2 ^ j * 3 ^ alpha) * u =
          2 ^ j * (3 ^ alpha * u) := by
            simp [Nat.mul_assoc]
      _ = 2 ^ j * (3 ^ beta * v) := by rw [hmatch]
      _ = 3 ^ beta * (2 ^ j * v) := by
            simp [Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]
      _ <= 3 ^ beta * (2 ^ i * u) := hscaled
      _ = (2 ^ i * 3 ^ beta) * u := by
            simp [Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]
  exact Nat.le_of_mul_le_mul_right hmult hu

/-- An EXACT equivalence at FIXED two clocks: a compatible positive
integer affine source coefficient pair exists iff the weighted guard
holds. The V135 cross-power construction proves sufficiency; the
new cancellation lemma proves necessity. -/
theorem matching_coefficients_exist_iff_weighted_clock
    (alpha beta i j : Nat) :
    (∃ u v : Nat,
       0 < u ∧ 0 < v ∧
       3 ^ alpha * u = 3 ^ beta * v ∧
       2 ^ j * v <= 2 ^ i * u) ↔
    2 ^ j * 3 ^ alpha <= 2 ^ i * 3 ^ beta := by
  constructor
  · rintro ⟨u,v,hu,_hv,hm,hd⟩
    exact weighted_clock_guard_necessary alpha beta i j u v hu hm hd
  · intro h
    refine ⟨3 ^ beta,3 ^ alpha,
            three_pow_positive beta,three_pow_positive alpha,?_,h⟩
    exact Nat.mul_comm _ _

/-- Instantiate the general iff with the real shortcut odd counts
of any two base charts; this is the complete coefficient-admission
interface that the ROS controller can safely consume. -/
theorem actual_chart_coefficients_iff_weighted_clock
    (a p i j : Nat) :
    (∃ u v : Nat,
       0 < u ∧ 0 < v ∧
       3 ^ SourceProduct.oddCount a i * u =
          3 ^ SourceProduct.oddCount p j * v ∧
       2 ^ j * v <= 2 ^ i * u) ↔
    2 ^ j * 3 ^ SourceProduct.oddCount a i <=
       2 ^ i * 3 ^ SourceProduct.oddCount p j :=
  matching_coefficients_exist_iff_weighted_clock
    (SourceProduct.oddCount a i)
    (SourceProduct.oddCount p j)
    i j

/-- One clock-phase diagnostic (5,3) is exact and exhaustive for ALL
positive affine multiplier pairs. The source5↔3 base collision
is real, but the specific clocks (3,8) admit NO valid nonexpanding
full-offset chart, however large a multiplier search budget is. -/
theorem source5_bad_clocks_have_no_chart_coefficients :
    ¬ ∃ u v : Nat,
       0 < u ∧ 0 < v ∧
       3 ^ SourceProduct.oddCount 5 3 * u =
          3 ^ SourceProduct.oddCount 3 8 * v ∧
       2 ^ 8 * v <= 2 ^ 3 * u := by
  intro h
  have hguard :=
    (actual_chart_coefficients_iff_weighted_clock 5 3 3 8).mp h
  have hbad :
      2 ^ 3 * 3 ^ SourceProduct.oddCount 3 8 <
      2 ^ 8 * 3 ^ SourceProduct.oddCount 5 3 := by decide
  exact (Nat.not_le_of_gt hbad) hguard

/-- The SAME true source pair at the earlier clocks (1,2) admits
positive coefficients, so clock choice is semantically consequential.
This does not force Collatz for arbitrary other source pairs. -/
theorem source5_good_clocks_admit_chart_coefficients :
    ∃ u v : Nat,
       0 < u ∧ 0 < v ∧
       3 ^ SourceProduct.oddCount 5 1 * u =
          3 ^ SourceProduct.oddCount 3 2 * v ∧
       2 ^ 2 * v <= 2 ^ 1 * u := by
  apply (actual_chart_coefficients_iff_weighted_clock 5 3 1 2).mpr
  decide

#print axioms positive_three_power_matching_normal_form
#print axioms weighted_clock_guard_necessary
#print axioms matching_coefficients_exist_iff_weighted_clock
#print axioms actual_chart_coefficients_iff_weighted_clock
#print axioms source5_bad_clocks_have_no_chart_coefficients
#print axioms source5_good_clocks_admit_chart_coefficients

end CollatzFinal
