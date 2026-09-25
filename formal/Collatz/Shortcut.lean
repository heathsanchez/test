import Collatz.FinalKernel

namespace CollatzFinal

def shortcut (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else (3 * n + 1) / 2

theorem shortcut_one : shortcut 1 = 2 := by
  decide

theorem shortcut_two : shortcut 2 = 1 := by
  decide

def Terminal (n : Nat) : Prop :=
  n = 1 ∨ n = 2

theorem terminal_forward_invariant :
    ForwardInvariant shortcut Terminal := by
  intro n hn
  rcases hn with rfl | rfl
  · exact Or.inr shortcut_one
  · exact Or.inl shortcut_two

def CollatzGood (n : Nat) : Prop :=
  Eventually shortcut Terminal n

theorem lower_merge_closes_minimal_collatz_bad
    {n : Nat}
    (hmin : MinimalBad (fun x => ¬ CollatzGood x) n) :
    ∀ p, ¬ LowerMerge shortcut n p := by
  exact minimal_bad_has_no_lower_merge
    shortcut Terminal terminal_forward_invariant hmin

theorem terminal_eventually_one :
    ∀ n, Terminal n → Eventually shortcut (fun x => x = 1) n := by
  intro n hn
  rcases hn with rfl | rfl
  · exact ⟨0, rfl⟩
  · exact ⟨1, by simp [iter, shortcut_two]⟩

theorem collatzGood_eventually_one
    {n : Nat}
    (h : CollatzGood n) :
    Eventually shortcut (fun x => x = 1) n := by
  obtain ⟨k, hk⟩ := h
  have ht : Eventually shortcut (fun x => x = 1) (iter shortcut k n) :=
    terminal_eventually_one (iter shortcut k n) hk
  obtain ⟨l, hl⟩ := ht
  exact ⟨k + l, by simpa [iter_add] using hl⟩

end CollatzFinal
