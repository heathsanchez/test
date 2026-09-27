import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/--
Once the protected origin window lies below the next source-lift scale,
a source-product child that remains in that window must have zero tail bit.
-/
theorem inside_origin_forces_zero_tail_bit
    (s : State) (X : Nat)
    (hX : X ≤ 2 ^ s.depth)
    (hin : (step s).sourceResidue < X) :
    s.tail % 2 = 0 := by
  have hb : s.tail % 2 = 0 ∨ s.tail % 2 = 1 := by
    omega
  rcases hb with h0 | h1
  · exact h0
  · change s.sourceResidue + 2 ^ s.depth * (s.tail % 2) < X at hin
    simp only [h1, Nat.mul_one] at hin
    omega

/--
Fixed-origin no-import law: a child that remains below X≤2^depth cannot
arrive by the positive 2^depth source lift, so its source residue is unchanged.
-/
theorem fixed_origin_no_import
    (s : State) (X : Nat)
    (hX : X ≤ 2 ^ s.depth)
    (hin : (step s).sourceResidue < X) :
    (step s).sourceResidue = s.sourceResidue := by
  have h0 := inside_origin_forces_zero_tail_bit s X hX hin
  change s.sourceResidue + 2 ^ s.depth * (s.tail % 2) = s.sourceResidue
  simp [h0]

/-- Any child remaining in the protected origin window came from a parent
    already in that same window. -/
theorem fixed_origin_parent_inside
    (s : State) (X : Nat)
    (hX : X ≤ 2 ^ s.depth)
    (hin : (step s).sourceResidue < X) :
    s.sourceResidue < X := by
  rw [← fixed_origin_no_import s X hX hin]
  exact hin

#print axioms inside_origin_forces_zero_tail_bit
#print axioms fixed_origin_no_import
#print axioms fixed_origin_parent_inside

end SourceProduct
end CollatzFinal
