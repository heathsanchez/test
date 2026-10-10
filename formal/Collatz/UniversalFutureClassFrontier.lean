import Collatz.ActualOrbitDichotomy
import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-!
V155 — universal positive future-class QED frontier.

SourceProduct already models the actual orbit of every positive Nat
at every depth. This file supplies the exact future-coalescence
equivalence relation, identifies the terminal class, connects that
criterion to the already-qualified empty zero-tail kernel, and
extracts the source-locked obstruction for any hypothetical failure.

It also proves a small but consequential impossibility boundary:
any class label invariant under even doubling and depending on only
a fixed number of low binary digits is constant on positive starts.
Therefore fixed-depth dyadic quotients cannot distinguish a putative
second future class. Any genuine QED must use unbounded source-attached
information and the actual odd affine rule.

ALL biconditionals below are equivalences, NOT proofs of their
positive assertions. In particular, we do not establish that all
positive starts belong to the terminal class; Collatz remains UNKNOWN.
-/

/-- Meeting at independently chosen, genuine shortcut clocks.
    This is the future-protecting distinction; no quotient ghosts. -/
def V155FutureMeet (n m : Nat) : Prop :=
  ∃ i j : Nat, iter shortcut i n = iter shortcut j m

theorem v155_future_meet_refl (n : Nat) :
    V155FutureMeet n n := by
  exact ⟨0,0,rfl⟩

theorem v155_future_meet_symm {n m : Nat}
    (h : V155FutureMeet n m) :
    V155FutureMeet m n := by
  obtain ⟨i,j,hij⟩ := h
  exact ⟨j,i,hij.symm⟩

theorem v155_future_meet_trans {n m p : Nat}
    (h₁ : V155FutureMeet n m)
    (h₂ : V155FutureMeet m p) :
    V155FutureMeet n p := by
  obtain ⟨i,j,hij⟩ := h₁
  obtain ⟨k,l,hkl⟩ := h₂
  refine ⟨i+k,l+j,?_⟩
  calc
    iter shortcut (i+k) n =
        iter shortcut k (iter shortcut i n) :=
      iter_add shortcut i k n
    _ = iter shortcut k (iter shortcut j m) := by rw [hij]
    _ = iter shortcut j (iter shortcut k m) := by
      calc
        _ = iter shortcut (j+k) m :=
          (iter_add shortcut j k m).symm
        _ = iter shortcut (k+j) m := by rw [Nat.add_comm]
        _ = iter shortcut j (iter shortcut k m) :=
          iter_add shortcut k j m
    _ = iter shortcut j (iter shortcut l p) := by rw [hkl]
    _ = iter shortcut (l+j) p :=
      (iter_add shortcut l j p).symm

/-- Exactly the real terminal class. Reaching 1 or 2 is equivalent
    to eventually meeting the genuine 1 <-> 2 trajectory. -/
theorem v155_future_meets_one_iff_good (n : Nat) :
    V155FutureMeet n 1 ↔ CollatzGood n := by
  constructor
  · intro hm
    obtain ⟨i,j,hij⟩ := hm
    have ht : ∀ t : Nat, Terminal (iter shortcut t 1) := by
      intro t
      induction t with
      | zero => exact Or.inl rfl
      | succ t ih =>
          rw [iter_succ_last]
          exact terminal_forward_invariant _ ih
    exact ⟨i, by rw [hij]; exact ht j⟩
  · intro hg
    obtain ⟨i,ht⟩ := hg
    rcases ht with h1 | h2
    · exact ⟨i,0,by simpa [iter] using h1⟩
    · exact ⟨i,1,by simpa [iter,shortcut_one] using h2⟩

/-- One future-coalescence class for positive Nat sources. -/
def V155SinglePositiveFutureClass : Prop :=
  ∀ n : Nat, 0 < n → V155FutureMeet n 1

theorem v155_single_class_iff_collatz :
    V155SinglePositiveFutureClass ↔
      (∀ n : Nat, 0<n → CollatzGood n) := by
  constructor
  · intro h n hn
    exact (v155_future_meets_one_iff_good n).mp (h n hn)
  · intro h n hn
    exact (v155_future_meets_one_iff_good n).mpr (h n hn)

/-- Reconciles two independently built ALL-SOURCE formulations:
    universal future-class uniqueness and the original zero-tail
    post-fixed kernel emptiness. Neither side is established true. -/
theorem v155_zero_tail_kernel_empty_iff_single_class :
    KernelEmpty ZeroTailLive Next ↔
      V155SinglePositiveFutureClass := by
  exact zero_tail_kernel_empty_iff_collatz.trans
    v155_single_class_iff_collatz.symm

