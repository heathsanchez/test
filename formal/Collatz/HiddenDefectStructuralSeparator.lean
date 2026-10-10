import Collatz.FiniteAuditHiddenDefect
import Collatz.AllModuliFutureLabelCollapse

namespace CollatzFinal
namespace SourceProduct

/-!
V176 — HIDDEN FINITE-AUDIT DEFECT RETAINS TWO UNIVERSAL INVARIANTS.

For ANY finite source cutoff X and finite clock H, the exact V174
hidden absorber a = 6*2^H*(X+1)+5 creates a second positive fixed
future class while matching EVERY audited true Collatz source/clock.

This stronger negative control additionally verifies, for ALL
positive natural sources and all finite depths:
(1) genuine even halving and exact ternary reverse sieve; and
(2) total collapse of ANY positive-source periodic invariant label.

Only the globally exact all-source +1 odd affine relation is missing.
Thus a proof using finite audits, even halving, ternary sieve and
absence of periodic factors alone cannot force unique terminal class.

This is a mathematical separator, NOT a nonconvergent true Collatz
source and NOT a Collatz QED.
-/

def v176Adversary (X H n : Nat) : Nat :=
  v173FreezeAt (v174HiddenDefect X H) n

theorem v176_even_halving (X H n : Nat) :
    v176Adversary X H (2*n) = n := by
  have ha : v174HiddenDefect X H %2=1 :=
    (v174_defect_large_and_odd X H).2.1
  have hn : 2*n ≠ v174HiddenDefect X H := by omega
  dsimp [v176Adversary]
  rw [v173_freeze_agrees_before_seed _ _ hn]
  exact shortcut_two_mul n

theorem v176_odd_output_mod_three
    (X H n : Nat) (hn : n%2=1) :
    v176Adversary X H n %3 = 2 := by
  let a := v174HiddenDefect X H
  by_cases heq : n=a
  · subst n
    change (v173FreezeAt a a)%3=2
    simp only [v173FreezeAt, ite_true]
    exact (v174_defect_large_and_odd X H).2.2
  · have hOdd : n%2≠0 := by omega
    have hTrue : v176Adversary X H n=shortcut n :=
      v173_freeze_agrees_before_seed a n heq
    rw [hTrue]
    simp only [shortcut,hOdd,ite_false]
    omega

/-- All exact preimages of a 3-divisible endpoint are even. -/
theorem v176_preimage_div_three_even
    (X H n : Nat) (hd : v176Adversary X H n%3=0) :
    n=2*v176Adversary X H n := by
  by_cases he : n%2=0
  · have hn : n=2*(n/2) := by omega
    have hval : v176Adversary X H n=n/2 := by
      calc
        v176Adversary X H n =
            v176Adversary X H (2*(n/2)) := by rw [hn]
        _=n/2 := v176_even_halving X H (n/2)
    rw [hval]
    omega
  · have hodd : n%2=1 := by omega
    have hx := v176_odd_output_mod_three X H n hodd
    omega

/-- Every positive source 3-divisible at depth k was purely even
for precisely k clocks: exact original-source lineage. -/
theorem v176_pure_even_predecessor_ancestry (X H k : Nat) :
    ∀ n : Nat, iter (v176Adversary X H) k n%3=0 →
      n=2^k*iter (v176Adversary X H) k n := by
  induction k with
  | zero =>
      intro n _
      simp [iter]
  | succ k ih =>
      intro n hDiv
      have hTail :
          iter (v176Adversary X H) k (v176Adversary X H n)%3=0 := by
        simpa only [iter] using hDiv
      have hRec := ih (v176Adversary X H n) hTail
      have hDivStep : v176Adversary X H n%3=0 := by
        rw [hRec]
        simp [Nat.mul_mod,hTail]
      have hEven := v176_preimage_div_three_even X H n hDivStep
      calc
        n=2*v176Adversary X H n := hEven
        _=2*(2^k*iter (v176Adversary X H) k (v176Adversary X H n)) :=
          congrArg (fun z : Nat => 2*z) hRec
        _=2^(k+1)*iter (v176Adversary X H) (k+1) n := by
          simp [Nat.pow_succ,iter,Nat.mul_assoc,
            Nat.mul_comm,Nat.mul_left_comm]

theorem v176_iter_even_powers (X H k y : Nat) :
    iter (v176Adversary X H) k (2^k*y)=y := by
  induction k generalizing y with
  | zero => simp [iter]
  | succ k ih =>
      have hstart : 2^(k+1)*y=2*(2^k*y) := by
        simp [Nat.pow_succ,Nat.mul_assoc,
          Nat.mul_comm,Nat.mul_left_comm]
      rw [hstart]
      simp only [iter]
      rw [v176_even_halving]
      exact ih y

/-- The full all-source/all-depth V158 sieve survives this
arbitrarily high one-arrow modification. -/
theorem v176_all_depths_ternary_sieve (X H n k : Nat) :
    iter (v176Adversary X H) k n%3=0 ↔ n%(3*2^k)=0 := by
  constructor
  · intro h
    have hEven := v176_pure_even_predecessor_ancestry X H k n h
    have hd : 3 ∣ iter (v176Adversary X H) k n :=
      Nat.dvd_of_mod_eq_zero h
    obtain ⟨q,hq⟩ := hd
    apply Nat.mod_eq_zero_of_dvd
    refine ⟨q,?_⟩
    calc
      n=2^k*iter (v176Adversary X H) k n := hEven
      _=2^k*(3*q) := by rw [hq]
      _=(3*2^k)*q := by ac_rfl
  · intro h
    have hd : 3*2^k ∣ n := Nat.dvd_of_mod_eq_zero h
    obtain ⟨q,hq⟩ := hd
    have hRep : n=2^k*(3*q) := by
      calc
        n=(3*2^k)*q := hq
        _=2^k*(3*q) := by ac_rfl
    rw [hRep,v176_iter_even_powers]
    simp

