import Collatz.AllModuliFutureLabelCollapse
import Collatz.IdealFiniteClockGraphElimination

namespace CollatzFinal
namespace SourceProduct

/-!
V171 — A ONE-ARROW SYNTHETIC COUNTERMODEL TO MODULAR
IRREDUCIBILITY PLUS THE 3-ADIC TARGET SIEVE.

Define S5(5)=5, and S5(n)=the genuine shortcut T(n) for ALL n!=5.
This changes exactly ONE positive source transition.

The system still has:
  - exact even halving S5(2n)=n for all n;
  - every odd output ≡2 mod3;
  - 3|S5^k(n) iff 3*2^k|n for all natural n,k;
  - NO nontrivial fixed finite-modulus periodic future-class label.

The last claim follows by a real two-clock/affine repair:
any positive-source MOD-M periodic f invariant under S5
also satisfies f (T(n))=f (n) at the exceptional source5,
because the unaffected source 5+2M is odd and
T(5+2M)=T(5)+3M. V159 then makes f constant.

Nevertheless S5 has TWO genuine, positive, disjoint future
classes: fixed 5 and actual terminal 1<->2. Every genuine
T ancestor of 5 becomes an actual S5 ancestor of the new
fixed cycle (independently of any convergence conjecture).

Consequently, "no finite modular future-class factor" plus
the full ternary sieve is NOT enough for a no-giant theorem.
The exact all-source affine lift of the unmodified +1 law,
including the exceptional source, remains indispensable.

This is a deliberately NON-COLLATZ map; it does not disprove
or prove the original conjecture.
-/

def v171Map (n : Nat) : Nat :=
  if n=5 then 5 else shortcut n

theorem v171_even_source (n : Nat) :
    v171Map (2*n) = n := by
  have hn : 2*n≠5 := by omega
  simp [v171Map,hn,shortcut_two_mul]

theorem v171_odd_output_mod_three
    (n : Nat) (hodd : n%2=1) :
    v171Map n%3=2 := by
  by_cases hFive : n=5
  · subst n
    decide
  · have hOdd : n%2≠0 := by omega
    have hActual : v171Map n=shortcut n := by
      simp [v171Map,hFive]
    have hDouble : 2*shortcut n=3*n+1 := by
      unfold shortcut
      simp only [hOdd,ite_false]
      omega
    rw [hActual]
    omega

theorem v171_only_even_predecessors_of_three
    (n : Nat) (h : v171Map n%3=0) :
    n=2*v171Map n := by
  by_cases he : n%2=0
  · have ht : v171Map n=n/2 := by
      have hEven := v171_even_source (n/2)
      have hn : n=2*(n/2) := by omega
      calc
        v171Map n = v171Map (2*(n/2)) :=
          congrArg v171Map hn
        _ = n/2 := hEven
    rw [ht]
    omega
  · have hOdd : n%2=1 := by omega
    have hno := v171_odd_output_mod_three n hOdd
    omega

theorem v171_pure_even_predecessor_ancestry (k : Nat) :
    ∀ n : Nat, iter v171Map k n%3=0 →
      n=2^k*iter v171Map k n := by
  induction k with
  | zero =>
      intro n _
      simp [iter]
  | succ k ih =>
      intro n hDiv
      have hTail : iter v171Map k (v171Map n)%3=0 := by
        simpa only [iter] using hDiv
      have hRec := ih (v171Map n) hTail
      have hDivStep : v171Map n%3=0 := by
        rw [hRec]
        simp [Nat.mul_mod,hTail]
      have heven := v171_only_even_predecessors_of_three n hDivStep
      calc
        n=2*v171Map n := heven
        _=2*(2^k*iter v171Map k (v171Map n)) :=
          congrArg (fun z : Nat => 2*z) hRec
        _=2^(k+1)*iter v171Map (k+1) n := by
          simp [Nat.pow_succ,iter,Nat.mul_assoc,
            Nat.mul_comm,Nat.mul_left_comm]

