import Collatz.Shortcut

namespace CollatzFinal

theorem regression_iter_zero (k : Nat) : iter shortcut k 0 = 0 := by
  induction k with
  | zero => rfl
  | succ k ih => simpa [iter, shortcut] using ih

theorem regression_zero_not_good : ¬ CollatzGood 0 := by
  rintro ⟨k, hk⟩
  rw [regression_iter_zero] at hk
  simp [Terminal] at hk

theorem regression_old_minimal_is_zero {n : Nat}
    (h : MinimalBad (fun x => ¬ CollatzGood x) n) : n = 0 := by
  by_contra hn
  have hp : 0 < n := by omega
  exact h.2 0 hp regression_zero_not_good

-- This deliberately fails before the positive-domain bridge is implemented.
example {n : Nat}
    (hmin : MinimalBad (fun x => 0 < x ∧ ¬ CollatzGood x) n) :
    ∀ p, 0 < p → ¬ LowerMerge shortcut n p := by
  intro p hp
  exact lower_merge_closes_minimal_collatz_bad hmin p

end CollatzFinal