/-- If the terminal class is not universal, there is a LEAST bad
    actual positive source, which cannot coalesce with any earlier
    positive source and is necessarily either genuinely nonterminal
    periodic or unbounded without original-source descent.

    All three consequences refer to real Nat orbits and clocks.
    This is a necessary obstruction, NOT its exclusion. -/
theorem v155_failure_has_actual_second_class_obstruction
    (hnot : ¬ V155SinglePositiveFutureClass) :
    ∃ n : Nat,
      MinimalBad PositiveBad n ∧
      (∀ p : Nat, 0<p → p<n → ¬ V155FutureMeet n p) ∧
      ((∃ i k : Nat, 0 < k ∧
        2 < iter shortcut i n ∧
        n ≤ iter shortcut i n ∧
        iter shortcut (i+k) n = iter shortcut i n) ∨
      (∀ B : Nat, ∃ k : Nat,
        B < iter shortcut k n ∧ n ≤ iter shortcut k n)) := by
  have hExists : ∃ n : Nat, MinimalBad PositiveBad n := by
    apply Classical.byContradiction
    intro hnone
    have hall : ∀ n, ¬ MinimalBad PositiveBad n := by
      intro n hn
      exact hnone ⟨n,hn⟩
    have hNoBad : ∀ n, ¬ PositiveBad n :=
      no_bad_of_no_minimal PositiveBad hall
    have hgood : ∀ n, 0<n → CollatzGood n := by
      intro n hn
      apply Classical.byContradiction
      intro hbad
      exact hNoBad n ⟨hn,hbad⟩
    exact hnot (v155_single_class_iff_collatz.mpr hgood)
  obtain ⟨n,hm⟩ := hExists
  refine ⟨n,hm,?_,least_positive_bad_nonterminal_cycle_or_unbounded_no_descent hm⟩
  intro p hp hlt hmeet
  obtain ⟨i,j,hij⟩ := hmeet
  exact (minimal_positive_bad_no_earlier_source_meeting
    hm p i j hp hlt) hij

/-- Powers-of-two stretching preserves ANY genuine future-invariant
    class label; this part needs no odd arithmetic. -/
theorem v155_even_scale_label
    {α : Type} (label : Nat → α)
    (hDouble : ∀ n : Nat, 0<n → label (2*n) = label n) :
    ∀ k n : Nat, 0<n →
      label (2^k*n) = label n := by
  intro k
  induction k with
  | zero =>
      intro n _
      simp
  | succ k ih =>
      intro n hn
      have hpos : 0 < 2^k*n :=
        Nat.mul_pos (Nat.pow_pos (by decide)) hn
      calc
        label (2^(k+1)*n) =
            label (2*(2^k*n)) := by
              congr 1
              simp [Nat.pow_succ, Nat.mul_assoc,
                Nat.mul_comm, Nat.mul_left_comm]
        _ = label (2^k*n) := hDouble _ hpos
        _ = label n := ih n hn

/-- NO-GO for a fixed dyadic-residue complete class label.
    If the label respects true halving and looks at only k low
    bits, all positive integer sources receive the SAME label.

    This is not a no-go for source-indexed, expanding-precision
    arithmetic states: those are the live V85/V134 machinery. -/
theorem v155_fixed_dyadic_future_labels_collapse
    {α : Type} (label : Nat → α) (k : Nat)
    (hDouble : ∀ n : Nat, 0<n → label (2*n) = label n)
    (hResidue : ∀ n m : Nat,
      0<n → 0<m → n % (2^k) = m % (2^k) →
        label n = label m) :
    ∀ n m : Nat, 0<n → 0<m → label n = label m := by
  intro n m hn hm
  have hp : 0 < 2^k*n :=
    Nat.mul_pos (Nat.pow_pos (by decide)) hn
  have hq : 0 < 2^k*m :=
    Nat.mul_pos (Nat.pow_pos (by decide)) hm
  have hres :
      (2^k*n) % (2^k) = (2^k*m) % (2^k) := by
    simp [Nat.mul_mod]
  calc
    label n = label (2^k*n) :=
      (v155_even_scale_label label hDouble k n hn).symm
    _ = label (2^k*m) :=
      hResidue _ _ hp hq hres
    _ = label m :=
      v155_even_scale_label label hDouble k m hm

#print axioms v155_future_meet_refl
#print axioms v155_future_meet_symm
#print axioms v155_future_meet_trans
#print axioms v155_future_meets_one_iff_good
#print axioms v155_single_class_iff_collatz
#print axioms v155_zero_tail_kernel_empty_iff_single_class
#print axioms v155_failure_has_actual_second_class_obstruction
#print axioms v155_even_scale_label
#print axioms v155_fixed_dyadic_future_labels_collapse

end SourceProduct
end CollatzFinal