theorem v171_iter_even_power (k y : Nat) :
    iter v171Map k (2^k*y)=y := by
  induction k generalizing y with
  | zero => simp [iter]
  | succ k ih =>
      have hstart : 2^(k+1)*y=2*(2^k*y) := by
        simp [Nat.pow_succ,Nat.mul_assoc,
          Nat.mul_comm,Nat.mul_left_comm]
      rw [hstart]
      simp only [iter]
      rw [v171_even_source]
      exact ih y

/-- Full V158-style sieve remains intact after changing one odd
    source's successor, since the modified output is still 2 mod3. -/
theorem v171_exact_full_ternary_sieve (n k : Nat) :
    iter v171Map k n%3=0 ↔ n%(3*2^k)=0 := by
  constructor
  · intro h
    have hEven := v171_pure_even_predecessor_ancestry k n h
    have hd : 3 ∣ iter v171Map k n := Nat.dvd_of_mod_eq_zero h
    obtain ⟨q,hq⟩ := hd
    apply Nat.mod_eq_zero_of_dvd
    refine ⟨q,?_⟩
    calc
      n=2^k*iter v171Map k n := hEven
      _=2^k*(3*q) := by rw [hq]
      _=(3*2^k)*q := by ac_rfl
  · intro h
    have hd : 3*2^k ∣ n := Nat.dvd_of_mod_eq_zero h
    obtain ⟨q,hq⟩ := hd
    have hRep : n=2^k*(3*q) := by
      calc
        n=(3*2^k)*q := hq
        _=2^k*(3*q) := by ac_rfl
    rw [hRep,v171_iter_even_power]
    simp

theorem v171_five_fixed :
    v171Map 5=5 := by decide

theorem v171_one_two_cycle :
    v171Map 1=2 ∧ v171Map 2=1 := by decide

theorem v171_all_future_five_fixed (t : Nat) :
    iter v171Map t 5=5 := by
  induction t with
  | zero => rfl
  | succ t ih =>
      simpa [iter,v171_five_fixed] using ih

theorem v171_one_two_stays_terminal
    (t : Nat) :
    iter v171Map t 1=1 ∨ iter v171Map t 1=2 := by
  induction t with
  | zero => exact Or.inl rfl
  | succ t ih =>
      have hStep :
          iter v171Map (t+1) 1 =
            v171Map (iter v171Map t 1) := by
        calc
          iter v171Map (t+1) 1 =
              iter v171Map 1 (iter v171Map t 1) :=
            iter_add v171Map t 1 1
          _ = v171Map (iter v171Map t 1) := rfl
      rw [hStep]
      rcases ih with h1 | h2
      · rw [h1]
        exact Or.inr (by decide)
      · rw [h2]
        exact Or.inl (by decide)

theorem v171_two_disjoint_real_positive_future_classes :
    ¬∃ i j : Nat,
      iter v171Map i 5 = iter v171Map j 1 := by
  intro h
  obtain ⟨i,j,hEq⟩ := h
  have hFive := v171_all_future_five_fixed i
  have hOne := v171_one_two_stays_terminal j
  rw [hFive] at hEq
  rcases hOne with h1 | h2
  · omega
  · omega

/-- Positive-only periodic recurrence: no use of a source-zero
    periodicity assumption. -/
theorem v171_positive_period_multiples {α : Type}
    (f : Nat → α) (M : Nat)
    (hPeriod : ∀ n, 0<n → f (n+M)=f n) :
    ∀ t n : Nat, 0<n →
      f (n+t*M)=f n := by
  intro t
  induction t with
  | zero =>
      intro n _
      simp
  | succ t ih =>
      intro n hn
      have hp : 0<n+t*M := by omega
      calc
        f (n+(t+1)*M)=f ((n+t*M)+M) := by
          congr 1
          simp [Nat.succ_mul,Nat.add_assoc]
        _=f (n+t*M) := hPeriod _ hp
        _=f n := ih n hn

