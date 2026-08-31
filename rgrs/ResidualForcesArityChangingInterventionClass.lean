import Std

namespace ResidualForcesArityChangingInterventionClass

inductive World where | A | B
  deriving DecidableEq

/-- Frozen accepted trace. -/
def x : List Bool := [false, true]

/-- The two verifier worlds agree on every length-2 observation but disagree on
    specific singleton observations. -/
def V : World → List Bool → Bool
  | .A, [true] => false
  | .B, [true] => true
  | .A, [false] => true
  | .B, [false] => false
  | _, [_a, _b] => true
  | _, _ => false

/-- Any intervention whose result still has arity 2 is verifier-blind to the
    residual in this witness. -/
theorem every_length_two_result_is_blind
    (ys : List Bool) (h : ys.length = 2) :
    V .A ys = V .B ys := by
  cases ys with
  | nil => contradiction
  | cons a ys =>
      cases ys with
      | nil => contradiction
      | cons b ys =>
          cases ys with
          | nil => rfl
          | cons c ys => simp at h

/-- Therefore any successful repair must leave the old arity-preserving class. -/
theorem separating_repair_must_change_arity
    (f : List Bool → List Bool)
    (hsep : V .A (f x) ≠ V .B (f x)) :
    (f x).length ≠ 2 := by
  intro hlen
  exact hsep (every_length_two_result_is_blind (f x) hlen)

/-- Evidence-generated deletion candidates are arity-changing. -/
def delete0 : List Bool → List Bool
  | [_a, b] => [b]
  | xs => xs

def delete1 : List Bool → List Bool
  | [a, _b] => [a]
  | xs => xs

theorem delete0_changes_arity : (delete0 x).length ≠ 2 := by decide
theorem delete1_changes_arity : (delete1 x).length ≠ 2 := by decide

theorem delete0_separates : V .A (delete0 x) ≠ V .B (delete0 x) := by decide
theorem delete1_separates : V .A (delete1 x) ≠ V .B (delete1 x) := by decide

/-- The residual determines a necessary constructor-class constraint without
    uniquely choosing a constructor: successful repair must be arity-changing,
    and at least two distinct arity-changing repairs satisfy that constraint. -/
theorem residual_forces_arity_changing_intervention_class :
    (∀ f : List Bool → List Bool,
      V .A (f x) ≠ V .B (f x) → (f x).length ≠ 2) ∧
    delete0 ≠ delete1 ∧
    V .A (delete0 x) ≠ V .B (delete0 x) ∧
    V .A (delete1 x) ≠ V .B (delete1 x) := by
  refine ⟨separating_repair_must_change_arity, ?_, delete0_separates, delete1_separates⟩
  intro h
  have := congrFun h x
  decide at this

#check every_length_two_result_is_blind
#check separating_repair_must_change_arity
#check residual_forces_arity_changing_intervention_class

end ResidualForcesArityChangingInterventionClass
