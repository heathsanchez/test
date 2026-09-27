import Collatz.HardFirstCrossing

namespace CollatzFinal
namespace SourceProduct

/-- The exact odd shortcut predecessor when it is admissible. -/
def inverseOdd (y : Nat) : Nat := (2 * y - 1) / 3

/-- Repeatedly take the candidate odd predecessor. -/
def inverseOddChain (y : Nat) : Nat → Nat
  | 0 => y
  | m + 1 => inverseOdd (inverseOddChain y m)

/-- Every reverse step through depth m is arithmetically admissible. -/
def InverseOddAdmissible (y m : Nat) : Prop :=
  ∀ i, i < m → inverseOddChain y i % 3 = 2

theorem shortcut_inverseOdd_of_mod3_two
    {y : Nat}
    (hy : y % 3 = 2) :
    shortcut (inverseOdd y) = y := by
  have h := inverse_odd_predecessor_of_mod3_two hy
  simpa [inverseOdd] using h.2.2

/-- An admissible reverse-odd chain is an exact shortcut predecessor chain. -/
theorem inverseOddChain_exact
    {y m : Nat}
    (hadm : InverseOddAdmissible y m) :
    iter shortcut m (inverseOddChain y m) = y := by
  induction m with
  | zero =>
      simp [inverseOddChain, iter]
  | succ m ih =>
      have hm : inverseOddChain y m % 3 = 2 :=
        hadm m (Nat.lt_succ_self m)
      have hadm' : InverseOddAdmissible y m := by
        intro i hi
        exact hadm i (Nat.lt_trans hi (Nat.lt_succ_self m))
      change iter shortcut m
        (shortcut (inverseOdd (inverseOddChain y m))) = y
      rw [shortcut_inverseOdd_of_mod3_two hm]
      exact ih hadm'

/-- Every nonempty admissible reverse-odd chain ends at a positive integer. -/
theorem inverseOddChain_positive
    {y m : Nat}
    (hmpos : 0 < m)
    (hadm : InverseOddAdmissible y m) :
    0 < inverseOddChain y m := by
  cases m with
  | zero => omega
  | succ m =>
      have hm : inverseOddChain y m % 3 = 2 :=
        hadm m (Nat.lt_succ_self m)
      have hp := inverse_odd_predecessor_of_mod3_two hm
      simpa [inverseOddChain, inverseOdd] using hp.1

/-- Universal reverse-cone barrier: on any no-ordinary-exit endpoint, every
nonempty admissible all-odd reverse chain terminates at or above the source. -/
theorem no_ordinary_exit_inverseOddChain_ge
    {n y m : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hmpos : 0 < m)
    (hadm : InverseOddAdmissible y m) :
    n ≤ inverseOddChain y m := by
  have hp : 0 < inverseOddChain y m :=
    inverseOddChain_positive hmpos hadm
  have hexact : iter shortcut m (inverseOddChain y m) = y :=
    inverseOddChain_exact hadm
  apply Nat.le_of_not_gt
  intro hlt
  exact hno (Or.inr (Or.inr
    ⟨inverseOddChain y m, m, hp, hlt, hexact⟩))

/-- The same reverse-cone barrier holds at every point of a hypothetical
minimal positive bad orbit. -/
theorem minimal_bad_inverseOddChain_ge
    {n k m : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hmpos : 0 < m)
    (hadm : InverseOddAdmissible (iter shortcut k n) m) :
    n ≤ inverseOddChain (iter shortcut k n) m := by
  exact no_ordinary_exit_inverseOddChain_ge
    (minimal_bad_has_no_ordinary_exit hmin k) hmpos hadm

/-- In particular, every hard first-crossing endpoint satisfies the entire
admissible reverse-odd cone barrier, not just the depth-one mod-3 case. -/
theorem hard_first_crossing_inverseOddChain_ge
    {n k m : Nat}
    (hhard : HardFirstCrossing n k)
    (hmpos : 0 < m)
    (hadm : InverseOddAdmissible (iter shortcut (k + 1) n) m) :
    n ≤ inverseOddChain (iter shortcut (k + 1) n) m := by
  exact no_ordinary_exit_inverseOddChain_ge hhard.2 hmpos hadm

#print axioms shortcut_inverseOdd_of_mod3_two
#print axioms inverseOddChain_exact
#print axioms inverseOddChain_positive
#print axioms no_ordinary_exit_inverseOddChain_ge
#print axioms minimal_bad_inverseOddChain_ge
#print axioms hard_first_crossing_inverseOddChain_ge

end SourceProduct
end CollatzFinal
