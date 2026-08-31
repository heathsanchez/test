import Std

namespace FiniteContextsCannotIdentifyUnrestrictedConstructor

/-- A finite verifier suite tests constructors only on finitely many natural
    contexts. -/
def freshContext (cs : List Nat) : Nat := cs.foldl Nat.max 0 + 1

/-- Every listed context is strictly below the generated fresh context. -/
theorem member_lt_fresh (cs : List Nat) :
    ∀ n ∈ cs, n < freshContext cs := by
  intro n hn
  unfold freshContext
  have hle : n ≤ cs.foldl Nat.max 0 := by
    induction cs generalizing n with
    | nil => simp at hn
    | cons a cs ih =>
        simp only [List.foldl_cons]
        have hmem : n = a ∨ n ∈ cs := by simpa using hn
        cases hmem with
        | inl hna =>
            subst n
            have ha : a ≤ Nat.max 0 a := Nat.le_max_right _ _
            have hmono : Nat.max 0 a ≤ cs.foldl Nat.max (Nat.max 0 a) := by
              clear ih
              induction cs generalizing (Nat.max 0 a) with
              | nil => simp
              | cons b bs ih' =>
                  simp only [List.foldl_cons]
                  exact le_trans (Nat.le_max_left _ _) (ih' (Nat.max (Nat.max 0 a) b))
            exact le_trans ha hmono
        | inr hrest =>
            -- The fold accumulator can only increase; apply the induction
            -- hypothesis to the tail and then compare its zero-start fold with
            -- the larger accumulator fold.
            have hn0 : n ≤ cs.foldl Nat.max 0 := ih n hrest
            have hacc : cs.foldl Nat.max 0 ≤ cs.foldl Nat.max (Nat.max 0 a) := by
              clear ih hrest hn0 hn
              induction cs generalizing (Nat.max 0 a) with
              | nil => simp
              | cons b bs ih' =>
                  simp only [List.foldl_cons]
                  apply ih'
            exact le_trans hn0 hacc
  omega

/-- Baseline constructor. -/
def f : Nat → Bool := fun _ => false

/-- A rival constructor that differs only at the fresh, untested context. -/
def g (cs : List Nat) : Nat → Bool :=
  fun n => if n = freshContext cs then true else false

/-- The two constructors agree on every tested context. -/
theorem finite_suite_cannot_separate (cs : List Nat) :
    ∀ n ∈ cs, f n = g cs n := by
  intro n hn
  have hne : n ≠ freshContext cs := by
    have hlt := member_lt_fresh cs n hn
    omega
  simp [f, g, hne]

/-- Yet they are extensionally different globally. -/
theorem constructors_differ_at_fresh_context (cs : List Nat) :
    f (freshContext cs) ≠ g cs (freshContext cs) := by
  simp [f, g]

theorem constructors_globally_distinct (cs : List Nat) : f ≠ g cs := by
  intro h
  have hfresh := congrFun h (freshContext cs)
  exact constructors_differ_at_fresh_context cs hfresh

/-- Exact obstruction: for every finite context suite there exist two globally
    different constructors with identical behavior on every tested context. -/
theorem finite_contexts_cannot_identify_unrestricted_constructor :
    ∀ cs : List Nat,
      ∃ f0 g0 : Nat → Bool,
        f0 ≠ g0 ∧
        (∀ n ∈ cs, f0 n = g0 n) := by
  intro cs
  exact ⟨f, g cs, constructors_globally_distinct cs,
    finite_suite_cannot_separate cs⟩

/-- Consequence for retention: a finite verifier suite cannot justify equality
    of unrestricted constructors from agreement alone.  What it can justify is
    only equality relative to the tested consequence family, unless a smaller
    hypothesis class supplies an independent completeness theorem. -/
def ObservationalEq (cs : List Nat) (u v : Nat → Bool) : Prop :=
  ∀ n ∈ cs, u n = v n

theorem finite_evidence_supports_only_observational_identity :
    ∀ cs : List Nat,
      ∃ u v : Nat → Bool,
        ObservationalEq cs u v ∧ u ≠ v := by
  intro cs
  exact ⟨f, g cs, finite_suite_cannot_separate cs,
    constructors_globally_distinct cs⟩

#check finite_suite_cannot_separate
#check constructors_globally_distinct
#check finite_contexts_cannot_identify_unrestricted_constructor
#check finite_evidence_supports_only_observational_identity

end FiniteContextsCannotIdentifyUnrestrictedConstructor
