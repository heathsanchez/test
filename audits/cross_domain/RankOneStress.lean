import Mathlib.Tactic

/-! A small reusable rank-one stress interface. This is an elementary
algebraic result, not a Navier--Stokes blow-up theorem. -/
namespace CrossDomainResidual

/-- On the rank-one cone, the mixed entry and diagonal difference determine
both diagonal entries. The nonnegativity of the squares is essential. -/
theorem rankOne_fiber (x y x' y' : ℝ)
    (hxy : x * y = x' * y')
    (hd : x ^ 2 - y ^ 2 = x' ^ 2 - y' ^ 2) :
    x ^ 2 = x' ^ 2 ∧ y ^ 2 = y' ^ 2 := by
  have hsquared : (x ^ 2 + y ^ 2) ^ 2 = (x' ^ 2 + y' ^ 2) ^ 2 := by
    calc
      (x ^ 2 + y ^ 2) ^ 2 = (x ^ 2 - y ^ 2) ^ 2 + 4 * (x * y) ^ 2 := by ring
      _ = (x' ^ 2 - y' ^ 2) ^ 2 + 4 * (x' * y') ^ 2 := by rw [hd, hxy]
      _ = (x' ^ 2 + y' ^ 2) ^ 2 := by ring
  have htrace : x ^ 2 + y ^ 2 = x' ^ 2 + y' ^ 2 := by
    nlinarith [sq_nonneg x, sq_nonneg y, sq_nonneg x', sq_nonneg y']
  constructor <;> nlinarith

/-- Two unnormalised cell means, the mixed quadratic flux, and the diagonal
flux difference determine the entire symmetric quadratic flux. -/
theorem twoCell_flux_determined
    (a b c d a' b' c' d' : ℝ)
    (hmx : a + c = a' + c')
    (hmy : b + d = b' + d')
    (hxy : a*b + c*d = a'*b' + c'*d')
    (hd : a*a + c*c - (b*b + d*d) =
          a'*a' + c'*c' - (b'*b' + d'*d')) :
    a*a + c*c = a'*a' + c'*c' ∧
    a*b + c*d = a'*b' + c'*d' ∧
    b*b + d*d = b'*b' + d'*d' := by
  have hmprod : (a+c)*(b+d) = (a'+c')*(b'+d') := by rw [hmx,hmy]
  have hmsqX : (a+c)^2 = (a'+c')^2 := by rw [hmx]
  have hmsqY : (b+d)^2 = (b'+d')^2 := by rw [hmy]
  have hcross : (a-c)*(b-d) = (a'-c')*(b'-d') := by
    nlinarith [hmprod, hxy]
  have hdiag : (a-c)^2 - (b-d)^2 = (a'-c')^2 - (b'-d')^2 := by
    nlinarith [hd, hmsqX, hmsqY]
  obtain ⟨hX,hY⟩ := rankOne_fiber (a-c) (b-d) (a'-c') (b'-d') hcross hdiag
  constructor
  · nlinarith [hX,hmsqX]
  constructor
  · exact hxy
  · nlinarith [hY,hmsqY]

/-- The same interface does not determine the signed fluctuation itself. -/
theorem sign_ambiguity :
    (1:ℝ)*2 = (-1)*(-2) ∧
    (1:ℝ)^2 - 2^2 = (-1)^2 - (-2)^2 ∧
    (1:ℝ) ≠ -1 := by norm_num

#print axioms rankOne_fiber
#print axioms twoCell_flux_determined
#print axioms sign_ambiguity
end CrossDomainResidual
