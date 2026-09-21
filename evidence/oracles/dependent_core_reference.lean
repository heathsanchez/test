/- Lean 4.29.1 reference obligations for G2-001 inference/conversion. -/

universe u

def annotatedId (A : Sort u) (x : A) : A := x

example (A : Sort u) (x : A) : annotatedId A x = x := rfl

example (P : Prop) (p : P) : (let x : P := p; x) = p := rfl

def dependentApply (f : (P : Prop) → P) (P : Prop) : P := f P
