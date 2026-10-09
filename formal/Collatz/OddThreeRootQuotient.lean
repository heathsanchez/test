import Collatz.ThreeRootConsequenceNormalForm

namespace CollatzFinal

/-!
V127: consequence-relative quotient contraction to ODD positive multiples
of three (residue 3 modulo 6), with BOTH genuine future meeting clocks.

The full positive Collatz conjecture is equivalent to checking convergence
only on the roots r ≡ 3 mod 6. This does NOT prove the roots terminate.

An apparent step through the canonical root normalizer need not decrease
the source or its root representative: any odd 3-root 6*t+3 takes one
step to 9*t+5, whose V126 canonical root is exactly 6*t+3.
Thus adding a root normalizer does not create descent, only verified
equivalence-class representation.
-/

/-- Pure halving of an EVEN positive multiple of three preserves
its ternary root class and strictly reduces the current value.
This proof is local to positive multiples of 3, not a global
Collatz contraction argument. -/
theorem three_even_half
    (n : Nat) (hn : 0 < n) (h3 : n % 3 = 0)
    (heven : n % 2 = 0) :
    0 < n / 2 ∧ n / 2 < n ∧
    (n / 2) % 3 = 0 ∧ shortcut n = n / 2 := by
  have hlt : n / 2 < n := Nat.div_lt_self hn (by decide)
  have hshortcut : shortcut n = n / 2 := by
    simp only [shortcut, if_pos heven]
  constructor
  · omega
  constructor
  · exact hlt
  constructor
  · omega
  · exact hshortcut

/-- Every POSITIVE multiple of three reaches some positive ODD
multiple of three by a genuine finite forward shortcut prefix. -/
theorem every_three_root_reaches_odd_three_root :
    ∀ n : Nat, 0 < n → n % 3 = 0 →
      ∃ oddRoot clock : Nat,
        0 < oddRoot ∧ oddRoot % 2 = 1 ∧
        oddRoot % 3 = 0 ∧
        iter shortcut clock n = oddRoot := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
      intro hn h3
      by_cases hodd : n % 2 = 1
      · exact ⟨n, 0, hn, hodd, h3, rfl⟩
      · have heven : n % 2 = 0 := by omega
        obtain ⟨hpos, hlt, hhalf3, hstep⟩ :=
          three_even_half n hn h3 heven
        obtain ⟨r, k, hrpos, hrodd, hr3, hreach⟩ :=
          ih (n / 2) hlt hpos hhalf3
        refine ⟨r, k + 1, hrpos, hrodd, hr3, ?_⟩
        change iter shortcut k (shortcut n) = r
        rw [hstep]
        exact hreach

/-- The protected FUTURE equivalence class of every positive natural
contains an ODD positive multiple-of-three representative.
Two independent clocks are retained: one for the source, one for the
root. No strict inequality between root and source is claimed. -/
theorem every_positive_meets_odd_three_root
    (n : Nat) (hn : 0 < n) :
    ∃ root a b : Nat,
      0 < root ∧ root % 2 = 1 ∧ root % 3 = 0 ∧
      iter shortcut a n = iter shortcut b root := by
  obtain ⟨p, k, hp, hthree, _hbound, hpn⟩ :=
    every_positive_has_bounded_three_root n hn
  obtain ⟨root, l, hrpos, hrodd, hrthree, hproot⟩ :=
    every_three_root_reaches_odd_three_root p hp hthree
  refine ⟨root, l, k, hrpos, hrodd, hrthree, ?_⟩
  calc
    iter shortcut l n =
        iter shortcut l (iter shortcut k p) := by rw [hpn]
    _ = iter shortcut (k + l) p := (iter_add shortcut k l p).symm
    _ = iter shortcut (l + k) p := by rw [Nat.add_comm]
    _ = iter shortcut k (iter shortcut l p) := iter_add shortcut l k p
    _ = iter shortcut k root := by rw [hproot]

theorem odd_three_root_mod_six
    (n : Nat) (hodd : n % 2 = 1) (hthree : n % 3 = 0) :
    n % 6 = 3 := by omega

/-- Universal Collatz is equivalent to termination just on
the POSITIVE odd multiples-of-three representative class (3 mod 6).
It remains an OPEN theorem on that restricted domain. -/
theorem collatz_iff_odd_three_roots_terminate :
    (∀ n : Nat, 0 < n → CollatzGood n) ↔
    (∀ r : Nat, 0 < r → r % 6 = 3 → CollatzGood r) := by
  constructor
  · intro hall r hr _
    exact hall r hr
  · intro hroot n hn
    obtain ⟨root, a, b, hpos, hodd, hthree, hmeet⟩ :=
      every_positive_meets_odd_three_root n hn
    have hr6 : root % 6 = 3 := odd_three_root_mod_six root hodd hthree
    have hg : CollatzGood root := hroot root hpos hr6
    have hfuture : CollatzGood (iter shortcut b root) :=
      eventually_iter_forward shortcut Terminal
        terminal_forward_invariant hg b
    have hon : CollatzGood (iter shortcut a n) := by
      rw [hmeet]
      exact hfuture
    obtain ⟨k, ht⟩ := hon
    exact ⟨a + k, by simpa [iter_add] using ht⟩

/-- A NEGATIVE control against confusing class normalization with
source progress: after one step, each odd 3-root selects itself
under the exact V126 residue-5 canonical lift. -/
theorem odd_three_root_first_step_normalization_stutters (t : Nat) :
    (6 * t + 3) % 6 = 3 ∧
    iter shortcut 1 (6 * t + 3) = 9 * t + 5 := by
  constructor
  · omega
  · have heq : 6 * t + 3 = 3 + 6 * t := by omega
    rw [heq]
    exact root_represents_mod9_five t

#print axioms three_even_half
#print axioms every_three_root_reaches_odd_three_root
#print axioms every_positive_meets_odd_three_root
#print axioms odd_three_root_mod_six
#print axioms collatz_iff_odd_three_roots_terminate
#print axioms odd_three_root_first_step_normalization_stutters

end CollatzFinal
