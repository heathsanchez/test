import Collatz.AssembledConstructorCloseout

namespace CollatzFinal
namespace SourceProduct

/-- Repeated source lift underlying the valuation-pullback constructor.
Closed form: ownerLift k p = 4^k*p + (4^k-1)/3. -/
def ownerLift : Nat → Nat → Nat
  | 0, p => p
  | k + 1, p => 4 * ownerLift k p + 1

theorem ownerLift_odd
    {p : Nat} (hpodd : p % 2 = 1) :
    ∀ k, ownerLift k p % 2 = 1 := by
  intro k
  induction k with
  | zero => simpa [ownerLift] using hpodd
  | succ k =>
      change (4 * ownerLift k p + 1) % 2 = 1
      omega

/-- One lift layer adds exactly two redundant shortcut steps:
three steps from 4*x+1 coalesce with one step from odd x. -/
theorem iter_three_four_mul_add_one
    {x : Nat} (hxodd : x % 2 = 1) :
    iter shortcut 3 (4 * x + 1) = shortcut x := by
  have hxne : x % 2 ≠ 0 := by omega
  have h1 : shortcut (4 * x + 1) = 6 * x + 2 := by
    unfold shortcut
    have ho : (4 * x + 1) % 2 ≠ 0 := by omega
    simp only [ho, ite_false]
    omega
  have h2 : shortcut (6 * x + 2) = 3 * x + 1 := by
    unfold shortcut
    have he : (6 * x + 2) % 2 = 0 := by omega
    simp only [he, ite_true]
    omega
  have h3 : shortcut (3 * x + 1) = shortcut x := by
    unfold shortcut
    have he : (3 * x + 1) % 2 = 0 := by omega
    simp only [he, ite_true, hxne, ite_false]
  simp [iter, h1, h2, h3]

/-- Exact parametric coalescence law for every owner lift. -/
theorem ownerLift_coalesces
    {p : Nat} (hpodd : p % 2 = 1) :
    ∀ k, iter shortcut (2 * k + 1) (ownerLift k p) = shortcut p := by
  intro k
  induction k with
  | zero =>
      simp [ownerLift, iter]
  | succ k ih =>
      have hkodd : ownerLift k p % 2 = 1 := ownerLift_odd hpodd k
      have h3 :
          iter shortcut 3 (ownerLift (k + 1) p) =
            shortcut (ownerLift k p) := by
        simpa [ownerLift] using iter_three_four_mul_add_one hkodd
      calc
        iter shortcut (2 * (k + 1) + 1) (ownerLift (k + 1) p) =
            iter shortcut (2 * k)
              (iter shortcut 3 (ownerLift (k + 1) p)) := by
                rw [show 2 * (k + 1) + 1 = 3 + 2 * k by omega, iter_add]
        _ = iter shortcut (2 * k) (shortcut (ownerLift k p)) := by rw [h3]
        _ = iter shortcut (2 * k + 1) (ownerLift k p) := by
              simp [iter]
        _ = shortcut p := ih

/-- If an owner lift occurs on n's orbit and its owner p is smaller than n,
it is an exact lower-source coalescence certificate. -/
theorem lower_merge_of_ownerLift_on_orbit
    {n p j k : Nat}
    (hpodd : p % 2 = 1)
    (hlt : p < n)
    (horbit : iter shortcut j n = ownerLift k p) :
    LowerMerge shortcut n p := by
  refine ⟨hlt, j + (2 * k + 1), 1, ?_⟩
  rw [iter_add, horbit]
  simpa [iter] using ownerLift_coalesces hpodd k

/-- Ordinary-exit form of the same constructor at the common future. -/
theorem ordinary_exit_of_ownerLift_on_orbit
    {n p j k : Nat}
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (hlt : p < n)
    (horbit : iter shortcut j n = ownerLift k p) :
    ∃ a, OrdinaryExit n (iter shortcut a n) := by
  refine ⟨j + (2 * k + 1), ?_⟩
  refine Or.inr (Or.inr ⟨p, 1, hp, hlt, ?_⟩)
  rw [iter_add, horbit]
  simpa [iter] using (ownerLift_coalesces hpodd k).symm

/-- On a hypothetical minimal positive bad orbit, every exact owner-lift
representation is source-anchored: its odd owner cannot lie below the source.
Otherwise the valuation-pullback constructor gives a lower-source ordinary
exit. -/
theorem minimal_bad_ownerLift_owner_ge
    {n p j k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (horbit : iter shortcut j n = ownerLift k p) :
    n ≤ p := by
  apply Nat.le_of_not_gt
  intro hlt
  obtain ⟨a, hexit⟩ :=
    ordinary_exit_of_ownerLift_on_orbit hp hpodd hlt horbit
  exact minimal_bad_has_no_ordinary_exit hmin a hexit

/-- First concrete valuation barrier.  Below 4*n+1 a minimal-bad orbit cannot
occupy residue 5 modulo 8, because every such value is exactly ownerLift 1 p
for an odd p<n. -/
theorem minimal_bad_below_four_source_not_mod8_five
    {n j : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hlt : iter shortcut j n < 4 * n + 1) :
    iter shortcut j n % 8 ≠ 5 := by
  intro hmod
  let x := iter shortcut j n
  let a := x / 8
  let p := 2 * a + 1
  have hx : x = 8 * a + 5 := by
    have hd := Nat.mod_add_div x 8
    dsimp [a]
    omega
  have hp : 0 < p := by
    dsimp [p]
    omega
  have hpodd : p % 2 = 1 := by
    dsimp [p]
    omega
  have hlift : ownerLift 1 p = x := by
    simp [ownerLift, p]
    omega
  have horbit : iter shortcut j n = ownerLift 1 p := by
    simpa [x] using hlift.symm
  have hge := minimal_bad_ownerLift_owner_ge hmin hp hpodd horbit
  have hxp : x = 4 * p + 1 := by
    calc
      x = ownerLift 1 p := hlift.symm
      _ = 4 * p + 1 := by simp [ownerLift]
  omega

#print axioms minimal_bad_ownerLift_owner_ge
#print axioms minimal_bad_below_four_source_not_mod8_five

#print axioms ownerLift_coalesces
#print axioms lower_merge_of_ownerLift_on_orbit
#print axioms ordinary_exit_of_ownerLift_on_orbit

end SourceProduct
end CollatzFinal
