import Init.Data.Nat.Div.Lemmas
import «CollatzConeReduction»
import «CollatzShortcutCone»

/--
A lower consequence is the exact induction interface needed by a compiled
reverse certificate.

Starting from n we reach y.  A strictly smaller positive p is known, and any
proof that p converges can be transformed into a proof that y converges.
This permits reverse certificates of arbitrary finite length; they need not be
a single predecessor edge.
-/
structure LowerConsequence (f : Nat → Nat) (n : Nat) where
  y : Nat
  reach : Reach f n y
  p : Nat
  pPos : 0 < p
  pLt : p < n
  transfer : Converges f p → Converges f y

/--
Abstract strong-induction closure for arbitrary compiled lower consequences.
-/
theorem allConvergeOfLowerConsequence
    (f : Nat → Nat)
    (compiler : ∀ n : Nat, 1 < n → LowerConsequence f n) :
    ∀ n : Nat, 0 < n → Converges f n := by
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
          let w := compiler (Nat.succ (Nat.succ m)) hgt
          have hpConv : Converges f w.p :=
            ih w.p w.pLt w.pPos
          have hyConv : Converges f w.y :=
            w.transfer hpConv
          exact Reach.trans w.reach hyConv

/-- The canonical minimal odd predecessor when y ≡ 2 (mod 3). -/
def canonicalPred2 (y : Nat) : Nat :=
  2 * (y / 3) + 1

/-- The canonical minimal odd predecessor when y ≡ 1 (mod 3). -/
def canonicalPred1 (y : Nat) : Nat :=
  4 * (y / 3) + 1

theorem mod3_eq2_decomp {y : Nat} (h : y % 3 = 2) :
    y = 3 * (y / 3) + 2 := by
  omega

theorem mod3_eq1_decomp {y : Nat} (h : y % 3 = 1) :
    y = 3 * (y / 3) + 1 := by
  omega

/--
For an odd target y ≡ 2 mod 3, canonicalPred2 y maps to y in one
shortcut-Collatz step.
-/
theorem canonicalPred2_step
    {y : Nat} (h3 : y % 3 = 2) (hodd : y % 2 = 1) :
    collatzShortcut (canonicalPred2 y) = y := by
  have hy : y = 3 * (y / 3) + 2 := mod3_eq2_decomp h3
  have hpodd : canonicalPred2 y % 2 = 1 := by
    simp [canonicalPred2]
  simp [collatzShortcut, canonicalPred2, hpodd]
  omega

/--
For an odd target y ≡ 1 mod 3, canonicalPred1 y maps first to 2*y.
-/
theorem canonicalPred1_first
    {y : Nat} (h3 : y % 3 = 1) (hodd : y % 2 = 1) :
    collatzShortcut (canonicalPred1 y) = 2 * y := by
  have hy : y = 3 * (y / 3) + 1 := mod3_eq1_decomp h3
  have hpodd : canonicalPred1 y % 2 = 1 := by
    simp [canonicalPred1]
  simp [collatzShortcut, canonicalPred1, hpodd]
  omega

theorem double_shortcut (y : Nat) :
    collatzShortcut (2 * y) = y := by
  simp [collatzShortcut]

/--
Thus the y ≡ 1 mod 3 canonical predecessor reaches y in two shortcut steps.
-/
theorem canonicalPred1_reaches
    {y : Nat} (h3 : y % 3 = 1) (hodd : y % 2 = 1) :
    Reach collatzShortcut (canonicalPred1 y) y := by
  exact Reach.step (canonicalPred1_first h3 hodd)
    (Reach.step (double_shortcut y) (Reach.refl y))

/--
A direct lower reached value is a LowerConsequence (take p=y).
-/
def directLowerConsequence
    {n y : Nat} (hyPos : 0 < y) (hyLt : y < n)
    (hreach : Reach collatzShortcut n y) :
    LowerConsequence collatzShortcut n := {
  y := y
  reach := hreach
  p := y
  pPos := hyPos
  pLt := hyLt
  transfer := fun h => h
}

/--
The residue-2 canonical reverse edge yields a lower consequence whenever its
canonical predecessor is positive and strictly below n.
-/
def canonical2LowerConsequence
    {n y : Nat}
    (hreach : Reach collatzShortcut n y)
    (h3 : y % 3 = 2) (hodd : y % 2 = 1)
    (hpPos : 0 < canonicalPred2 y)
    (hpLt : canonicalPred2 y < n)
    (hpOne : canonicalPred2 y ≠ 1) :
    LowerConsequence collatzShortcut n := {
  y := y
  reach := hreach
  p := canonicalPred2 y
  pPos := hpPos
  pLt := hpLt
  transfer := by
    intro hpConv
    have htail : Reach collatzShortcut
        (collatzShortcut (canonicalPred2 y)) 1 :=
      Reach.tailOfNe hpConv hpOne
    rw [canonicalPred2_step h3 hodd] at htail
    exact htail
}

/--
The residue-1 canonical reverse edge is a two-step lower consequence.
-/
def canonical1LowerConsequence
    {n y : Nat}
    (hreach : Reach collatzShortcut n y)
    (h3 : y % 3 = 1) (hodd : y % 2 = 1)
    (hpPos : 0 < canonicalPred1 y)
    (hpLt : canonicalPred1 y < n)
    (hpOne : canonicalPred1 y ≠ 1)
    (hyPos : 0 < y) :
    LowerConsequence collatzShortcut n := {
  y := y
  reach := hreach
  p := canonicalPred1 y
  pPos := hpPos
  pLt := hpLt
  transfer := by
    intro hpConv
    have h2y : Reach collatzShortcut
        (collatzShortcut (canonicalPred1 y)) 1 :=
      Reach.tailOfNe hpConv hpOne
    rw [canonicalPred1_first h3 hodd] at h2y
    have h2yne : 2 * y ≠ 1 := by omega
    have hyConv : Reach collatzShortcut
        (collatzShortcut (2 * y)) 1 :=
      Reach.tailOfNe h2y h2yne
    rw [double_shortcut y] at hyConv
    exact hyConv
}

/--
Any compiler that supplies one of these generalized lower consequences for
every n>1 proves global convergence.
-/
theorem collatzConvergesOfCanonicalConsequenceCompiler
    (compiler : ∀ n : Nat, 1 < n →
      LowerConsequence collatzShortcut n) :
    ∀ n : Nat, 0 < n → Reach collatzShortcut n 1 := by
  simpa [Converges] using
    allConvergeOfLowerConsequence collatzShortcut compiler
