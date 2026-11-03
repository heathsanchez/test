set_option autoImplicit false
universe u
example {C : Type u} {P Q : Prop} (p : P) (q : Q) (F : C → C → P → Prop)
    (a b : C) (w : F a b p) : F a b q := w
