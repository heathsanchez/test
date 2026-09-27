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
      simp [ownerLift]

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
    omega
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
  have hm := lower_merge_of_ownerLift_on_orbit hpodd hlt horbit
  rcases hm with ⟨_, a, b, hab⟩
  have ha : a = j + (2 * k + 1) := rfl
  subst a
  exact Or.inr (Or.inr ⟨p, b, hp, hlt, hab.symm⟩)

#print axioms ownerLift_coalesces
#print axioms lower_merge_of_ownerLift_on_orbit
#print axioms ordinary_exit_of_ownerLift_on_orbit

end SourceProduct
end CollatzFinal
