import Std

namespace FiniteContextsCannotIdentifyUnrestrictedConstructor

/-- A fresh natural context generated beyond every member of the finite suite. -/
def freshContext (cs : List Nat) : Nat := cs.sum + 1

/-- Every member of a finite Nat list is bounded by its sum. -/
theorem member_le_sum (cs : List Nat) :
    ∀ n ∈ cs, n ≤ cs.sum := by
  intro n hn
  induction cs with
  | nil => simp at hn
  | cons a cs ih =>
      simp only [List.sum_cons]
      have hmem : n = a ∨ n ∈ cs := by simpa using hn
      cases hmem with
      | inl hna =>
          subst n
          omega
      | inr hrest =>
          have hle := ih hrest
          omega

/-- Therefore no tested context is the generated fresh one. -/
theorem member_lt_fresh (cs : List Nat) :
    ∀ n ∈ cs, n < freshContext cs := by
  intro n hn
  have hle := member_le_sum cs n hn
  unfold freshContext
  omega

def f : Nat → Bool := fun _ => false

def g (cs : List Nat) : Nat → Bool :=
  fun n => if n = freshContext cs then true else false

theorem finite_suite_cannot_separate (cs : List Nat) :
    ∀ n ∈ cs, f n = g cs n := by
  intro n hn
  have hne : n ≠ freshContext cs := by
    have hlt := member_lt_fresh cs n hn
    omega
  simp [f, g, hne]

theorem constructors_differ_at_fresh_context (cs : List Nat) :
    f (freshContext cs) ≠ g cs (freshContext cs) := by
  simp [f, g]

theorem constructors_globally_distinct (cs : List Nat) : f ≠ g cs := by
  intro h
  have hfresh := congrFun h (freshContext cs)
  exact constructors_differ_at_fresh_context cs hfresh

/-- Exact obstruction: for every finite context suite there exist two globally
    different unrestricted constructors that agree on every tested context. -/
theorem finite_contexts_cannot_identify_unrestricted_constructor :
    ∀ cs : List Nat,
      ∃ f0 g0 : Nat → Bool,
        f0 ≠ g0 ∧
        (∀ n ∈ cs, f0 n = g0 n) := by
  intro cs
  exact ⟨f, g cs, constructors_globally_distinct cs,
    finite_suite_cannot_separate cs⟩

def ObservationalEq (cs : List Nat) (u v : Nat → Bool) : Prop :=
  ∀ n ∈ cs, u n = v n

/-- Finite evidence can certify observational equality on the tested consequence
    family, but not extensional equality of unrestricted constructors. -/
theorem finite_evidence_supports_only_observational_identity :
    ∀ cs : List Nat,
      ∃ u v : Nat → Bool,
        ObservationalEq cs u v ∧ u ≠ v := by
  intro cs
  exact ⟨f, g cs, finite_suite_cannot_separate cs,
    constructors_globally_distinct cs⟩

#check member_lt_fresh
#check finite_suite_cannot_separate
#check constructors_globally_distinct
#check finite_contexts_cannot_identify_unrestricted_constructor
#check finite_evidence_supports_only_observational_identity

end FiniteContextsCannotIdentifyUnrestrictedConstructor
