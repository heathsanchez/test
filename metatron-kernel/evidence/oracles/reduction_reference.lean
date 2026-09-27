/-
Lean 4.29.1 reference obligations for the beta and zeta transitions retained
by G1-002. Delta is qualified separately against Arena declarations because
its availability depends on declaration transparency.
-/

universe u

example (A : Sort u) (a : A) : (fun x => x) a = a := rfl

example (A : Sort u) (a : A) : (let x := a; x) = a := rfl
