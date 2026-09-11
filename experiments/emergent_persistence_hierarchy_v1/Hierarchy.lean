structure Account where
  genesis : Nat
  saved : Nat
  maintenance : Nat

def Account.profitable (a : Account) : Prop := a.genesis + a.maintenance < a.saved

inductive Evidence where
  | verified : String → Evidence
  | residual : String → Evidence

inductive Licensed where
  | retain : Evidence → Account → Licensed
  | revoke : Evidence → Licensed

def coldTotal : Nat := 1928
def adaptiveTotal : Nat := 812
def deepAblationTotal : Nat := 1865
def shallowAblationTotal : Nat := 880

theorem amortized_advantage : adaptiveTotal < coldTotal := by decide
theorem deeper_ablation_broader :
    deepAblationTotal - adaptiveTotal > shallowAblationTotal - adaptiveTotal := by decide

theorem no_unlicensed_constructor (x : Licensed) :
    (∃ e a, x = .retain e a) ∨ (∃ e, x = .revoke e) := by
  cases x <;> simp
