set_option autoImplicit false
universe u
example {C : Type u} (p q : C) (F : C → C → C → Prop)
    (a b : C) (w : F a b p) : F a b q := w
