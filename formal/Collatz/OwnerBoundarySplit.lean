import Collatz.OwnerFourThirdsBoundary

namespace CollatzFinal
namespace SourceProduct

/-- General form of the V12 deficit-one squeeze.

On a hypothetical minimal bad path, if the actual odd count is exactly one
below qmin and has not exceeded the four-thirds source budget, then the
ordinary endpoint is strictly below twice the source.

Unlike the original V12 theorem this is not tied to the checkpoint k=2*n. -/
theorem minimal_bad_deficit_one_lt_double_of_three_q_le_four_n
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hqpos : 0 < oddCount n k)
    (hbudget : 3 * oddCount n k ≤ 4 * n)
    (hdef : oddCount n k + 1 = qmin k) :
    iter shortcut k n < 2 * n := by
  let q := oddCount n k
  let y := iter shortcut k n
  have hn : 0 < n := hmin.1.1
  have hqpos' : 0 < q := by simpa [q] using hqpos
  have htwq : 2 * q < 3 * n := by
    dsimp [q] at hbudget ⊢
    omega
  have hq3 : q < 3 * n := by omega
  have hrel :
      2 ^ k * n ^ q * y ≤
        (3 * n + 1) ^ q * n := by
    simpa [q, y] using
      source_relative_scaled_orbit_le hn
        (fun i _ => minimal_bad_nondescending_all_depths hmin i)
  have hratio :
      (3 * n + 1) ^ q * (3 * n - q) <
        (3 * n) ^ (q + 1) :=
    adjacent_power_ratio_lt (3 * n) q hqpos' hq3
  have hrelScaled :
      2 ^ k * n ^ q * y * (3 * n - q) ≤
        ((3 * n + 1) ^ q * n) * (3 * n - q) := by
    exact Nat.mul_le_mul_right (3 * n - q) hrel
  have hratioN :
      ((3 * n + 1) ^ q * n) * (3 * n - q) <
        (3 * n) ^ (q + 1) * n := by
    have hm := (Nat.mul_lt_mul_right hn).2 hratio
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hm
  have hqfail : 3 ^ q < 2 ^ k := by
    apply lt_qmin_fails
    rw [← hdef]
    omega
  have h3q :
      3 ^ (q + 1) < 3 * 2 ^ k := by
    have hm := (Nat.mul_lt_mul_right (by decide : 0 < 3)).2 hqfail
    simpa [Nat.pow_succ, Nat.mul_comm] using hm
  have hpowN :
      (3 * n) ^ (q + 1) * n =
        3 ^ (q + 1) * n ^ (q + 2) := by
    rw [Nat.mul_pow]
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hratioUpper :
      (3 * n) ^ (q + 1) * n <
        3 * 2 ^ k * n ^ (q + 2) := by
    rw [hpowN]
    have hp : 0 < n ^ (q + 2) := Nat.pow_pos hn
    have hm := (Nat.mul_lt_mul_right hp).2 h3q
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hm
  have hupper :
      2 ^ k * n ^ q * y * (3 * n - q) <
        3 * 2 ^ k * n ^ (q + 2) :=
    Nat.lt_of_le_of_lt hrelScaled
      (Nat.lt_trans hratioN hratioUpper)
  apply Classical.byContradiction
  intro hnot
  have hyge : 2 * n ≤ y := by
    dsimp [y] at hnot ⊢
    omega
  have hlin : 3 * n < 2 * (3 * n - q) := by
    omega
  have hlinN :
      3 * n * n < 2 * (3 * n - q) * n :=
    (Nat.mul_lt_mul_right hn).2 hlin
  have hyprod :
      3 * n * n < y * (3 * n - q) := by
    have hmono :
        (2 * n) * (3 * n - q) ≤ y * (3 * n - q) :=
      Nat.mul_le_mul_right (3 * n - q) hyge
    have hreorder :
        2 * (3 * n - q) * n =
          (2 * n) * (3 * n - q) := by
      simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    rw [hreorder] at hlinN
    exact Nat.lt_of_lt_of_le hlinN hmono
  have hfactor :
      0 < 2 ^ k * n ^ q :=
    Nat.mul_pos (Nat.pow_pos (by decide)) (Nat.pow_pos hn)
  have hlower0 :=
    (Nat.mul_lt_mul_left hfactor).2 hyprod
  have hlower :
      3 * 2 ^ k * n ^ (q + 2) <
        2 ^ k * n ^ q * y * (3 * n - q) := by
    have heq :
        (2 ^ k * n ^ q) * (3 * n * n) =
          3 * 2 ^ k * n ^ (q + 2) := by
      simp [Nat.pow_add, Nat.pow_succ, Nat.mul_assoc,
        Nat.mul_comm, Nat.mul_left_comm]
    rw [heq] at hlower0
    simpa [Nat.mul_assoc] using hlower0
  exact (Nat.lt_asymm hupper hlower)

