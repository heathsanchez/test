import Collatz.GuardedDyadicSwitch
import Collatz.Shortcut

namespace CollatzFinal.SourceProduct

/-- A conditional payment rule: the payment account is an explicit hypothesis. -/
theorem compensated_reserve_exhaustion
    (v H D : Nat → Nat) (g : Nat → Int)
    (hbalance : ∀ i, (v (i+1) : Int) = v i - D i + g i)
    (hpay : ∀ i, g i + H (i+1) - H i ≤ (D i : Int) - 1) : False := by
  have hdrop : ∀ i, v (i+1) + H (i+1) < v i + H i := by
    intro i
    have hb := hbalance i
    have hp := hpay i
    omega
  have hb : ∀ k, v k + H k + k ≤ v 0 + H 0 := by
    intro k
    induction k with
    | zero => omega
    | succ k ih =>
      have hd := hdrop k
      omega
  have hx := hb (v 0 + H 0 + 1)
  omega

theorem shortcut_three_eight_nine (z : Nat) (hz : 0 < z) :
    iter shortcut 3 (32*z-5) = 36*z-5 := by
  have h0 : shortcut (32*z-5) = 48*z-7 := by
    have hp : (32*z-5)%2 ≠ 0 := by omega
    simp only [shortcut, hp, ite_false]
    omega
  have h1 : shortcut (48*z-7) = 72*z-10 := by
    have hp : (48*z-7)%2 ≠ 0 := by omega
    simp only [shortcut, hp, ite_false]
    omega
  have h2 : shortcut (72*z-10) = 36*z-5 := by
    have hp : (72*z-10)%2 = 0 := by omega
    simp only [shortcut, hp, ite_true]
    omega
  simpa only [iter, h0, h1, h2]

/-- This is only the declared direct/quarter/M1 exit language. -/
def SimpleBlockProtected (n : Nat) : Prop :=
  ∀ j, j ≤ 3 →
    n ≤ iter shortcut j n ∧
    iter shortcut j n % 8 ≠ 5 ∧
    (iter shortcut j n % 3 = 2 →
      n ≤ (2 * iter shortcut j n - 1) / 3)

theorem plateau_block_protected (z : Nat) (hz : 0 < z) :
    SimpleBlockProtected (6912*z-5) := by
  have h0 : shortcut (6912*z-5) = 10368*z-7 := by
    have hp : (6912*z-5)%2 ≠ 0 := by omega
    simp only [shortcut, hp, ite_false]
    omega
  have h1 : shortcut (10368*z-7) = 15552*z-10 := by
    have hp : (10368*z-7)%2 ≠ 0 := by omega
    simp only [shortcut, hp, ite_false]
    omega
  have h2 : shortcut (15552*z-10) = 7776*z-5 := by
    have hp : (15552*z-10)%2 = 0 := by omega
    simp only [shortcut, hp, ite_true]
    omega
  intro j hj
  have hc : j=0 ∨ j=1 ∨ j=2 ∨ j=3 := by omega
  rcases hc with rfl | rfl | rfl | rfl <;>
    simp only [iter, h0, h1, h2] <;> omega

def PlateauCell (n : Nat) : Prop :=
  ∃ z : Nat, 0 < z ∧ n = 864*z-5

/-- Actual finite chains, with increasing endpoints and the named exit guards. -/
def PlateauRun : Nat → Nat → Prop
  | 0, n => PlateauCell n
  | r+1, n => PlateauCell n ∧ n < iter shortcut 3 n ∧
      SimpleBlockProtected n ∧ PlateauRun r (iter shortcut 3 n)

theorem arbitrarily_long_plateau (r z : Nat) (hz : 0 < z) :
    PlateauRun r (864 * (8^r*z) - 5) := by
  induction r generalizing z with
  | zero =>
    exact ⟨z, hz, by simp⟩
  | succ r ih =>
    let u := 8^r*z
    have hu : 0 < u := Nat.mul_pos (Nat.pow_pos (by decide)) hz
    have hn : 864*(8^(r+1)*z)-5 = 6912*u-5 := by
      dsimp [u]
      simp only [Nat.pow_succ, Nat.mul_assoc]
      omega
    have ht : iter shortcut 3 (6912*u-5) = 7776*u-5 := by
      have hh := shortcut_three_eight_nine (216*u) (by omega)
      simpa only [Nat.mul_assoc] using hh
    change PlateauCell _ ∧ _ ∧ _ ∧ _
    rw [hn, ht]
    refine ⟨⟨8*u, by omega, by omega⟩, by omega,
      plateau_block_protected u hu, ?_⟩
    have hi := ih (9*z) (by omega)
    have he : 864*(8^r*(9*z))-5 = 7776*u-5 := by
      dsimp [u]
      simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    rw [he] at hi
    exact hi

theorem plateau_reference_orders (z : Nat) (hz : 0 < z) :
    DyadicOrder (returnDefect 6561 2443 2048 (216*z-1 : Nat)) 1 ∧
    TernaryOrder (returnDefect 6561 2443 2048 (216*z-1 : Nat)) 2 := by
  have hc : ((216*z-1 : Nat) : Int) = 216*(z:Int)-1 := by omega
  rw [hc]
  constructor
  · refine ⟨1035-487404*(z:Int), ?_, ?_⟩
    · simp only [returnDefect, Int.mul_sub, Int.mul_one]
      omega
    · omega
  · refine ⟨230-108312*(z:Int), ?_, ?_⟩
    · simp only [returnDefect, Int.mul_sub, Int.mul_one]
      omega
    · omega

/-- Every cell has the same pair of fixed-reference orders. -/
theorem plateau_cell_orders (n : Nat) (hn : PlateauCell n) :
    DyadicOrder (returnDefect 6561 2443 2048 ((n+1)/4)) 1 ∧
    TernaryOrder (returnDefect 6561 2443 2048 ((n+1)/4)) 2 := by
  obtain ⟨z, hz, rfl⟩ := hn
  have he : (864*z-5+1)/4 = 216*z-1 := by omega
  rw [he]
  exact plateau_reference_orders z hz

/-- Any payment depending only on source and the two frozen orders is unchanged. -/
theorem frozen_order_payment_cannot_pay (H : Nat → Nat → Nat → Int)
    (source : Nat) : ¬ (3 + H source 1 2 - H source 1 2 ≤ (3:Int)-1) := by
  omega

#print axioms compensated_reserve_exhaustion
#print axioms shortcut_three_eight_nine
#print axioms plateau_block_protected
#print axioms arbitrarily_long_plateau
#print axioms plateau_reference_orders
#print axioms plateau_cell_orders
#print axioms frozen_order_payment_cannot_pay

end CollatzFinal.SourceProduct
