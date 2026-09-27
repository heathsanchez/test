import Collatz.HardFirstCrossing

namespace CollatzFinal
namespace SourceProduct

/-- One odd shortcut step maps 2*b-1 exactly to 3*b-1. -/
theorem shortcut_two_mul_sub_one
    {b : Nat}
    (hb : 0 < b) :
    shortcut (2 * b - 1) = 3 * b - 1 := by
  unfold shortcut
  have hpar : (2 * b - 1) % 2 ≠ 0 := by
    omega
  simp only [hpar, ite_false]
  omega

/-- Closed all-odd tower: after m shortcut steps,
2^m*a-1 maps exactly to 3^m*a-1. -/
theorem iter_shortcut_oddTower :
    ∀ a m : Nat, 0 < a →
      iter shortcut m (2 ^ m * a - 1) = 3 ^ m * a - 1 := by
  intro a m ha
  induction m generalizing a with
  | zero =>
      simp [iter]
  | succ m ih =>
      change iter shortcut m
        (shortcut (2 ^ (m + 1) * a - 1)) =
        3 ^ (m + 1) * a - 1
      have hb : 0 < 2 ^ m * a :=
        Nat.mul_pos (Nat.pow_pos (by omega)) ha
      have htwo :
          2 ^ (m + 1) * a = 2 * (2 ^ m * a) := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      rw [htwo, shortcut_two_mul_sub_one hb]
      have hi := ih (3 * a) (by omega)
      simpa [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        using hi

/-- Any no-exit endpoint of exact form 3^m*a-1 forbids the matching
all-odd predecessor 2^m*a-1 from lying below the source. -/
theorem no_ordinary_exit_oddTower_source_ge
    {n a m : Nat}
    (hno : ¬ OrdinaryExit n (3 ^ m * a - 1))
    (ha : 0 < a)
    (hp : 0 < 2 ^ m * a - 1) :
    n ≤ 2 ^ m * a - 1 := by
  have hexact := iter_shortcut_oddTower a m ha
  apply Nat.le_of_not_gt
  intro hlt
  exact hno (Or.inr (Or.inr
    ⟨2 ^ m * a - 1, m, hp, hlt, hexact⟩))

/-- Closed 3-adic reverse barrier for an arbitrary endpoint.
If y+1=3^m*a, then the exact all-odd reverse source is 2^m*a-1;
on a no-exit orbit it must be at least n. -/
theorem no_ordinary_exit_threeAdic_barrier
    {n y a m : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hy : y + 1 = 3 ^ m * a)
    (ha : 0 < a)
    (hp : 0 < 2 ^ m * a - 1) :
    n ≤ 2 ^ m * a - 1 := by
  have htarget : y = 3 ^ m * a - 1 := by
    have hpos : 0 < 3 ^ m * a :=
      Nat.mul_pos (Nat.pow_pos (by omega)) ha
    omega
  rw [htarget] at hno
  exact no_ordinary_exit_oddTower_source_ge hno ha hp

/-- Quantitative form: a no-exit endpoint with m trailing ternary 2-digits
(y+1 divisible by 3^m) must be large enough that
(n+1)3^m <= 2^m(y+1). -/
theorem no_ordinary_exit_threeAdic_growth
    {n y a m : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hy : y + 1 = 3 ^ m * a)
    (ha : 0 < a)
    (hp : 0 < 2 ^ m * a - 1) :
    (n + 1) * 3 ^ m ≤ 2 ^ m * (y + 1) := by
  have hge := no_ordinary_exit_threeAdic_barrier hno hy ha hp
  have hna : n + 1 ≤ 2 ^ m * a := by
    omega
  calc
    (n + 1) * 3 ^ m ≤ (2 ^ m * a) * 3 ^ m :=
      Nat.mul_le_mul_right (3 ^ m) hna
    _ = 2 ^ m * (3 ^ m * a) := by
      simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    _ = 2 ^ m * (y + 1) := by rw [← hy]

/-- The same closed 3-adic growth barrier holds at every hard first-crossing
endpoint whenever the divisibility witness is supplied. -/
theorem hard_first_crossing_threeAdic_growth
    {n k a m : Nat}
    (hhard : HardFirstCrossing n k)
    (hy : iter shortcut (k + 1) n + 1 = 3 ^ m * a)
    (ha : 0 < a)
    (hp : 0 < 2 ^ m * a - 1) :
    (n + 1) * 3 ^ m ≤
      2 ^ m * (iter shortcut (k + 1) n + 1) := by
  exact no_ordinary_exit_threeAdic_growth hhard.2 hy ha hp

#print axioms shortcut_two_mul_sub_one
#print axioms iter_shortcut_oddTower
#print axioms no_ordinary_exit_oddTower_source_ge
#print axioms no_ordinary_exit_threeAdic_barrier
#print axioms no_ordinary_exit_threeAdic_growth
#print axioms hard_first_crossing_threeAdic_growth

end SourceProduct
end CollatzFinal
