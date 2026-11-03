set_option autoImplicit false
universe u
example {C : Type u} {P : Prop} (p q : P) (F : C → C → P → Prop)
    (a b : C) (w : F a b p) : F a a q := w
