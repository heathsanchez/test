import Collatz.FSwapGrammar
import Collatz.ReverseAffineMerger

namespace CollatzFinal
namespace SourceProduct

/-- The protected composition interface for an entire infinite affine family.
    The F-collision certificate is required for EVERY offset, independently
    of the exact reverse-affine predecessor word. No global event-production
    or source-coverage premise is hidden here. -/
theorem affine_phase_family_lower_merge
    (a M p c k t : Nat)
    (hcollision : ∀ q : Nat, FCollisionCert (a + M * q) t)
    (hreverse : AffineReverse (3 * a + 2) (3 * M) p c k)
    (hpositive : 0 < p)
    (hbelow : p < a)
    (hslope : c ≤ M)
    (q : Nat) :
    0 < p + c * q ∧
      LowerMerge shortcut (a + M * q) (p + c * q) := by
  have hword := affine_reverse_sound hreverse q
  have hscaled :
      (3 * a + 2) + (3 * M) * q = 3 * (a + M * q) + 2 := by
    simp [Nat.mul_add, Nat.mul_assoc, Nat.add_assoc, Nat.add_comm,
      Nat.add_left_comm]
  have hpre :
      iter shortcut k (p + c * q) = 3 * (a + M * q) + 2 := by
    calc
      iter shortcut k (p + c * q) =
          (3 * a + 2) + (3 * M) * q := hword
      _ = 3 * (a + M * q) + 2 := hscaled
  have hmul : c * q ≤ M * q := Nat.mul_le_mul_right q hslope
  have hpos : 0 < p + c * q := by omega
  have hlt : p + c * q < a + M * q := by omega
  exact F_certificate_lower_merge (a + M * q) (p + c * q)
    t k (hcollision q) hpre hpos hlt

/-- More explicit quantifier form for a reusable certified constructor. -/
theorem affine_phase_family_all_offsets
    (a M p c k t : Nat)
    (hcollision : ∀ q : Nat, FCollisionCert (a + M * q) t)
    (hreverse : AffineReverse (3 * a + 2) (3 * M) p c k)
    (hpositive : 0 < p)
    (hbelow : p < a)
    (hslope : c ≤ M) :
    ∀ q : Nat, 0 < p + c * q ∧
      LowerMerge shortcut (a + M * q) (p + c * q) := by
  intro q
  exact affine_phase_family_lower_merge a M p c k t
    hcollision hreverse hpositive hbelow hslope q

#print axioms affine_phase_family_lower_merge
#print axioms affine_phase_family_all_offsets

end SourceProduct
end CollatzFinal
