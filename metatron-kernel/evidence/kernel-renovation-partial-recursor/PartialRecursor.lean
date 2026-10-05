-- Compatibility probes copied from lean4 PR #15374 at
-- 63da8abdd58db2d6d4f6a648a6e24df2949d6a11, tests/elab/12520_2.lean.
-- Only the declaration names and explicit variable binders are added.

theorem nucleusPartialEq (a : true = true → Bool) :
    (@Eq.rec Bool true (fun _ _ => Bool) (a (Eq.refl true)) _) = a := rfl

theorem nucleusPartialProd (a : Bool × Bool → Bool) :
    @Prod.rec Bool Bool (motive := fun _ => Bool) (fun b c => a (b,c)) = a := rfl
