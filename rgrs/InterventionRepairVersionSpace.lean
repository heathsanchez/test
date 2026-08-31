import Std

namespace InterventionRepairVersionSpace

inductive World where | A | B
  deriving DecidableEq

def x : List Bool := [false, true]

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

theorem old_grammar_exhausted :
    ∀ e : OldExperiment, V .A (runOld e x) = V .B (runOld e x) := by
  intro e
  cases e <;> rfl

inductive NewExperiment where
  | delete0
  | delete1
  deriving DecidableEq

def runNew : NewExperiment → List Bool → List Bool
  | .delete0, [_a,b] => [b]
  | .delete1, [a,_b] => [a]
  | _, xs => xs

def ResolvesResidual (e : NewExperiment) : Prop :=
  V .A (runNew e x) ≠ V .B (runNew e x)

theorem delete0_resolves : ResolvesResidual .delete0 := by
  simp [ResolvesResidual, V, runNew, x]

theorem delete1_resolves : ResolvesResidual .delete1 := by
  simp [ResolvesResidual, V, runNew, x]

theorem candidate_repairs_are_distinct :
    NewExperiment.delete0 ≠ NewExperiment.delete1 := by
  intro h
  cases h

theorem residual_does_not_uniquely_determine_repair :
    ∃ d0 d1 : NewExperiment,
      d0 ≠ d1 ∧ ResolvesResidual d0 ∧ ResolvesResidual d1 := by
  exact ⟨.delete0, .delete1, candidate_repairs_are_distinct,
    delete0_resolves, delete1_resolves⟩

theorem no_old_experiment_resolves :
    ¬ ∃ e : OldExperiment, V .A (runOld e x) ≠ V .B (runOld e x) := by
  rintro ⟨e, h⟩
  exact h (old_grammar_exhausted e)

def AttachesToA (e : NewExperiment) : Prop :=
  V .A (runNew e x) = false

theorem delete0_attaches : AttachesToA .delete0 := by
  rfl

theorem delete1_does_not_attach : ¬ AttachesToA .delete1 := by
  intro h
  cases h

/-- Once attachment is included, delete0 is the unique surviving repair. -/
theorem attachment_collapses_version_space :
    ∃ e : NewExperiment,
      (ResolvesResidual e ∧ AttachesToA e) ∧
      ∀ e' : NewExperiment,
        ResolvesResidual e' ∧ AttachesToA e' → e' = e := by
  refine ⟨.delete0, ⟨delete0_resolves, delete0_attaches⟩, ?_⟩
  intro e he
  cases e
  · rfl
  · exact False.elim (delete1_does_not_attach he.2)

theorem verified_failure_yields_version_space_before_selection :
    (¬ ∃ e : OldExperiment, V .A (runOld e x) ≠ V .B (runOld e x)) ∧
    (∃ d0 d1 : NewExperiment,
      d0 ≠ d1 ∧ ResolvesResidual d0 ∧ ResolvesResidual d1) ∧
    (∃ e : NewExperiment,
      (ResolvesResidual e ∧ AttachesToA e) ∧
      ∀ e' : NewExperiment,
        ResolvesResidual e' ∧ AttachesToA e' → e' = e) := by
  exact ⟨no_old_experiment_resolves,
    residual_does_not_uniquely_determine_repair,
    attachment_collapses_version_space⟩

#check old_grammar_exhausted
#check no_old_experiment_resolves
#check residual_does_not_uniquely_determine_repair
#check attachment_collapses_version_space
#check verified_failure_yields_version_space_before_selection

end InterventionRepairVersionSpace
