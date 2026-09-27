import Mathlib

namespace CollatzOriginTransfer

/-- One symbolic live source-product state at depth j. -/
structure State where
  q : Nat
  R : Nat
  Y : Nat
deriving DecidableEq, Repr

/-- Source coordinate of the child obtained with lift ell. -/
def childSource (j : Nat) (s : State) (ell : Nat) : Nat :=
  s.R + ell * 2^j

/-- The unique parity bit which gives zero source lift is the endpoint parity. -/
theorem zeroLift_bit_unique (j : Nat) (s : State) (bit : Nat)
    (hbit : bit < 2) :
    ((bit - s.Y) % 2 = 0) ↔ bit = s.Y % 2 := by
  omega

/-- A positive lift leaves every fixed origin window X <= 2^j. -/
theorem positiveLift_outside_origin
    (j X : Nat) (s : State)
    (hR : s.R < X) (hX : X ≤ 2^j) :
    X ≤ childSource j s 1 := by
  simp [childSource]
  omega

/-- Consequently, any child which remains below X must use zero lift. -/
theorem inside_origin_forces_zero_lift
    (j X ell : Nat) (s : State)
    (hX : X ≤ 2^j) (hell : ell < 2)
    (hin : childSource j s ell < X) :
    ell = 0 := by
  interval_cases ell <;> simp_all [childSource]
  omega

/--
Fixed-origin transfer principle: once X <= 2^j, source lifting cannot import a
new parent into [0,X). Any child in the origin window is the zero-lift child.
This is the structural theorem needed before adding the legal q-threshold.
-/
theorem fixed_origin_no_import
    (j X : Nat) (s : State) (ell : Nat)
    (hX : X ≤ 2^j) (hell : ell < 2)
    (hin : childSource j s ell < X) :
    childSource j s ell = s.R := by
  have h0 := inside_origin_forces_zero_lift j X ell s hX hell hin
  simp [h0, childSource]

end CollatzOriginTransfer
