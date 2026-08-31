import Std

namespace LocalResidualCannotIdentifyGlobalConstructor

/-- Current residual-bearing evidence. -/
def x : List Bool := [false, true]

/-- A new context not seen by the current residual. -/
def y : List Bool := [true, false]

/-- Two globally different intervention constructors.  Both delete the first
    position on the current evidence x, but they disagree away from x. -/
def constructorA : List Bool → List Bool
  | [_a, b] => [b]
  | xs => xs

/-- On x this behaves exactly like constructorA, but on the reversed pair it
    deletes the second position instead. -/
def constructorB : List Bool → List Bool
  | [false, true] => [true]
  | [true, false] => [true]
  | xs => xs

/-- The current residual cannot distinguish the two constructors because their
    action on the only observed evidence is identical. -/
theorem constructors_agree_on_current_residual :
    constructorA x = constructorB x := by
  rfl

/-- Nevertheless they are genuinely different functions. -/
theorem constructors_are_globally_distinct : constructorA ≠ constructorB := by
  intro h
  have hy := congrFun h y
  simp [constructorA, constructorB, y] at hy

/-- Any verifier consequence that only observes the repaired current evidence
    must give the same verdict for both constructors. -/
theorem every_local_consequence_identifies_them
    (V : List Bool → Bool) :
    V (constructorA x) = V (constructorB x) := by
  rw [constructors_agree_on_current_residual]

/-- Therefore no selector based only on the local repaired output can certify
    which global constructor was used. -/
theorem local_output_cannot_determine_global_constructor :
    ¬ ∃ choose : List Bool → (List Bool → List Bool),
      choose (constructorA x) = constructorA ∧
      choose (constructorB x) = constructorB := by
  rintro ⟨choose, hA, hB⟩
  have hsame : choose (constructorA x) = choose (constructorB x) := by
    rw [constructors_agree_on_current_residual]
  exact constructors_are_globally_distinct (hA.symm.trans (hsame.trans hB))

/-- A fresh context separates the constructors. -/
theorem transfer_context_separates_constructors :
    constructorA y ≠ constructorB y := by
  decide

/-- The pair of outputs on current and transfer contexts is sufficient to keep
    the two constructors distinct. -/
def transferSignature (f : List Bool → List Bool) : List Bool × List Bool :=
  (f x, f y)

theorem transfer_signature_separates :
    transferSignature constructorA ≠ transferSignature constructorB := by
  intro h
  have hy := congrArg Prod.snd h
  exact transfer_context_separates_constructors hy

/-- Exact boundary theorem.

    A current residual may constrain the required behavior and even the
    constructor class, yet cannot identify a global constructor from one local
    action when two distinct constructors coincide there.  A new verifier
    context can expose the difference.  Thus transfer/replay over additional
    contexts is not optional if the retained object is intended to be a global
    constructor rather than a one-instance patch. -/
theorem local_residual_cannot_identify_global_constructor :
    constructorA x = constructorB x ∧
    constructorA ≠ constructorB ∧
    (∀ V : List Bool → Bool,
      V (constructorA x) = V (constructorB x)) ∧
    (¬ ∃ choose : List Bool → (List Bool → List Bool),
      choose (constructorA x) = constructorA ∧
      choose (constructorB x) = constructorB) ∧
    constructorA y ≠ constructorB y ∧
    transferSignature constructorA ≠ transferSignature constructorB := by
  exact ⟨constructors_agree_on_current_residual,
    constructors_are_globally_distinct,
    every_local_consequence_identifies_them,
    local_output_cannot_determine_global_constructor,
    transfer_context_separates_constructors,
    transfer_signature_separates⟩

#check constructors_agree_on_current_residual
#check constructors_are_globally_distinct
#check every_local_consequence_identifies_them
#check local_output_cannot_determine_global_constructor
#check transfer_context_separates_constructors
#check transfer_signature_separates
#check local_residual_cannot_identify_global_constructor

end LocalResidualCannotIdentifyGlobalConstructor
