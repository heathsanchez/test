/-!
Renaissance intent-fidelity pilot. Exact finite scope: Fin 4.
All proof terms checked by Lean; the intended predicates are independently
specified here by the experimenter, not recovered from natural language.
No general natural-language fidelity or human-reviewer superiority claim.
-/
def intendedEven (x : Fin 4) : Bool := decide (x.val % 2 = 0)
def faithfulEven (x : Fin 4) : Bool := decide (x.val = 0 ∨ x.val = 2)
def wrongEven (x : Fin 4) : Bool := decide (x.val ≥ 0)
def intendedStrict (x : Fin 4) : Bool := decide (x.val ≥ 1)
def wrongStrict (x : Fin 4) : Bool := decide (x.val ≥ 0)
def intendedBound (x : Fin 4) : Bool := decide (x.val ≤ 2)
def faithfulBound (x : Fin 4) : Bool := decide (¬ x.val > 2)

theorem harmless_equivalence :
    ∀ x : Fin 4, intendedEven x = faithfulEven x := by decide

theorem wrong_even_counterexample :
    ∃ x : Fin 4, intendedEven x ≠ wrongEven x := by decide

theorem wrong_strict_counterexample :
    ∃ x : Fin 4, intendedStrict x ≠ wrongStrict x := by decide

theorem faithful_bound :
    ∀ x : Fin 4, intendedBound x = faithfulBound x := by decide

-- The wrong predicate itself has a valid theorem, but is not the intended predicate.
theorem valid_but_wrong_statement :
    ∀ x : Fin 4, wrongEven x = true := by decide

-- Explicitly finite proof dependency and selective withdrawal.
inductive Claim where
  | A | B | C | D | E | F
  deriving DecidableEq, Repr

def depends : Claim → List Claim
  | .A => []
  | .B => [.A]
  | .C => [.B]
  | .D => []
  | .E => [.D]
  | .F => [.A, .D]

def liveBefore : Claim → Bool := fun _ => true
def liveAfter : Claim → Bool
  | .A | .B | .C | .F => false
  | .D | .E => true

theorem independent_survives :
    liveAfter .D = true ∧ liveAfter .E = true := by decide
theorem dependent_withdrawn :
    liveAfter .A = false ∧ liveAfter .B = false ∧
    liveAfter .C = false ∧ liveAfter .F = false := by decide
theorem restore_identity :
    ∀ c : Claim, liveBefore c = true := by
  intro c
  rfl