/-- An invariant label of the modified map that is periodic
    modulo any M MUST also be invariant under the one original
    arrow 5 -> 8, by moving to unaffected odd source5+2M.
    This is unconditional even if a genuine second future
    class exists in the modified system. -/
theorem v171_periodic_label_reconstructs_true_shortcut
    {α : Type} (f : Nat → α) (M : Nat) (hM : 0<M)
    (hStep : ∀ n, 0<n → f (v171Map n)=f n)
    (hPeriod : ∀ n, 0<n → f (n+M)=f n) :
    ∀ n, 0<n → f (shortcut n)=f n := by
  intro n hn
  by_cases hFive : n=5
  · subst n
    have hLift : (5+2*M)≠5 := by omega
    have hLiftPos : 0<5+2*M := by omega
    have hShift : shortcut (5+2*M)=shortcut 5+3*M := by
      have hStepShift := shortcut_shift 5 M
      simpa using hStepShift
    have hMap : v171Map (5+2*M)=shortcut (5+2*M) := by
      change (if 5+2*M=5 then 5 else shortcut (5+2*M)) =
        shortcut (5+2*M)
      simp only [if_neg hLift]
    have hP3 : f (shortcut 5+3*M)=f (shortcut 5) :=
      v171_positive_period_multiples f M hPeriod
        3 (shortcut 5) (by decide)
    have hP2 : f (5+2*M)=f 5 :=
      v171_positive_period_multiples f M hPeriod 2 5 (by decide)
    calc
      f (shortcut 5)=f (shortcut 5+3*M) := hP3.symm
      _=f (shortcut (5+2*M)) := by rw [hShift]
      _=f (v171Map (5+2*M)) := by rw [hMap]
      _=f (5+2*M) := hStep _ hLiftPos
      _=f 5 := hP2
  · have hs := hStep n hn
    simpa [v171Map,hFive] using hs

/-- The MODULAR IRREDUCIBILITY theorem V159 survives a single
    bad positive fixed point introduced by one modified arrow!
    So absence of a fixed-congruence class label does not
    imply absence of nonterminal future classes. -/
theorem v171_no_nontrivial_fixed_mod_future_label
    {α : Type} (f : Nat → α)
    (M : Nat) (hM : 0<M)
    (hStep : ∀ n, 0<n → f (v171Map n)=f n)
    (hPeriod : ∀ n, 0<n → f (n+M)=f n) :
    ∀ n m, 0<n → 0<m → f n=f m := by
  exact v159_positive_future_label_cannot_be_periodic
    f M hM
    (v171_periodic_label_reconstructs_true_shortcut
      f M hM hStep hPeriod)
    hPeriod

/-- Every source reaching 5 under the REAL Collatz map must
    also reach the new synthetic 5-fixed class, because the
    two maps are identical UNTIL their first encounter with 5.
    This does not assume that all real sources reach 5. -/
theorem v171_true_hits_five_modified_sticks
    (k : Nat) :
    ∀ n : Nat, iter shortcut k n=5 →
      iter v171Map k n=5 := by
  induction k with
  | zero =>
      intro n hn
      simpa [iter] using hn
  | succ k ih =>
      intro n hn
      by_cases hf : n=5
      · subst n
        exact v171_all_future_five_fixed (k+1)
      · have hSame : v171Map n=shortcut n := by
          simp [v171Map,hf]
        have hTail : iter shortcut k (shortcut n)=5 := by
          simpa only [iter] using hn
        have hHit := ih (shortcut n) hTail
        simpa only [iter,hSame] using hHit

#print axioms v171_even_source
#print axioms v171_odd_output_mod_three
#print axioms v171_exact_full_ternary_sieve
#print axioms v171_all_future_five_fixed
#print axioms v171_one_two_stays_terminal
#print axioms v171_two_disjoint_real_positive_future_classes
#print axioms v171_periodic_label_reconstructs_true_shortcut
#print axioms v171_no_nontrivial_fixed_mod_future_label
#print axioms v171_true_hits_five_modified_sticks

end SourceProduct
end CollatzFinal
