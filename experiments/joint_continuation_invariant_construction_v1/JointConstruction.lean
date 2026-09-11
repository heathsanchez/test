inductive Expr where
  | field : Fin 3 → Expr
  | neg : Expr → Expr
  | and : Expr → Expr → Expr
  | or : Expr → Expr → Expr
deriving DecidableEq, Repr

def Expr.eval : Expr → (Fin 3 → Bool) → Bool
  | .field i, r => r i
  | .neg x, r => !(x.eval r)
  | .and x y, r => x.eval r && y.eval r
  | .or x y, r => x.eval r || y.eval r

def sep : Expr :=
  .or (.and (.field 0) (.neg (.field 1)))
      (.and (.neg (.field 0)) (.field 1))

theorem sep_is_xor (r : Fin 3 → Bool) : sep.eval r = (r 0 != r 1) := by
  cases h0 : r 0 <;> cases h1 : r 1 <;> simp [sep, Expr.eval, h0, h1]

def profile (r : Fin 3 → Bool) : Bool × Bool := (r 2, sep.eval r)

theorem separator_refines_collision
    (a b : Fin 3 → Bool) (hobs : a 2 = b 2) (hsep : sep.eval a ≠ sep.eval b) :
    profile a ≠ profile b := by
  intro h
  exact hsep (Prod.mk.inj h).2

theorem ablation_collapses (a b : Fin 3 → Bool) (hobs : a 2 = b 2) :
    (a 2) = (b 2) := hobs
