import Collatz.FirstCrossingGap

namespace CollatzFinal
namespace SourceProduct

/-- Pure exponent form of the zero-carry boundary-excursion law.

If the coefficient is still above threshold immediately after the starting
boundary, while the ending coefficient is below the *next* threshold, then
the intervening multiplicative block is strictly contractive.

This is independent of any finite source census or particular parity word. -/
theorem boundary_excursion_coefficient_contracts
    {s L q r : Nat}
    (hstart : 2 ^ (s + 1) ≤ 3 ^ q)
    (hend : 3 ^ (q + r) < 2 ^ (s + L + 1)) :
    3 ^ r < 2 ^ L := by
  by_contra hnot
  have hge : 2 ^ L ≤ 3 ^ r := by omega
  have hmul :
      2 ^ (s + 1) * 2 ^ L ≤ 3 ^ q * 3 ^ r :=
    Nat.mul_le_mul hstart hge
  have hcontra :
      2 ^ (s + L + 1) ≤ 3 ^ (q + r) := by
    calc
      2 ^ (s + L + 1) = 2 ^ ((s + 1) + L) := by
        congr 1
        omega
      _ = 2 ^ (s + 1) * 2 ^ L := by
        rw [pow_add]
      _ ≤ 3 ^ q * 3 ^ r := hmul
      _ = 3 ^ (q + r) := by
        rw [pow_add]
  omega

/-- Equivalent block-language form with explicit start/end depths. -/
theorem boundary_excursion_depth_contracts
    {s e q r : Nat}
    (hse : s ≤ e)
    (hstart : 2 ^ (s + 1) ≤ 3 ^ q)
    (hend : 3 ^ (q + r) < 2 ^ (e + 1))
    (hlen : e = s + (e - s)) :
    3 ^ r < 2 ^ (e - s) := by
  apply boundary_excursion_coefficient_contracts
    (s := s) (L := e - s) (q := q) (r := r) hstart
  simpa [hlen, Nat.add_assoc] using hend

/-- For an affine shortcut block with a contractive multiplicative coefficient,
failure of strict decrease is exactly paid for by the additive bias.  This
isolates the only quantity contraction alone does not control. -/
theorem affine_contracting_block_nondescending_forces_bias
    {A B D x y : Nat}
    (hA : A < 2 ^ D)
    (hxy : 2 ^ D * y = A * x + B)
    (hnd : x ≤ y) :
    (2 ^ D - A) * x ≤ B := by
  have hs : 2 ^ D * x ≤ 2 ^ D * y :=
    Nat.mul_le_mul_left (2 ^ D) hnd
  rw [hxy] at hs
  rw [Nat.sub_mul]
  omega

/-- Conversely, if the additive bias is smaller than the contraction deficit
at the block input, the block strictly descends. -/
theorem affine_contracting_block_descends_of_bias_lt
    {A B D x y : Nat}
    (hA : A < 2 ^ D)
    (hxy : 2 ^ D * y = A * x + B)
    (hbias : B < (2 ^ D - A) * x) :
    y < x := by
  apply Classical.byContradiction
  intro hnot
  have hnd : x ≤ y := by omega
  have hforced :=
    affine_contracting_block_nondescending_forces_bias hA hxy hnd
  omega

#print axioms boundary_excursion_coefficient_contracts
#print axioms boundary_excursion_depth_contracts
#print axioms affine_contracting_block_nondescending_forces_bias
#print axioms affine_contracting_block_descends_of_bias_lt

end SourceProduct
end CollatzFinal
