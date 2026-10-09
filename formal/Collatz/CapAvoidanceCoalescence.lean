import Collatz.EarlyCoalescenceRegression

namespace CollatzFinal
namespace SourceProduct

/-- Exact 110 block. The quotient parameter is positive; subtraction is exact. -/
theorem guard_reclosure_step1 (u : Nat) (hu : 0 < u) :
    shortcut (8 * u - 5) = 12 * u - 7 := by
  have hp : (8 * u - 5) % 2 ≠ 0 := by omega
  simp only [shortcut, hp, ite_false]
  omega

theorem guard_reclosure_step2 (u : Nat) (hu : 0 < u) :
    shortcut (12 * u - 7) = 18 * u - 10 := by
  have hp : (12 * u - 7) % 2 ≠ 0 := by omega
  simp only [shortcut, hp, ite_false]
  omega

theorem guard_reclosure_step3 (u : Nat) (hu : 0 < u) :
    shortcut (18 * u - 10) = 9 * u - 5 := by
  have hp : (18 * u - 10) % 2 = 0 := by omega
  simp only [shortcut, hp, ite_true]
  omega

theorem guard_reclosure_block (u : Nat) (hu : 0 < u) :
    iter shortcut 3 (8 * u - 5) = 9 * u - 5 := by
  change shortcut (shortcut (shortcut (8 * u - 5))) = _
  rw [guard_reclosure_step1 u hu, guard_reclosure_step2 u hu,
      guard_reclosure_step3 u hu]

