import «CollatzCanonicalConsequence»

/--
If an affine Collatz prefix has genuinely descended at one positive integer,
then its multiplicative coefficient is already strictly contracting.

The additive offset is nonnegative, so A >= M would make
A*n + C >= M*n, contradicting descent.
-/
theorem affineDescentForcesSlope
    {A M C n : Nat}
    (h : A * n + C < M * n) :
    A < M := by
  apply Nat.lt_of_not_ge
  intro hMA
  have hmul : M * n ≤ A * n := by
    exact Nat.mul_le_mul_right n hMA
  have hadd : A * n ≤ A * n + C := by
    omega
  have hcontra : M * n ≤ A * n + C :=
    Nat.le_trans hmul hadd
  exact (Nat.not_lt_of_ge hcontra) h

/--
Once both the affine slope and the concrete boundary value are lower, every
member of the corresponding cylinder is lower.
-/
theorem affineCylinderDescent
    {A M y n q : Nat}
    (hA : A < M)
    (hy : y < n) :
    A * q + y < M * q + n := by
  have hcoef : A * q ≤ M * q := by
    exact Nat.mul_le_mul_right q (Nat.le_of_lt hA)
  omega

/--
A concrete affine descent inequality therefore certifies the whole parity
cylinder.  This is the exact algebra behind the observed zero slope-wait count.
-/
theorem affineDescentClosesCylinder
    {A M C n y q : Nat}
    (hdesc : A * n + C < M * n)
    (hy : y < n) :
    A * q + y < M * q + n := by
  have hA : A < M := affineDescentForcesSlope hdesc
  exact affineCylinderDescent hA hy

/--
The exact remaining global boundary: finite first descent for every n>1 is
sufficient for shortcut-Collatz convergence by strong induction.

This theorem deliberately stays in Prop, so the existential first-descent
witness can be eliminated directly without choosing computational data.
-/
theorem collatzConvergesOfFirstDescent
    (drop : ∀ n : Nat, 1 < n →
      ∃ y : Nat, 0 < y ∧ y < n ∧ Reach collatzShortcut n y) :
    ∀ n : Nat, 0 < n → Reach collatzShortcut n 1 := by
  intro n
  refine Nat.strongRecOn n ?_
  intro n ih hn
  cases n with
  | zero =>
      exact False.elim (Nat.lt_irrefl 0 hn)
  | succ k =>
      cases k with
      | zero =>
          exact Reach.refl 1
      | succ m =>
          have hgt : 1 < Nat.succ (Nat.succ m) := by
            omega
          obtain ⟨y, hyPos, hyLt, hreach⟩ :=
            drop (Nat.succ (Nat.succ m)) hgt
          have hyConv : Reach collatzShortcut y 1 :=
            ih y hyLt hyPos
          exact Reach.trans hreach hyConv
