import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-- Once the dyadic depth exceeds a fixed positive source, the exact
source-product tail is zero. From this point onward no new source bit/carry
can be supplied; only the actual endpoint dynamics remain. -/
theorem source_tail_zero_of_lt_pow
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).tail = 0 := by
  have htail := (common_tail (at_valid hn k)).1
  rw [at_source, at_depth, Nat.div_eq_of_lt hlt] at htail
  exact htail.symm

/-- At zero tail the canonical source residue is the actual fixed source. -/
theorem sourceResidue_eq_source_of_tail_zero
    {s : State} (hs : Valid s) (hzero : s.tail = 0) :
    s.sourceResidue = s.source := by
  have he := hs.2.2.2
  simp [hzero] at he
  exact he.symm

/-- A zero source tail freezes the canonical source residue on the next step. -/
theorem sourceResidue_frozen_of_tail_zero
    (s : State) (hzero : s.tail = 0) :
    (step s).sourceResidue = s.sourceResidue := by
  simp [step, hzero]

/-- Exact one-step arithmetic behind a first coefficient crossing.

qmin <= q says the parent is still live. Both the actual odd-count increment
e and the moving coefficient-boundary increment delta are bits. If the child
falls below the boundary, the parent was exactly on it, the endpoint supplied
no odd-step replenishment, and the boundary carried. -/
theorem first_crossing_carry_shape
    {q qmin e delta : Nat}
    (he : e ≤ 1)
    (hdelta : delta ≤ 1)
    (hlive : qmin ≤ q)
    (hcross : q + e < qmin + delta) :
    q = qmin ∧ e = 0 ∧ delta = 1 := by
  omega

/-- The fatal carry shape is sufficient for a one-step boundary crossing. -/
theorem crossing_of_boundary_even_carry
    {q qmin e delta : Nat}
    (hboundary : q = qmin)
    (heven : e = 0)
    (hcarry : delta = 1) :
    q + e < qmin + delta := by
  omega

#print axioms source_tail_zero_of_lt_pow
#print axioms sourceResidue_eq_source_of_tail_zero
#print axioms sourceResidue_frozen_of_tail_zero
#print axioms first_crossing_carry_shape
#print axioms crossing_of_boundary_even_carry

end SourceProduct
end CollatzFinal
