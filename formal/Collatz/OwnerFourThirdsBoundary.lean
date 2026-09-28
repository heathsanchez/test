import Collatz.ProtectedFourThirds
import Collatz.FourThirdsBoundary
import Collatz.ValuationPullback
import Collatz.FixedOriginTransfer

namespace CollatzFinal
namespace SourceProduct

/-- The four-thirds floor already dominates the positive source. -/
theorem source_le_four_thirds_floor
    {n : Nat} (hn : 0 < n) :
    n ≤ (4 * n) / 3 := by
  have hdiv := Nat.mod_add_div (4 * n) 3
  have hmod := Nat.mod_lt (4 * n) (by decide : 0 < 3)
  omega

/-- Elementary dyadic domination used only to expose the frozen-source regime. -/
theorem succ_le_two_pow (k : Nat) :
    k + 1 ≤ 2 ^ k := by
  induction k with
  | zero =>
      decide
  | succ k ih =>
      rw [Nat.pow_succ]
      have hpos : 1 ≤ 2 ^ k := by omega
      omega

/-- At q=floor(4n/3), elapsed ordinary depth has already passed the source. -/
theorem four_thirds_boundary_depth_ge_source
    {n k : Nat}
    (hn : 0 < n)
    (hq : oddCount n k = (4 * n) / 3) :
    n ≤ k := by
  have hnQ := source_le_four_thirds_floor hn
  have hqk := oddCount_le_depth n k
  omega

/-- Therefore the source-product presentation is completely frozen at the
four-thirds boundary: no source tail or fresh source bit remains. -/
theorem four_thirds_boundary_source_frozen
    {n k : Nat}
    (hgt : 1 < n)
    (hq : oddCount n k = (4 * n) / 3) :
    (stateAt n k).tail = 0 ∧
    (stateAt n k).sourceResidue = n ∧
    (stateAt n k).endpointResidue = iter shortcut k n := by
  have hn : 0 < n := by omega
  have hnk : n ≤ k :=
    four_thirds_boundary_depth_ge_source hn hq
  have hkpow : k + 1 ≤ 2 ^ k := succ_le_two_pow k
  have hlt : n < 2 ^ k := by omega
  exact fixed_origin_state_collapse hn hlt

/-- The exact four-thirds slack is just the source residue modulo three. -/
theorem four_thirds_slack_eq_source_mod3 (n : Nat) :
    4 * n - 3 * ((4 * n) / 3) = n % 3 := by
  have hdiv := Nat.mod_add_div (4 * n) 3
  have hmod := four_mul_mod_three n
  omega

/-- A minimal bad source has only slack zero or one at the four-thirds floor. -/
theorem minimal_bad_four_thirds_slack_zero_or_one
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    4 * n - 3 * ((4 * n) / 3) = 0 ∨
    4 * n - 3 * ((4 * n) / 3) = 1 := by
  have hnot2 := minimal_bad_source_not_mod3_two hmin
  have hlt := Nat.mod_lt n (by decide : 0 < 3)
  have hslack := four_thirds_slack_eq_source_mod3 n
  omega

/-- V13's one-bit coefficient corridor is active at the four-thirds boundary. -/
theorem minimal_bad_four_thirds_boundary_corridor
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hq : oddCount n k = (4 * n) / 3) :
    qmin k ≤ oddCount n k ∨
      oddCount n k + 1 = qmin k := by
  have hn : 0 < n := hmin.1.1
  have hgt : 1 < n := by
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hqpos : 0 < oddCount n k := by
    rw [hq]
    have hnQ := source_le_four_thirds_floor hn
    omega
  have hq2 : oddCount n k ≤ 2 * n := by
    rw [hq]
    have hlt := four_thirds_floor_lt_double hgt
    omega
  exact minimal_bad_persistent_survival_or_deficit_one
    hmin hqpos hq2

/-- The single local statement that is sufficient for the corrected Crystal
cap: a protected state sitting exactly on q=floor(4n/3) cannot itself be odd. -/
def FourThirdsProtectedBoundaryEven : Prop :=
  ∀ n k, 1 < n →
    DirectQuarterProtectedPrefix n k →
    oddCount n k = (4 * n) / 3 →
    iter shortcut k n % 2 = 0

/-- Local boundary parity implies the whole protected-prefix four-thirds cap.
The proof is a literal induction on the odd counter: away from the boundary it
can rise by at most one; at the boundary the parity premise freezes it. -/
theorem four_thirds_protected_prefix_cap_of_boundary_even
    (hEven : FourThirdsProtectedBoundaryEven) :
    FourThirdsProtectedPrefixCap := by
  intro n k hgt hprot
  let Q := (4 * n) / 3
  have hqQ : oddCount n k ≤ Q := by
    revert hprot
    induction k with
    | zero =>
        intro _hprot
        simp [oddCount, Q]
    | succ k ih =>
        intro hprot
        have hprev : DirectQuarterProtectedPrefix n k := by
          intro i hi
          exact hprot i (by omega)
        have hprevQ : oddCount n k ≤ Q := ih hprev
        by_cases heq : oddCount n k = Q
        · have heven :
              iter shortcut k n % 2 = 0 :=
            hEven n k hgt hprev (by simpa [Q] using heq)
          simp only [oddCount, heven, ite_true]
          exact hprevQ
        · have hb := oddCount_succ_bounds n k
          omega
  have hfloor := four_thirds_floor_boundary n
  have hmul := Nat.mul_le_mul_left 3 hqQ
  dsimp [Q] at hmul
  omega

