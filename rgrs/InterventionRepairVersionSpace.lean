import Std

namespace InterventionRepairVersionSpace

inductive World where | A | B
  deriving DecidableEq

/-- One frozen observation shared by both worlds. -/
def x : List Bool := [false, true]

/-- The two verifier worlds agree on the old experiment grammar but differ under
    two structurally new deletion experiments. -/
def V : World → List Bool → Bool
  | .A, [false, true] => true
  | .B, [false, true] => true
  | .A, [true, false] => false
  | .B, [true, false] => false
  | .A, [true] => false
  | .B, [true] => true
  | .A, [false] => true
  | .B, [false] => false
  | _, _ => false

inductive OldExperiment where
  | keep
  | swap
  deriving DecidableEq

def runOld : OldExperiment → List Bool → List Bool
  | .keep, xs => xs
  | .swap, [a,b] => [b,a]
  | .swap, xs => xs.reverse

/-- The entire old experiment language is exhausted extensionally on the frozen
    observation: every old experiment gives the same verifier consequence in
    both worlds. -/
theorem old_grammar_exhausted :
    ∀ e : OldExperiment, V .A (runOld e x) = V .B (runOld e x) := by
  intro e
  cases e <;> decide

/-- Two distinct one-constructor grammar repairs. -/
inductive NewExperiment where
  | delete0
  | delete1
  deriving DecidableEq

def runNew : NewExperiment → List Bool → List Bool
  | .delete0, [_a,b] => [b]
  | .delete1, [a,_b] => [a]
  | _, xs => xs

/-- Residual-relative repair constraint: the added experiment must expose a
    verifier consequence that separates the currently indistinguishable worlds. -/
def ResolvesResidual (e : NewExperiment) : Prop :=
  V .A (runNew e x) ≠ V .B (runNew e x)

theorem delete0_resolves : ResolvesResidual .delete0 := by decide
theorem delete1_resolves : ResolvesResidual .delete1 := by decide

theorem candidate_repairs_are_distinct :
    NewExperiment.delete0 ≠ NewExperiment.delete1 := by decide

/-- The residual-relative version space has at least two distinct members. -/
theorem residual_does_not_uniquely_determine_repair :
    ∃ d0 d1 : NewExperiment,
      d0 ≠ d1 ∧ ResolvesResidual d0 ∧ ResolvesResidual d1 := by
  exact ⟨.delete0, .delete1, by decide, delete0_resolves, delete1_resolves⟩

/-- Zero new constructors cannot solve the residual because the old language is
    exhaustive and blind.  Each successful repair above adds exactly one new
    constructor, so both are cardinal-minimal extensions of this frozen grammar. -/
theorem no_old_experiment_resolves :
    ¬ ∃ e : OldExperiment, V .A (runOld e x) ≠ V .B (runOld e x) := by
  rintro ⟨e, h⟩
  exact h (old_grammar_exhausted e)

/-- A further attachment consequence can distinguish the two otherwise equally
    minimal repairs.  Here attachment asks that deleting the selected position
    reject world A; delete0 attaches, delete1 does not. -/
def AttachesToA (e : NewExperiment) : Prop :=
  V .A (runNew e x) = false

theorem delete0_attaches : AttachesToA .delete0 := by decide
theorem delete1_does_not_attach : ¬ AttachesToA .delete1 := by decide

/-- Once the attachment constraint is included, the surviving repair is unique. -/
theorem attachment_collapses_version_space :
    ∃! e : NewExperiment, ResolvesResidual e ∧ AttachesToA e := by
  refine ⟨.delete0, ⟨delete0_resolves, delete0_attaches⟩, ?_⟩
  intro e he
  cases e
  · rfl
  · exact False.elim (delete1_does_not_attach he.2)

/-- End-to-end RGRS version-space theorem.

    Exhaustive failure of the old intervention grammar forces a grammar change,
    but the residual alone does not identify a unique representation: two
    distinct one-constructor repairs are equally minimal and both resolve it.
    An additional attachment consequence collapses the version space to one.

    Therefore the developmental seed must be formulated as residual -> necessary
    constraints -> minimal version space -> attachment/verification, not as a
    globally unique residual-to-repair function. -/
theorem verified_failure_yields_version_space_before_selection :
    (¬ ∃ e : OldExperiment, V .A (runOld e x) ≠ V .B (runOld e x)) ∧
    (∃ d0 d1 : NewExperiment,
      d0 ≠ d1 ∧ ResolvesResidual d0 ∧ ResolvesResidual d1) ∧
    (∃! e : NewExperiment, ResolvesResidual e ∧ AttachesToA e) := by
  exact ⟨no_old_experiment_resolves,
    residual_does_not_uniquely_determine_repair,
    attachment_collapses_version_space⟩

#check old_grammar_exhausted
#check no_old_experiment_resolves
#check residual_does_not_uniquely_determine_repair
#check attachment_collapses_version_space
#check verified_failure_yields_version_space_before_selection

end InterventionRepairVersionSpace
