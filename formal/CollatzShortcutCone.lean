import Init.Data.Nat.Div.Lemmas
import «CollatzConeReduction»

/-- The shortcut Collatz map used throughout the experiments. -/
def collatzShortcut (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else (3 * n + 1) / 2

/-- Every even n > 1 supplies a strict direct lower witness by halving. -/
def evenLowerWitness
    (n : Nat) (hn : 1 < n) (heven : n % 2 = 0) :
    LowerWitness collatzShortcut n := by
  have hnPos : 0 < n := by omega
  have halfPos : 0 < n / 2 := by omega
  have halfLt : n / 2 < n :=
    Nat.div_lt_self hnPos (by decide)
  have hstep : collatzShortcut n = n / 2 := by
    simp [collatzShortcut, heven]
  exact {
    y := n / 2
    reach := Reach.step hstep (Reach.refl (n / 2))
    kind := Or.inl ⟨halfPos, halfLt⟩
  }

/--
Exact odd-only reduction.

To prove convergence of every positive natural for the shortcut Collatz map, it
is enough to construct a LowerWitness for every odd n > 1. Even n are handled
by the verified halving witness above.
-/
theorem collatzConvergesOfOddLowerWitness
    (oddLower :
      ∀ n : Nat, 1 < n → n % 2 = 1 → LowerWitness collatzShortcut n) :
    ∀ n : Nat, 0 < n → Reach collatzShortcut n 1 := by
  have lowerAll :
      ∀ n : Nat, 1 < n → LowerWitness collatzShortcut n := by
    intro n hn
    cases Nat.mod_two_eq_zero_or_one n with
    | inl heven =>
        exact evenLowerWitness n hn heven
    | inr hodd =>
        exact oddLower n hn hodd
  have h := allConvergeOfLowerWitness collatzShortcut lowerAll
  simpa [Converges] using h

/--
Conversely, global Collatz convergence trivially gives an odd lower witness:
choose the reached value y = 1. Thus the odd-lower-witness formulation is
equivalent in logical strength to global convergence.
-/
def oddLowerWitnessOfCollatzConvergence
    (allConv : ∀ n : Nat, 0 < n → Reach collatzShortcut n 1) :
    ∀ n : Nat, 1 < n → n % 2 = 1 → LowerWitness collatzShortcut n := by
  intro n hn _hodd
  apply lowerWitnessOfConvergence collatzShortcut
  · intro m hm
    exact allConv m hm
  · exact hn

theorem collatzConvergenceIffOddLowerWitness :
    (∀ n : Nat, 0 < n → Reach collatzShortcut n 1) ↔
    Nonempty
      (∀ n : Nat, 1 < n → n % 2 = 1 →
        LowerWitness collatzShortcut n) := by
  constructor
  · intro h
    exact ⟨oddLowerWitnessOfCollatzConvergence h⟩
  · intro h
    exact collatzConvergesOfOddLowerWitness (Classical.choice h)
