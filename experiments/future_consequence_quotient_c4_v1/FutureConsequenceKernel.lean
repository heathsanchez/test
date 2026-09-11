universe u v w

namespace FutureConsequenceKernel

structure Act (M : Type u) (A : Type v) [Monoid M] where
  run : M → A → A
  one_run : ∀ a, run 1 a = a
  mul_run : ∀ m n a, run (m * n) a = run m (run n a)

variable {M : Type u} {A : Type v} {K : Type w} [Monoid M]
variable (α : Act M A) (e : A → K)

def FutureEq (a b : A) : Prop :=
  ∀ σ : M, e (α.run σ a) = e (α.run σ b)

theorem futureEq_refl (a : A) : FutureEq α e a a := by
  intro σ
  rfl

theorem futureEq_symm {a b : A} (h : FutureEq α e a b) :
    FutureEq α e b a := by
  intro σ
  exact (h σ).symm

theorem futureEq_trans {a b c : A} (hab : FutureEq α e a b)
    (hbc : FutureEq α e b c) : FutureEq α e a c := by
  intro σ
  exact (hab σ).trans (hbc σ)

theorem outcome_respects {a b : A} (h : FutureEq α e a b) : e a = e b := by
  simpa [α.one_run] using h 1

theorem action_respects (τ : M) {a b : A} (h : FutureEq α e a b) :
    FutureEq α e (α.run τ a) (α.run τ b) := by
  intro σ
  simpa [α.mul_run] using h (σ * τ)

structure AdmissibleCongruence (R : A → A → Prop) : Prop where
  refl : ∀ a, R a a
  symm : ∀ {a b}, R a b → R b a
  trans : ∀ {a b c}, R a b → R b c → R a c
  stable : ∀ (σ : M) {a b}, R a b → R (α.run σ a) (α.run σ b)
  observes : ∀ {a b}, R a b → e a = e b

theorem greatest_congruence {R : A → A → Prop}
    (hR : AdmissibleCongruence α e R) {a b : A} (hab : R a b) :
    FutureEq α e a b := by
  intro σ
  exact hR.observes (hR.stable σ hab)

def QuotientSetoid : Setoid A where
  r := FutureEq α e
  iseqv := ⟨futureEq_refl α e, futureEq_symm α e, futureEq_trans α e⟩

def Q := Quotient (QuotientSetoid α e)

def descendedAction (τ : M) : Q α e → Q α e :=
  Quotient.map (α.run τ) (by
    intro a b h
    exact action_respects α e τ h)

def descendedOutcome : Q α e → K :=
  Quotient.lift e (by
    intro a b h
    exact outcome_respects α e h)

theorem descended_action_mk (τ : M) (a : A) :
    descendedAction α e τ (Quotient.mk _ a) = Quotient.mk _ (α.run τ a) := rfl

theorem descended_outcome_mk (a : A) :
    descendedOutcome α e (Quotient.mk _ a) = e a := rfl

theorem separator_necessity {Z : Type*} (q : A → Z)
    (adequate : ∀ {a b}, q a = q b → FutureEq α e a b)
    {a b : A} (σ : M) (hsep : e (α.run σ a) ≠ e (α.run σ b)) :
    q a ≠ q b := by
  intro hq
  exact hsep (adequate hq σ)

end FutureConsequenceKernel
