import Std

namespace ResidualForcesArityChangingInterventionClass

inductive World where | A | B
  deriving DecidableEq

def x : List Bool := [false, true]

def V : World → List Bool → Bool
  | .A, [true] => false
  | .B, [true] => true
  | .A, [false] => true
  | .B, [false] => false
  | _, [_a, _b] => true
  | _, _ => false

theorem every_length_two_result_is_blind
    (ys : List Bool) (h : ys.length = 2) :
    V .A ys = V .B ys := by
  cases ys with
  | nil => simp at h
  | cons a ys =>
      cases ys with
      | nil => simp at h
      | cons b ys =>
          cases ys with
          | nil =>
              cases a <;> cases b <;> rfl
          | cons c ys => simp at h

theorem separating_repair_must_change_arity
    (f : List Bool → List Bool)
    (hsep : V .A (f x) ≠ V .B (f x)) :
    (f x).length ≠ 2 := by
  intro hlen
  exact hsep (every_length_two_result_is_blind (f x) hlen)

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

theorem delete_repairs_are_distinct : delete0 ≠ delete1 := by
  intro h
  have hx := congrFun h x
  simp [delete0, delete1, x] at hx

theorem residual_forces_arity_changing_intervention_class :
    (∀ f : List Bool → List Bool,
      V .A (f x) ≠ V .B (f x) → (f x).length ≠ 2) ∧
    delete0 ≠ delete1 ∧
    V .A (delete0 x) ≠ V .B (delete0 x) ∧
    V .A (delete1 x) ≠ V .B (delete1 x) := by
  exact ⟨separating_repair_must_change_arity,
    delete_repairs_are_distinct,
    delete0_separates,
    delete1_separates⟩

#check every_length_two_result_is_blind
#check separating_repair_must_change_arity
#check delete_repairs_are_distinct
#check residual_forces_arity_changing_intervention_class

end ResidualForcesArityChangingInterventionClass
