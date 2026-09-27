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

/-- Once the source itself lies below the dyadic scale, its source-product tail
    has vanished completely. -/
theorem at_tail_zero_of_source_lt_pow
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).tail = 0 := by
  have h := (common_tail (at_valid hn k)).1
  rw [at_source, at_depth, Nat.div_eq_of_lt hlt] at h
  exact h.symm

/-- After the tail vanishes, the source residue is the source itself. -/
theorem at_sourceResidue_eq_source_of_lt
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).sourceResidue = n := by
  have hv := at_valid hn k
  have ht := at_tail_zero_of_source_lt_pow hn hlt
  have hs := hv.2.2.2
  rw [at_source, at_depth, ht, Nat.mul_zero, Nat.add_zero] at hs
  exact hs.symm

/-- In the fixed-origin regime the endpoint residue is no abstraction: it is
    exactly the ordinary shortcut orbit value. -/
theorem at_endpointResidue_eq_iter_of_lt
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).endpointResidue = iter shortcut k n := by
  have ht := at_tail_zero_of_source_lt_pow hn hlt
  have he := at_endpoint n k
  unfold endpoint at he
  rw [ht, Nat.mul_zero, Nat.add_zero] at he
  exact he

/-- Complete fixed-origin collapse of the source-product presentation. -/
theorem fixed_origin_state_collapse
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).tail = 0 ∧
    (stateAt n k).sourceResidue = n ∧
    (stateAt n k).endpointResidue = iter shortcut k n := by
  exact ⟨at_tail_zero_of_source_lt_pow hn hlt,
    at_sourceResidue_eq_source_of_lt hn hlt,
    at_endpointResidue_eq_iter_of_lt hn hlt⟩

#print axioms at_tail_zero_of_source_lt_pow
#print axioms at_sourceResidue_eq_source_of_lt
#print axioms at_endpointResidue_eq_iter_of_lt
#print axioms fixed_origin_state_collapse

#print axioms inside_origin_forces_zero_tail_bit
#print axioms fixed_origin_no_import
#print axioms fixed_origin_parent_inside

end SourceProduct
end CollatzFinal
