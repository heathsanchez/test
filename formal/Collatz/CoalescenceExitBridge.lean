import Collatz.CoalescenceDescent

namespace CollatzFinal
namespace SourceProduct

/-- Any ordinary exit encountered on the actual orbit of a source n>1
constructs a strictly smaller positive source whose orbit coalesces with n. -/
theorem lower_source_certificate_of_ordinary_exit_at
    {n k : Nat}
    (hgt : 1 < n)
    (hx : OrdinaryExit n (iter shortcut k n)) :
    ∃ p, 0 < p ∧ LowerMerge shortcut n p := by
  rcases hx with ht | hd | hm
  · rcases ht with h1 | h2
    · refine ⟨1, by omega, hgt, k, 0, ?_⟩
      simpa [iter, h1]
    · refine ⟨1, by omega, hgt, k, 1, ?_⟩
      simpa [iter, h2, shortcut_one]
  · refine ⟨iter shortcut k n, hd.1, hd.2, k, 0, ?_⟩
    simp [iter]
  · obtain ⟨p, b, hp, hlt, heq⟩ := hm
    refine ⟨p, hp, hlt, k, b, ?_⟩
    exact heq.symm

/-- Conversely, a lower-source coalescence certificate is already an
ordinary-exit witness at the matching source depth. -/
theorem ordinary_exit_of_lower_source_certificate
    {n p : Nat}
    (hp : 0 < p)
    (hm : LowerMerge shortcut n p) :
    ∃ k, OrdinaryExit n (iter shortcut k n) := by
  obtain ⟨hlt, a, b, hab⟩ := hm
  refine ⟨a, Or.inr (Or.inr ⟨p, b, hp, hlt, ?_⟩)⟩
  exact hab.symm

/-- The campaign-facing eventual OrdinaryExit obligation is exactly
CoalescenceDescent once the trivial source n=1 is removed. -/
theorem eventual_ordinary_exit_gt_one_iff_coalescence_descent :
    (∀ n, 1 < n → ∃ k, OrdinaryExit n (iter shortcut k n)) ↔
      CoalescenceDescent := by
  constructor
  · intro hexit n hgt
    obtain ⟨k, hx⟩ := hexit n hgt
    exact lower_source_certificate_of_ordinary_exit_at hgt hx
  · intro hcd n hgt
    obtain ⟨p, hp, hm⟩ := hcd n hgt
    exact ordinary_exit_of_lower_source_certificate hp hm

/-- Therefore eventual OrdinaryExit, universal lower-source coalescence,
and positive Collatz termination are the same remaining proposition. -/
theorem eventual_ordinary_exit_gt_one_iff_collatz :
    (∀ n, 1 < n → ∃ k, OrdinaryExit n (iter shortcut k n)) ↔
      (∀ n, 0 < n → CollatzGood n) := by
  rw [eventual_ordinary_exit_gt_one_iff_coalescence_descent]
  exact coalescence_descent_iff_collatz

#print axioms lower_source_certificate_of_ordinary_exit_at
#print axioms ordinary_exit_of_lower_source_certificate
#print axioms eventual_ordinary_exit_gt_one_iff_coalescence_descent
#print axioms eventual_ordinary_exit_gt_one_iff_collatz

end SourceProduct
end CollatzFinal
