-- Source-authentic proof-irrelevance probe for Nucleus C239.
-- The equality should be definitional in Lean because (A → A) : Prop.
import Init

namespace ProofIrrel

theorem app_proof_irrel (A : Prop) (q : A → A)
    (f : (A → A) → Nat) :
    f (fun a : A => a) = f q := by
  rfl

-- Same logical equality with the proof arguments declared as global constants.
-- This isolates source binding origin from the dependent equality itself.
axiom A0 : Prop
axiom q0 : A0 → A0
axiom f0 : (A0 → A0) → Nat

theorem global_app_proof_irrel :
    f0 (fun a : A0 => a) = f0 q0 := by
  rfl

theorem benign_true : True := True.intro

end ProofIrrel
