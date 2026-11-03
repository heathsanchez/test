set_option autoImplicit false
universe u
example {C : Type u} {P : Prop} (p q : P) (F G : C → C → P → Prop)
    (a b : C) (w : F a b p) : G a b q := w