/-- Positive-only modular periodicity can be iterated without a
source-zero assumption. -/
theorem v176_positive_period_multiples
    {α : Type} (f : Nat → α) (M : Nat)
    (hPeriod : ∀ n, 0<n → f (n+M)=f n) :
    ∀ t n : Nat, 0<n → f(n+t*M)=f n := by
  intro t
  induction t with
  | zero =>
      intro n _
      simp
  | succ t ih =>
      intro n hn
      have hp : 0<n+t*M := by omega
      calc
        f(n+(t+1)*M)=f((n+t*M)+M) := by
          congr 1
          simp [Nat.succ_mul,Nat.add_assoc]
        _=f(n+t*M) := hPeriod _ hp
        _=f n := ih n hn

/-- Any mod-M periodic invariant label under the false map is also
invariant under the TRUE arrow of the single hidden defect.
A universally quantified affine arithmetic relation, rather than
finite auditing, repairs the missing arrow. -/
theorem v176_hidden_periodic_label_reconstructs_true
    {α : Type} (f : Nat → α)
    (X H M : Nat) (hM : 0<M)
    (hStep : ∀ n, 0<n → f (v176Adversary X H n)=f n)
    (hPeriod : ∀ n, 0<n → f(n+M)=f n) :
    ∀ n, 0<n → f(shortcut n)=f n := by
  intro n hn
  let a := v174HiddenDefect X H
  by_cases heq : n=a
  · subst n
    have haPos : 0<a := by
      have h := (v174_defect_large_and_odd X H).1
      omega
    have haOdd : a%2=1 :=
      (v174_defect_large_and_odd X H).2.1
    have hLift : a+2*M≠a := by omega
    have hLiftPos : 0<a+2*M := by omega
    have hOdd : a%2≠0 := by omega
    have hOddLift : (a+2*M)%2≠0 := by omega
    have hShift : shortcut (a+2*M)=shortcut a+3*M := by
      simp only [shortcut,hOddLift,hOdd,ite_false]
      omega
    have hTrue : v176Adversary X H (a+2*M)=shortcut (a+2*M) :=
      v173_freeze_agrees_before_seed a (a+2*M) hLift
    have hShortcutPos : 0<shortcut a := by
      simp only [shortcut,hOdd,ite_false]
      omega
    have hP3 : f(shortcut a+3*M)=f(shortcut a) :=
      v176_positive_period_multiples f M hPeriod
        3 (shortcut a) hShortcutPos
    have hP2 : f(a+2*M)=f a :=
      v176_positive_period_multiples f M hPeriod 2 a haPos
    calc
      f(shortcut a)=f(shortcut a+3*M) := hP3.symm
      _=f(shortcut (a+2*M)) := by rw [hShift]
      _=f(v176Adversary X H (a+2*M)) := by rw [hTrue]
      _=f(a+2*M) := hStep _ hLiftPos
      _=f a := hP2
  · have hs := hStep n hn
    have hEq : v176Adversary X H n=shortcut n :=
      v173_freeze_agrees_before_seed a n heq
    rw [hEq] at hs
    exact hs

/-- The V159 no-fixed-modulus-factor theorem remains TRUE for the
false map at EVERY finite X,H, even though it has a second
positive future class. -/
theorem v176_all_positive_periodic_future_labels_constant
    {α : Type} (f : Nat → α)
    (X H M : Nat) (hM : 0<M)
    (hStep : ∀ n, 0<n → f(v176Adversary X H n)=f n)
    (hPeriod : ∀ n, 0<n → f(n+M)=f n) :
    ∀ n m, 0<n → 0<m → f n=f m := by
  exact v159_positive_future_label_cannot_be_periodic f M hM
    (v176_hidden_periodic_label_reconstructs_true
      f X H M hM hStep hPeriod) hPeriod

/-- Yet the same system is indistinguishable on EVERY audited source
and clock, while its frozen hidden source is a separate
nonterminal fixed point. -/
theorem v176_full_finite_audit_still_cannot_detect_two_classes
    (X H : Nat) :
    (∀ n t, n<X → t≤H →
      iter (v176Adversary X H) t n=iter shortcut t n) ∧
    ¬ ∃ i j : Nat,
      iter (v176Adversary X H) i (v174HiddenDefect X H)=
      iter (v176Adversary X H) j 1 := by
  constructor
  · intro n t hn ht
    exact v174_every_bounded_audit_agrees X H n t hn ht
  · exact v174_false_map_has_two_disjoint_positive_classes X H

#print axioms v176_even_halving
#print axioms v176_odd_output_mod_three
#print axioms v176_all_depths_ternary_sieve
#print axioms v176_hidden_periodic_label_reconstructs_true
#print axioms v176_all_positive_periodic_future_labels_constant
#print axioms v176_full_finite_audit_still_cannot_detect_two_classes

end SourceProduct
end CollatzFinal
