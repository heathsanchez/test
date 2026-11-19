-- Source-authentic proof-irrelevance probe for Nucleus C239.
-- The equality should be definitional in Lean because (A → A) : Prop.
import Init

namespace ProofIrrel

theorem app_proof_irrel (A : Prop) (q : A → A)
    (f : (A → A) → Nat) :
    f (fun a : A => a) = f q := by
  rfl

theorem benign_true : True := True.intro

end ProofIrrel
