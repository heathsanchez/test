import Collatz.GuardedExitObligation
import Collatz.EventualMacroProgress
import Collatz.GuardedDyadicSwitch

namespace CollatzFinal.SourceProduct

/-- An explicit universal normalization depth, independent of orbit growth. -/
theorem source_lt_two_pow_successor (n : Nat) : n < 2 ^ (n + 1) := by
  induction n with
  | zero => decide
  | succ n ih =>
      rw [Nat.pow_succ]
      omega

theorem iter_step_stateAt (n k j : Nat) :
    iter step j (stateAt n k) = stateAt n (k + j) := by
  induction j generalizing k with
  | zero => simp [iter]
  | succ j ih =>
      change iter step j (stateAt n (k + 1)) = stateAt n (k + (j + 1))
      simpa [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using ih (k + 1)

theorem zero_tail_iter {s : State} (hz : s.tail = 0) (j : Nat) :
    (iter step j s).tail = 0 := by
  induction j generalizing s with
  | zero => exact hz
  | succ j ih => exact ih (tail_zero_persists s hz)

/-- Coverage of the exact state representation for every hypothetical no-exit
natural orbit. This does not assert admission to a narrower return grammar. -/
theorem no_exit_source_eventually_zero_tail
    (n : Nat) (hn : 0 < n)
    (hno : forall k, Not (OrdinaryExit n (iter shortcut k n))) :
    forall j, ZeroTailLive (stateAt n (n + 1 + j)) := by
  intro j
  constructor
  · constructor
    · exact ⟨n, n + 1 + j, hn, rfl⟩
    · exact fun hx => hno _ ((exit_stateAt_iff_ordinary n _).mp hx)
  · rw [← iter_step_stateAt]
    exact zero_tail_iter
      (at_tail_zero_of_source_lt_pow hn (source_lt_two_pow_successor n)) j

/-- The rank arithmetic works when the actual switch has zero injection.
The dyadic orders imply nonzero defects; depth must be positive. -/
theorem zero_injection_strict_rank
    (x y A : Int) (v w D : Nat)
    (hx : DyadicOrder x v) (hy : DyadicOrder y w)
    (hA : A % 2 = 1) (hD : 0 < D)
    (hstep : (2 : Int)^D * y = A * x) : w < v := by
  obtain ⟨hle, hout⟩ := dyadic_switch_zero_injection hx hA hstep
  have he := dyadic_order_unique hy hout
  omega

/-- A natural-valued rank is well-founded, with an explicit chain bound. -/
theorem no_infinite_nat_rank_decrease
    (rank : Nat → Nat) (hdec : forall i, rank (i + 1) < rank i) : False := by
  have hbound : forall i, rank i + i ≤ rank 0 := by
    intro i
    induction i with
    | zero => omega
    | succ i ih =>
        have hd := hdec i
        omega
  have hbad := hbound (rank 0 + 1)
  omega

/-- Finite forward-closed bank containing all smaller positive sources than 27.
Its closure certifies absence of any smaller-source merge at the witness. -/
def Small27 (y : Nat) : Prop := y ∈ [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 32, 35, 38, 40, 44, 53, 80]

theorem smaller_than_27_in_bank (p : Nat) (hp : 0 < p) (hlt : p < 27) :
    Small27 p := by
  simp only [Small27, List.mem_cons, List.not_mem_nil, or_false]
  omega

theorem small27_forward : ForwardInvariant shortcut Small27 := by
  intro y hy
  simp only [Small27, List.mem_cons, List.not_mem_nil, or_false] at hy
  rcases hy with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;> unfold Small27 <;> decide

theorem small27_iter (p b : Nat) (hp : Small27 p) :
    Small27 (iter shortcut b p) := by
  induction b generalizing p with
  | zero => exact hp
  | succ b ih => exact ih (shortcut p) (small27_forward p hp)

theorem small27_le_80 (y : Nat) (hy : Small27 y) : y ≤ 80 := by
  simp only [Small27, List.mem_cons, List.not_mem_nil, or_false] at hy
  omega

theorem no_ordinary_exit_27_above_80 (y : Nat) (hy : 80 < y) :
    Not (OrdinaryExit 27 y) := by
  intro hx
  rcases hx with ht | hd | hm
  · rcases ht with ht | ht <;> omega
  · omega
  · rcases hm with ⟨p,b,hp,hlt,heq⟩
    have hsmall := small27_iter p b (smaller_than_27_in_bank p hp hlt)
    rw [heq] at hsmall
    have hb := small27_le_80 y hsmall
    omega

/-- All four witness endpoints are actual zero-tail live states, not abstract
integer solutions. This finite segment is not an infinite bad orbit. -/
theorem source_27_recharge_segment_live :
    ZeroTailLive (stateAt 27 12) ∧ ZeroTailLive (stateAt 27 13) ∧
    ZeroTailLive (stateAt 27 14) ∧ ZeroTailLive (stateAt 27 15) := by
  have make (k y : Nat) (he : iter shortcut k 27 = y)
      (hy : 80 < y) (hk : 27 < 2 ^ k) : ZeroTailLive (stateAt 27 k) := by
    constructor
    · constructor
      · exact ⟨27, k, by decide, rfl⟩
      · intro hx
        have ho := (exit_stateAt_iff_ordinary 27 k).mp hx
        rw [he] at ho
        exact no_ordinary_exit_27_above_80 y hy ho
    · exact at_tail_zero_of_source_lt_pow (by decide) hk
  exact ⟨make 12 137 (by decide) (by decide) (by decide),
    make 13 206 (by decide) (by decide) (by decide),
    make 14 103 (by decide) (by decide) (by decide),
    make 15 155 (by decide) (by decide) (by decide)⟩

/-- The three-step actual macro expands with negative original-floor budget. -/
theorem source_27_macro_budget :
    iter shortcut 3 137 = 155 ∧
    (8 : Int) * 155 = 9 * 137 + 7 ∧
    affineBudget 9 7 8 27 = -34 := by decide

/-- The basic odd-step reference has defect -m-1. Equal-order injection
raises its order from 1 to 2 on this actual nonpositive-budget macro. -/
theorem source_27_macro_recharges :
    DyadicOrder (returnDefect 3 1 2 137) 1 ∧
    DyadicOrder (returnDefect 3 1 2 155) 2 ∧
    DyadicOrder (returnInjection 3 1 2 9 7 8) 1 := by
  exact ⟨⟨-69, by decide, by decide⟩,
    ⟨-39, by decide, by decide⟩, ⟨-3, by decide, by decide⟩⟩

/-- Its own centre still spends exactly three dyadic bits. The missing rule
is about choosing/resetting centres, not failure of self-transport. -/
theorem source_27_macro_own_defect_consumption :
    DyadicOrder (returnDefect 9 7 8 137) 4 ∧
    DyadicOrder (returnDefect 9 7 8 155) 1 := by
  exact ⟨⟨-9, by decide, by decide⟩, ⟨-81, by decide, by decide⟩⟩

/-- Reject universal strict decrease of this fixed-reference rank for arbitrary
actual negative-budget macros. No membership in a narrower frozen protected
return grammar is asserted. Eventual progress remains possible. -/
theorem fixed_reference_rank_not_universal :
    Not (forall v w : Nat,
      DyadicOrder (returnDefect 3 1 2 137) v →
      DyadicOrder (returnDefect 3 1 2 155) w → w < v) := by
  intro h
  have hh := h 1 2 source_27_macro_recharges.1 source_27_macro_recharges.2.1
  omega

#print axioms no_exit_source_eventually_zero_tail
#print axioms zero_injection_strict_rank
#print axioms no_infinite_nat_rank_decrease
#print axioms source_27_recharge_segment_live
#print axioms source_27_macro_budget
#print axioms source_27_macro_recharges
#print axioms source_27_macro_own_defect_consumption
#print axioms fixed_reference_rank_not_universal

end CollatzFinal.SourceProduct
