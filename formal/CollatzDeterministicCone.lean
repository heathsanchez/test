import «CollatzConeReduction»
import «CollatzShortcutCone»

/--
The exact H-free deterministic cone witness tested computationally.

Starting from n, reach y.  Then either y is already a strict positive lower
value, or y has the explicit inverse-odd predecessor

  p = (2*y - 1) / 3

which is positive, strictly below n, and maps to y under the shortcut Collatz
map.  The p=1 edge records the one extra successor needed by the abstract
strong-induction reduction.
-/
structure DeterministicConeWitness (n : Nat) where
  y : Nat
  reach : Reach collatzShortcut n y
  kind :
    (0 < y ∧ y < n) ∨
    (y % 3 = 2 ∧
      let p := (2 * y - 1) / 3
      0 < p ∧ p < n ∧
      collatzShortcut p = y ∧
      (p = 1 → collatzShortcut y = 1))

def DeterministicConeLaw : Prop :=
  ∀ n : Nat, 1 < n → n % 2 = 1 →
    Nonempty (DeterministicConeWitness n)

/-- Every exact deterministic-cone witness is an abstract lower witness. -/
def lowerWitnessOfDeterministicCone
    {n : Nat} (w : DeterministicConeWitness n) :
    LowerWitness collatzShortcut n := by
  refine {
    y := w.y
    reach := w.reach
    kind := ?_
  }
  cases w.kind with
  | inl h =>
      exact Or.inl h
  | inr h =>
      refine Or.inr ?_
      let p := (2 * w.y - 1) / 3
      exact ⟨p, h.2.1, h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩

/--
The exact deterministic cone law implies global Collatz convergence.
-/
theorem collatzConvergesOfDeterministicConeLaw
    (hcone : DeterministicConeLaw) :
    ∀ n : Nat, 0 < n → Reach collatzShortcut n 1 := by
  apply collatzConvergesOfOddLowerWitness
  intro n hn hodd
  exact lowerWitnessOfDeterministicCone
    (Classical.choice (hcone n hn hodd))

/--
If Collatz convergence holds, the exact deterministic cone law holds
trivially by taking y = 1 as the direct lower witness.
-/
def deterministicConeLawOfCollatzConvergence
    (hconv : ∀ n : Nat, 0 < n → Reach collatzShortcut n 1) :
    DeterministicConeLaw := by
  intro n hn _hodd
  have hnPos : 0 < n := by omega
  exact ⟨{
    y := 1
    reach := hconv n hnPos
    kind := Or.inl ⟨by decide, hn⟩
  }⟩

/--
Exact formal research boundary.

The unbounded deterministic cone law used by the experiments is equivalent in
logical strength to the Collatz conjecture for the shortcut map.
-/
theorem collatzConvergenceIffDeterministicConeLaw :
    (∀ n : Nat, 0 < n → Reach collatzShortcut n 1) ↔
    DeterministicConeLaw := by
  constructor
  · exact deterministicConeLawOfCollatzConvergence
  · exact collatzConvergesOfDeterministicConeLaw