/-- Consequently the local parity theorem alone closes positive Collatz. -/
theorem reaches_one_of_four_thirds_protected_boundary_even
    (hEven : FourThirdsProtectedBoundaryEven) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_four_thirds_protected_prefix_cap
    (four_thirds_protected_prefix_cap_of_boundary_even hEven)

/-- Every owner lift contains its owner below it. -/
theorem owner_le_ownerLift (k p : Nat) :
    p ≤ ownerLift k p := by
  induction k with
  | zero =>
      simp [ownerLift]
  | succ k ih =>
      simp only [ownerLift]
      omega

/-- Exact owner-normal-form waist for a hypothetical odd boundary state.
Either the state is already an unlifted normalized core, or source anchoring
forces the lifted presentation strictly above the 4n protected band. -/
theorem minimal_bad_four_thirds_boundary_odd_owner_waist
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hq : oddCount n k = (4 * n) / 3)
    (hodd : iter shortcut k n % 2 = 1) :
    ∃ r p,
      0 < p ∧
      p % 2 = 1 ∧
      p % 8 ≠ 5 ∧
      n ≤ p ∧
      iter shortcut k n = ownerLift r p ∧
      (r = 0 ∨ 4 * n < iter shortcut k n) ∧
      ((shortcut p % 2 = 1) ∨
        (p % 8 = 1 ∧ shortcut p % 2 = 0 ∧
          iter shortcut 2 p % 2 = 1)) := by
  obtain ⟨r, p, hp, hpodd, hp5, hpn, horbit⟩ :=
    minimal_bad_odd_owner_core hmin hodd
  have hshape := owner_core_low_step hpodd hp5
  refine ⟨r, p, hp, hpodd, hp5, hpn, horbit, ?_, hshape⟩
  cases r with
  | zero =>
      exact Or.inl rfl
  | succ r =>
      right
      have howner : p ≤ ownerLift r p := owner_le_ownerLift r p
      rw [horbit, ownerLift]
      omega

/-- A minimal bad source itself is a normalized low-valuation core: residue
1 mod 8 would descend in two steps, and residue 5 mod 8 would expose a lower
owner immediately. -/
theorem minimal_bad_source_mod8_three_or_seven
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n % 8 = 3 ∨ n % 8 = 7 := by
  have hodd := positive_minimal_bad_odd hmin
  have hr :
      n % 8 = 1 ∨ n % 8 = 3 ∨ n % 8 = 5 ∨ n % 8 = 7 := by
    omega
  rcases hr with h1 | h3 | h5 | h7
  · have hn : 0 < n := hmin.1.1
    have hneven : n % 2 ≠ 0 := by omega
    have hstep1 : shortcut n = (3 * n + 1) / 2 := by
      unfold shortcut
      simp only [hneven, ite_false]
    have hstep1even : shortcut n % 2 = 0 := by
      rw [hstep1]
      omega
    have hstep2 :
        iter shortcut 2 n = (3 * n + 1) / 4 := by
      change shortcut (shortcut n) = _
      rw [hstep1]
      unfold shortcut
      simp only [hstep1even, ite_true]
    have hlt : iter shortcut 2 n < n := by
      rw [hstep2]
      omega
    have hnd := minimal_bad_nondescending_all_depths hmin 2
    omega
  · exact Or.inl h3
  · have hlt0 : iter shortcut 0 n < 4 * n + 1 := by
      simp [iter]
      omega
    have hnot5 :=
      minimal_bad_below_four_source_not_mod8_five
        (j := 0) hmin hlt0
    simp [iter, h5] at hnot5
  · exact Or.inr h7

/-- Combining source mod 3 and normalized owner shape leaves four source
classes modulo 24.  This is the finite source-side type carried into Crystal;
it is not a source census. -/
theorem minimal_bad_source_mod24_four_classes
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n % 24 = 3 ∨ n % 24 = 7 ∨
    n % 24 = 15 ∨ n % 24 = 19 := by
  have h8 := minimal_bad_source_mod8_three_or_seven hmin
  have hnot2 := minimal_bad_source_not_mod3_two hmin
  have h3lt := Nat.mod_lt n (by decide : 0 < 3)
  have h24lt := Nat.mod_lt n (by decide : 0 < 24)
  omega

#print axioms four_thirds_boundary_source_frozen
#print axioms minimal_bad_four_thirds_boundary_corridor
#print axioms four_thirds_protected_prefix_cap_of_boundary_even
#print axioms reaches_one_of_four_thirds_protected_boundary_even
#print axioms minimal_bad_four_thirds_boundary_odd_owner_waist
#print axioms minimal_bad_source_mod8_three_or_seven
#print axioms minimal_bad_source_mod24_four_classes

end SourceProduct
end CollatzFinal
