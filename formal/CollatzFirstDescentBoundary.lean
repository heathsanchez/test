import «CollatzCanonicalConsequence»

/--
If an affine Collatz prefix has genuinely descended at one positive integer,
then its multiplicative coefficient is already strictly contracting.

This is the algebraic reason there is no separate "slope wait" after first
descent: the additive Collatz offset is nonnegative.
-/
theorem affineDescentForcesSlope
    {A M C n : Nat}
    (h : A * n + C < M * n) :
    A < M := by
  by_contra hnot
  have hMA : M ≤ A := Nat.le_of_not_gt hnot
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
A concrete affine first descent therefore certifies the whole parity cylinder:
the slope contraction follows automatically from the affine identity.
-/
theorem firstDescentClosesCylinder
    {A M C n y q : Nat}
    (hAff : M * y = A * n + C)
    (hM : 0 < M)
    (hy : y < n) :
    A * q + y < M * q + n := by
  have hscaled : M * y < M * n := by
    exact Nat.mul_lt_mul_left M hy hM
  have hdesc : A * n + C < M * n := by
    simpa [hAff] using hscaled
  have hA : A < M := affineDescentForcesSlope hdesc
  exact affineCylinderDescent hA hy

/--
The exact remaining global boundary: finite first descent for every n>1 is
sufficient for shortcut-Collatz convergence by strong induction.
-/
theorem collatzConvergesOfFirstDescent
    (drop : ∀ n : Nat, 1 < n →
      ∃ y : Nat, 0 < y ∧ y < n ∧ Reach collatzShortcut n y) :
    ∀ n : Nat, 0 < n → Reach collatzShortcut n 1 := by
  apply collatzConvergesOfCanonicalConsequenceCompiler
  intro n hn
  obtain ⟨y, hyPos, hyLt, hreach⟩ := drop n hn
  exact directLowerConsequence hyPos hyLt hreach