/-- Exact unrestricted-length corridor, not a claim of an infinite natural orbit. -/
theorem guard_reclosure_corridor (r q : Nat) (hq : 0 < q) :
    iter shortcut (3 * r) (8 ^ r * q - 5) = 9 ^ r * q - 5 := by
  induction r generalizing q with
  | zero => simp [iter]
  | succ r ih =>
    let u := 8 ^ r * q
    have hu : 0 < u := Nat.mul_pos (Nat.pow_pos (by decide)) hq
    have hstart : 8 ^ (r + 1) * q = 8 * u := by
      simp [u, Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm]
    have hnext : 9 * u = 8 ^ r * (9 * q) := by
      simp [u, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    have htime : 3 * (r + 1) = 3 + 3 * r := by omega
    rw [htime, iter_add, hstart, guard_reclosure_block u hu, hnext]
    rw [ih (9 * q) (by omega)]
    simp [Nat.pow_succ, Nat.mul_assoc]

/-- Every ternary endpoint in one such block stays above the ORIGINAL source cap. -/
theorem guard_reclosure_block_cap
    (n u k : Nat) (hu : 0 < u) (hn : n ≤ 8 * u - 5)
    (hm : (8 * u - 5) % 3 ≠ 2) (hk : k ≤ 3)
    (hy : (iter shortcut k (8 * u - 5)) % 3 = 2) :
    3 * n ≤ 2 * iter shortcut k (8 * u - 5) - 1 := by
  have hc : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 := by omega
  rcases hc with hc | hc | hc | hc
  · subst k
    exact False.elim (hm hy)
  · subst k
    change 3 * n ≤ 2 * shortcut (8 * u - 5) - 1
    rw [guard_reclosure_step1 u hu]
    omega
  · subst k
    change 3 * n ≤ 2 * shortcut (shortcut (8 * u - 5)) - 1
    rw [guard_reclosure_step1 u hu, guard_reclosure_step2 u hu]
    omega
  · subst k
    rw [guard_reclosure_block u hu] at hy
    omega

/-- All finite corridor lengths, with the source fixed THROUGHOUT the prefix. -/
theorem guard_reclosure_no_cap
    (r q n : Nat) (hq : 0 < q) (hn : n ≤ 8 ^ r * q - 5)
    (hm : (8 ^ r * q - 5) % 3 ≠ 2) :
    ∀ k, k ≤ 3 * r → (iter shortcut k (8 ^ r * q - 5)) % 3 = 2 →
      3 * n ≤ 2 * iter shortcut k (8 ^ r * q - 5) - 1 := by
  induction r generalizing q n with
  | zero =>
    intro k hk hy
    have hk0 : k = 0 := by omega
    subst k
    exact False.elim (hm hy)
  | succ r ih =>
    let u := 8 ^ r * q
    have hu : 0 < u := Nat.mul_pos (Nat.pow_pos (by decide)) hq
    have hstart : 8 ^ (r + 1) * q = 8 * u := by
      simp [u, Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm]
    have hnext : 9 * u = 8 ^ r * (9 * q) := by
      simp [u, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    have hn0 : n ≤ 8 * u - 5 := by simpa only [hstart] using hn
    have hm0 : (8 * u - 5) % 3 ≠ 2 := by simpa only [hstart] using hm
    have hn1 : n ≤ 8 ^ r * (9 * q) - 5 := by
      rw [← hnext]
      omega
    have hm1 : (8 ^ r * (9 * q) - 5) % 3 ≠ 2 := by
      rw [← hnext]
      omega
    have ht := ih (9 * q) n (by omega) hn1 hm1
    intro k hk hy
    by_cases hshort : k ≤ 3
    · simpa only [hstart] using
        (guard_reclosure_block_cap n u k hu hn0 hm0 hshort
          (by simpa only [hstart] using hy))
    · have hkstep : k = 3 + (k - 3) := by omega
      have hklimit : k - 3 ≤ 3 * r := by omega
      have hpath : iter shortcut k (8 ^ (r + 1) * q - 5) =
          iter shortcut (k - 3) (8 ^ r * (9 * q) - 5) := by
        calc
          iter shortcut k (8 ^ (r + 1) * q - 5) =
              iter shortcut (3 + (k - 3)) (8 ^ (r + 1) * q - 5) :=
            congrArg (fun z => iter shortcut z (8 ^ (r + 1) * q - 5)) hkstep
          _ = iter shortcut (k - 3) (8 ^ r * (9 * q) - 5) := by
            rw [iter_add, hstart, guard_reclosure_block u hu, hnext]
      rw [hpath] at hy ⊢
      exact ht (k - 3) hklimit hy

/-- No capped one-predecessor hit for the whole corridor, but a genuine
EARLIER-SOURCE coalescence via the existing ten-step reverse constructor. -/
theorem guard_reclosure_no_cap_but_merged
    (r q t : Nat) (hq : 0 < q)
    (hsource : 8 ^ r * q - 5 = 273 + 1458 * t) :
    LowerMerge shortcut (8 ^ r * q - 5) (191 + 1024 * t) ∧
    (∀ k, k ≤ 3 * r → (iter shortcut k (8 ^ r * q - 5)) % 3 = 2 →
      3 * (8 ^ r * q - 5) ≤ 2 * iter shortcut k (8 ^ r * q - 5) - 1) := by
  constructor
  · rw [hsource]
    exact v113_a_source_merge t
  · apply guard_reclosure_no_cap r q (8 ^ r * q - 5) hq (Nat.le_refl _)
    rw [hsource]
    omega

#print axioms guard_reclosure_corridor
#print axioms guard_reclosure_no_cap
#print axioms guard_reclosure_no_cap_but_merged

/-- Use the short multiplicative period of 8 modulo 729. -/
theorem guard_reclosure_lift_mod (r : Nat) :
    ((8 ^ 162) ^ r) % 729 = 1 := by
  have hperiod : (8 : Nat) ^ 162 % 729 = 1 := by decide
  induction r with
  | zero => decide
  | succ r ih =>
    rw [Nat.pow_succ, Nat.mul_mod, ih, hperiod]

/-- Keep powers symbolic so simplification never unfolds a large fixed exponent. -/
theorem guard_reclosure_power_product (a b r : Nat) :
    (a * b) ^ r = a ^ r * b ^ r := by
  induction r with
  | zero => simp
  | succ r ih =>
    simp only [Nat.pow_succ, ih, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem guard_reclosure_lift_factor (r : Nat) :
    8 ^ r * (278 * (8 ^ 161) ^ r) = 278 * (8 ^ 162) ^ r := by
  have hstep : (8 : Nat) * 8 ^ 161 = 8 ^ 162 := by decide
  have hproduct := guard_reclosure_power_product 8 (8 ^ 161) r
  rw [hstep] at hproduct
  calc
    8 ^ r * (278 * (8 ^ 161) ^ r) = 278 * (8 ^ r * (8 ^ 161) ^ r) := by
      simp only [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    _ = 278 * (8 ^ 162) ^ r := by rw [← hproduct]

/-- EVERY finite horizon has a positive source with no capped ternary hit
through that horizon, yet a known smaller positive coalescent. Finite cap
avoidance is therefore not the full no-merger hypothesis. No positive
infinite cap-avoiding orbit is asserted. -/
theorem arbitrary_cap_avoidance_with_lower_merge (H : Nat) :
    ∃ n p : Nat, 0 < p ∧ LowerMerge shortcut n p ∧
      (∀ k, k ≤ H → (iter shortcut k n) % 3 = 2 →
        3 * n ≤ 2 * iter shortcut k n - 1) := by
  let q := 278 * (8 ^ 161) ^ H
  let n := 8 ^ H * q - 5
  have hq : 0 < q := Nat.mul_pos (by decide) (Nat.pow_pos (by decide))
  have hfactor : n = 278 * (8 ^ 162) ^ H - 5 := by
    dsimp [n, q]
    rw [guard_reclosure_lift_factor H]
  have hmod := guard_reclosure_lift_mod H
  have hpower : 0 < (8 ^ 162) ^ H := Nat.pow_pos (by decide)
  have hnmod : n % 1458 = 273 := by rw [hfactor]; omega
  let t := (n - 273) / 1458
  have hnfamily : n = 273 + 1458 * t := by dsimp [t]; omega
  have hboth := guard_reclosure_no_cap_but_merged H q t hq hnfamily
  refine ⟨n, 191 + 1024 * t, by omega, hboth.1, ?_⟩
  intro k hk hy
  exact hboth.2 k (by omega) hy

#print axioms arbitrary_cap_avoidance_with_lower_merge

end SourceProduct
end CollatzFinal