/-- At the four-thirds boundary, the deficit-one + odd case has no remaining
owner-lift depth. Its odd endpoint is already the normalized owner core, and
that core lies in the narrow source interval [n,2*n).

This removes every lifted owner from the deficit-one residual. -/
theorem minimal_bad_four_thirds_deficit_one_normalized_core
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hq :
      oddCount n k = (4 * n) / 3)
    (hodd : iter shortcut k n % 2 = 1)
    (hdef :
      oddCount n k + 1 = qmin k) :
    ∃ p,
      n ≤ p ∧ p < 2 * n ∧
      0 < p ∧ p % 2 = 1 ∧ p % 8 ≠ 5 ∧
      iter shortcut k n = p := by
  have hn : 0 < n := hmin.1.1
  have hgt : 1 < n := by
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hbudget0 := (four_thirds_floor_boundary n).1
  have hbudget :
      3 * oddCount n k ≤ 4 * n := by
    rw [hq]
    exact hbudget0
  have hqpos : 0 < oddCount n k := by
    rw [hq]
    have hlower := source_le_four_thirds_floor hgt
    omega
  have hlt :
      iter shortcut k n < 2 * n :=
    minimal_bad_deficit_one_lt_double_of_three_q_le_four_n
      hmin hqpos hbudget hdef
  obtain ⟨r, p, hp, hpodd, hp5, hpn, hyform, hwaist, _⟩ :=
    minimal_bad_four_thirds_boundary_odd_owner_waist
      hmin hq hodd
  have hr0 : r = 0 := by
    rcases hwaist with hr | hlarge
    · exact hr
    · omega
  subst r
  have heq : iter shortcut k n = p := by
    simpa [ownerLift] using hyform
  exact ⟨p, hpn, by simpa [heq] using hlt, hp, hpodd, hp5, heq⟩

/-- Exact V17 odd-boundary split.

For a hypothetical minimal bad source, an odd four-thirds boundary endpoint
is either coefficient-surviving, or it is already a normalized odd core in
[n,2*n). No lifted-owner case remains on the deficit-one side. -/
theorem minimal_bad_four_thirds_odd_boundary_split
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hq :
      oddCount n k = (4 * n) / 3)
    (hodd : iter shortcut k n % 2 = 1) :
    qmin k ≤ oddCount n k ∨
      ∃ p,
        n ≤ p ∧ p < 2 * n ∧
        0 < p ∧ p % 2 = 1 ∧ p % 8 ≠ 5 ∧
        iter shortcut k n = p := by
  have hgt : 1 < n := by
    have hn : 0 < n := hmin.1.1
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hqpos : 0 < oddCount n k := by
    rw [hq]
    have hlower := source_le_four_thirds_floor hgt
    omega
  have hq2 : oddCount n k ≤ 2 * n := by
    rw [hq]
    exact Nat.le_trans
      (source_le_four_thirds_floor hgt)
      (by omega)
  rcases minimal_bad_persistent_survival_or_deficit_one
      hmin hqpos hq2 with hsurv | hdef
  · exact Or.inl hsurv
  · exact Or.inr
      (minimal_bad_four_thirds_deficit_one_normalized_core
        hmin hq hodd hdef)

#print axioms minimal_bad_deficit_one_lt_double_of_three_q_le_four_n
#print axioms minimal_bad_four_thirds_deficit_one_normalized_core
#print axioms minimal_bad_four_thirds_odd_boundary_split

end SourceProduct
end CollatzFinal
