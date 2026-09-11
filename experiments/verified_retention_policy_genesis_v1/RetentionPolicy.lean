import Std

def dependencyClosed (deps chosen : List Nat) : Prop :=
  ∀ x, x ∈ chosen → ∀ d, d ∈ deps → d ∈ chosen

structure RetentionCertificate where
  chosen : List Nat
  warranted : Prop
  closed : Prop
  withinBudget : Prop

inductive PolicyResult where
  | retained (c : RetentionCertificate)
  | policyResidual (oldCost newCost : Nat) (improves : newCost < oldCost)

def revision_requires_improvement
    (oldCost newCost : Nat) (h : newCost < oldCost) :
    PolicyResult :=
  PolicyResult.policyResidual oldCost newCost h
