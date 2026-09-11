universe u v w

namespace FutureConsequenceKernel

structure ActionSystem (M : Type u) (A : Type v) where
  one : M
  comp : M → M → M
  run : M → A → A
  one_run : ∀ a, run one a = a
  comp_run : ∀ m n a, run (comp m n) a = run m (run n a)

variable {M : Type u} {A : Type v} {K : Type w}
variable (S : ActionSystem M A) (e : A → K)

def FutureEq (a b : A) : Prop :=
  ∀ σ : M, e (S.run σ a) = e (S.run σ b)

theorem futureEq_refl (a : A) : FutureEq S e a a := by
  intro σ
  rfl

theorem futureEq_symm {a b : A} (h : FutureEq S e a b) :
    FutureEq S e b a := by
  intro σ
  exact (h σ).symm

theorem futureEq_trans {a b c : A} (hab : FutureEq S e a b)
    (hbc : FutureEq S e b c) : FutureEq S e a c := by
  intro σ
  exact (hab σ).trans (hbc σ)

theorem outcome_respects {a b : A} (h : FutureEq S e a b) : e a = e b := by
  rw [← S.one_run a, ← S.one_run b]
  exact h S.one

theorem action_respects (τ : M) {a b : A} (h : FutureEq S e a b) :
    FutureEq S e (S.run τ a) (S.run τ b) := by
  intro σ
  rw [← S.comp_run σ τ a, ← S.comp_run σ τ b]
  exact h (S.comp σ τ)

structure AdmissibleCongruence (R : A → A → Prop) : Prop where
  refl : ∀ a, R a a
  symm : ∀ {a b}, R a b → R b a
  trans : ∀ {a b c}, R a b → R b c → R a c
  stable : ∀ (σ : M) {a b}, R a b → R (S.run σ a) (S.run σ b)
  observes : ∀ {a b}, R a b → e a = e b

theorem greatest_congruence {R : A → A → Prop}
    (hR : AdmissibleCongruence S e R) {a b : A} (hab : R a b) :
    FutureEq S e a b := by
  intro σ
  exact hR.observes (hR.stable σ hab)

def quotientSetoid : Setoid A where
  r := FutureEq S e
  iseqv := ⟨futureEq_refl S e, futureEq_symm S e, futureEq_trans S e⟩

abbrev Q := @Quotient A (quotientSetoid S e)

def descendedAction (τ : M) : Q S e → Q S e :=
  Quotient.lift
    (fun a => Quotient.mk (quotientSetoid S e) (S.run τ a))
    (by
      intro a b h
      exact Quotient.sound (action_respects S e τ h))

def descendedOutcome : Q S e → K :=
  Quotient.lift e (by
    intro a b h
    exact outcome_respects S e h)

theorem descended_action_mk (τ : M) (a : A) :
    descendedAction S e τ (Quotient.mk _ a) = Quotient.mk _ (S.run τ a) := rfl

theorem descended_outcome_mk (a : A) :
    descendedOutcome S e (Quotient.mk _ a) = e a := rfl

theorem separator_necessity {Z : Type*} (q : A → Z)
    (adequate : ∀ {a b}, q a = q b → FutureEq S e a b)
    {a b : A} (σ : M) (hsep : e (S.run σ a) ≠ e (S.run σ b)) :
    q a ≠ q b := by
  intro hq
  exact hsep (adequate hq σ)

end FutureConsequenceKernel
