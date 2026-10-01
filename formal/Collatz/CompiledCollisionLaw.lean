import Collatz.EarlierSourceCollision

namespace CollatzFinal.SourceProduct

/-- The dominant V65/V66 reverse word OEOO, compiled once.

Starting at the earlier source 16*q+11, the actual shortcut parity word is
O,O,E,O and lands exactly at 27*q+20 after four shortcut steps.  Equivalently,
for an endpoint y ≡ 20 (mod 27), the reverse word O,E,O,O recovers the exact
earlier source (16*y-23)/27 without storing the discovery trace. -/
theorem oeoo_exact (q : Nat) :
    iter shortcut 4 (16 * q + 11) = 27 * q + 20 := by
  have h1 : shortcut (16 * q + 11) = 24 * q + 17 := by
    have hp : (16 * q + 11) % 2 ≠ 0 := by omega
    rw [shortcut, if_neg hp]
    omega
  have h2 : shortcut (24 * q + 17) = 36 * q + 26 := by
    have hp : (24 * q + 17) % 2 ≠ 0 := by omega
    rw [shortcut, if_neg hp]
    omega
  have h3 : shortcut (36 * q + 26) = 18 * q + 13 := by
    have hp : (36 * q + 26) % 2 = 0 := by omega
    rw [shortcut, if_pos hp]
    omega
  have h4 : shortcut (18 * q + 13) = 27 * q + 20 := by
    have hp : (18 * q + 13) % 2 ≠ 0 := by omega
    rw [shortcut, if_neg hp]
    omega
  simp [iter, h1, h2, h3, h4]

/-- A single source-relative inequality turns the compiled OEOO word into the
protected EarlierSourceCollision consequence. -/
theorem earlierSourceCollision_oeoo
    {source q : Nat}
    (hbelow : 16 * q + 11 < source) :
    EarlierSourceCollision source (27 * q + 20) := by
  refine ⟨16 * q + 11, 4, ?_, hbelow, ?_⟩
  · omega
  · exact oeoo_exact q

/-- Affine-family form used by the parameter-cover compiler.  The parameter is
not a new protected semantic coordinate; it is only a proof index for a family
of exact EarlierSourceCollision certificates. -/
theorem earlierSourceCollision_oeoo_affine
    {source0 sourceSlope q0 qSlope u : Nat}
    (hbelow :
      16 * (q0 + qSlope * u) + 11 <
        source0 + sourceSlope * u) :
    EarlierSourceCollision
      (source0 + sourceSlope * u)
      (27 * (q0 + qSlope * u) + 20) := by
  exact earlierSourceCollision_oeoo hbelow

/-- The compiled collision immediately discharges the old OrdinaryExit label,
showing that the old exit taxonomy is not needed at use sites. -/
theorem ordinaryExit_oeoo
    {source q : Nat}
    (hsource : 1 < source)
    (hbelow : 16 * q + 11 < source) :
    OrdinaryExit source (27 * q + 20) := by
  exact (ordinaryExit_iff_earlierSourceCollision hsource).2
    (earlierSourceCollision_oeoo hbelow)

#print axioms oeoo_exact
#print axioms earlierSourceCollision_oeoo
#print axioms earlierSourceCollision_oeoo_affine
#print axioms ordinaryExit_oeoo

end CollatzFinal.SourceProduct
