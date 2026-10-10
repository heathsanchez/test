import Collatz.FiniteParityPopulationMixing

namespace CollatzFinal
namespace SourceProduct

/-!
V162 — EXACT 3n+7 COUNTERMODEL TO FINITE-MIXING QED.

The synthetic GENERALIZED shortcut G has:
  G(2x)=x,
  G(2x+1)=3x+5 = (3*(2x+1)+7)/2.

It has the same EVEN branch, the same odd 3x slope, the same
odd-output residue 2 modulo 3, the same pure-even preimages of
3-divisible targets, and the same complete finite future parity-
word controllability as the actual Collatz shortcut T with 3n+1.

But G has TWO disjoint genuine positive periodic cycles:
  7 -> 14 -> 7
  5 -> 11 -> 20 -> 10 -> 5

Therefore those structural premises alone cannot imply
uniqueness of the terminal future class or Collatz.
This is NOT a Collatz counterexample, since its odd intercept
is 7 rather than 1. No QED is asserted.
-/

def v162Map (n : Nat) : Nat :=
  if n%2=0 then n/2 else (3*n+7)/2

theorem v162_even (n : Nat) :
    v162Map (2*n)=n := by
  simp [v162Map]

theorem v162_odd (n : Nat) :
    v162Map (2*n+1)=3*n+5 := by
  simp [v162Map]
  omega

theorem v162_iter_succ_last (n k : Nat) :
    iter v162Map (k+1) n = v162Map (iter v162Map k n) := by
  simpa [iter] using (iter_add v162Map k 1 n)

theorem v162_shift (x z : Nat) :
    v162Map (x+2*z) =
      v162Map x+(if x%2=0 then z else 3*z) := by
  by_cases he : x%2=0
  · have hp : (x+2*z)%2=0 := by omega
    simp [v162Map,he,hp]
    omega
  · have hp : ¬ (x+2*z)%2=0 := by omega
    simp [v162Map,he,hp]
    omega

def v162OddCount (n : Nat) : Nat → Nat
  | 0 => 0
  | k+1 =>
      if iter v162Map k n %2=0 then v162OddCount n k
      else v162OddCount n k+1

theorem v162_exact_cylinder_affine :
    ∀ k n q : Nat,
      iter v162Map k (n + 2^k*q) =
        iter v162Map k n + 3^(v162OddCount n k)*q := by
  intro k
  induction k with
  | zero =>
      intro n q
      simp [iter,v162OddCount]
  | succ k ih =>
      intro n q
      have hPow :
          2^(k+1)*q = 2^k*(2*q) := by
        simp [Nat.pow_succ,Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]
      have hPre :
          iter v162Map k (n+2^(k+1)*q) =
            iter v162Map k n+2*(3^v162OddCount n k*q) := by
        rw [hPow,ih n (2*q)]
        congr 1
        ac_rfl
      calc
        iter v162Map (k+1) (n+2^(k+1)*q) =
            v162Map (iter v162Map k (n+2^(k+1)*q)) :=
          v162_iter_succ_last _ _
        _ = v162Map (iter v162Map k n+2*(3^v162OddCount n k*q)) := by
          rw [hPre]
        _ = v162Map (iter v162Map k n) +
            (if iter v162Map k n%2=0
              then 3^v162OddCount n k*q else 3*(3^v162OddCount n k*q)) :=
          v162_shift _ _
        _ = iter v162Map (k+1) n +
            3^v162OddCount n (k+1)*q := by
          rw [v162_iter_succ_last]
          by_cases hEven : iter v162Map k n%2=0
          · simp [v162OddCount,hEven]
          · simp [v162OddCount,hEven,Nat.pow_succ,
              Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]


/-- Every odd source has a target congruent to 2 mod3,
    exactly as for the actual 3n+1 shortcut. -/
theorem v162_odd_target_mod3 (n : Nat) (hn : n%2=1) :
    v162Map n%3=2 := by
  have hForm : n=2*(n/2)+1 := by omega
  rw [hForm,v162_odd]
  omega

theorem v162_three_target_only_even_predecessor
    (n : Nat) (hDiv : v162Map n%3=0) :
    n=2*v162Map n := by
  by_cases he : n%2=0
  · have hEven : v162Map n=n/2 := by simp [v162Map,he]
    rw [hEven]
    omega
  · have hOdd : n%2=1 := by omega
    have hResidue := v162_odd_target_mod3 n hOdd
    omega

theorem v162_pure_even_ancestry (k : Nat) :
    ∀ n : Nat, iter v162Map k n%3=0 →
      n=2^k*iter v162Map k n := by
  induction k with
  | zero =>
      intro n _
      simp [iter]
  | succ k ih =>
      intro n hDiv
      have hDivTail :
          iter v162Map k (v162Map n)%3=0 := by
        simpa only [iter] using hDiv
      have hRec := ih (v162Map n) hDivTail
      have hDivStep : v162Map n%3=0 := by
        rw [hRec]
        simp [Nat.mul_mod,hDivTail]
      have hEven :=
        v162_three_target_only_even_predecessor n hDivStep
      calc
        n=2*v162Map n := hEven
        _=2*(2^k*iter v162Map k (v162Map n)) :=
          congrArg (fun z : Nat => 2*z) hRec
        _=2^(k+1)*iter v162Map (k+1) n := by
          simp [Nat.pow_succ,iter,Nat.mul_assoc,
            Nat.mul_comm,Nat.mul_left_comm]

theorem v162_iter_even_power (s y : Nat) :
    iter v162Map s (2^s*y)=y := by
  induction s generalizing y with
  | zero => simp [iter]
  | succ s ih =>
      have hStart :
          2^(s+1)*y = 2*(2^s*y) := by
        simp [Nat.pow_succ,Nat.mul_assoc,Nat.mul_comm,
          Nat.mul_left_comm]
      rw [hStart]
      simp only [iter]
      rw [v162_even]
      exact ih y

theorem v162_same_ternary_sieve (n k : Nat) :
    iter v162Map k n%3=0 ↔ n%(3*2^k)=0 := by
  constructor
  · intro hDiv
    have hh := v162_pure_even_ancestry k n hDiv
    have hd : 3 ∣ iter v162Map k n :=
      Nat.dvd_of_mod_eq_zero hDiv
    obtain ⟨q,hq⟩ := hd
    apply Nat.mod_eq_zero_of_dvd
    refine ⟨q,?_⟩
    calc
      n=2^k*iter v162Map k n := hh
      _=2^k*(3*q) := by rw [hq]
      _=(3*2^k)*q := by ac_rfl
  · intro hDiv
    have hd : 3*2^k ∣ n :=
      Nat.dvd_of_mod_eq_zero hDiv
    obtain ⟨q,hq⟩ := hd
    have hRep : n=2^k*(3*q) := by
      calc
        n=(3*2^k)*q := hq
        _=2^k*(3*q) := by ac_rfl
    rw [hRep]
    rw [v162_iter_even_power]
    simp

theorem v162_odd_affine_coefficient (n k : Nat) :
    (3^(v162OddCount n k)) % 2 = 1 :=
  three_pow_mod_two _

/-- Raising the (K+1)-st SOURCE bit flips the exact K-th ENDPOINT
    parity, without any distribution/probability assumption. -/
theorem v162_flips_next_actual_parity (n K : Nat) :
    (iter v162Map K (n + 2^K)) % 2 =
      1 - (iter v162Map K n) % 2 := by
  have hLift := v162_exact_cylinder_affine K n 1
  simp only [Nat.mul_one] at hLift
  rw [hLift]
  have hOdd := v162_odd_affine_coefficient n K
  omega

/-- Adding any multiple of 2^K to the original source preserves
    every one of the first K ACTUAL parity decisions.
    The result follows from the exact source affine law, with no
    independence assumption or source ghost. -/
theorem v162_preserves_earlier_actual_parities :
    ∀ K n q j : Nat, j<K →
      (iter v162Map j (n+2^K*q))%2 =
        (iter v162Map j n)%2 := by
  intro K
  induction K with
  | zero =>
      intro n q j hj
      omega
  | succ K ih =>
      intro n q j hj
      have hStart :
          n+2^(K+1)*q = n+2*(2^K*q) := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
          Nat.mul_left_comm]
      cases j with
      | zero =>
          have hh : (n+2^(K+1)*q)%2=n%2 := by
            rw [hStart]
            omega
          simpa only [iter] using hh
      | succ j =>
          have hShift :
              v162Map (n+2^(K+1)*q) =
              v162Map n+2^K*(if n%2=0 then q else 3*q) := by
            rw [hStart,v162_shift]
            by_cases hEven : n%2=0
            · simp [hEven,Nat.mul_assoc]
            · simp [hEven,Nat.mul_assoc,Nat.mul_comm,
                Nat.mul_left_comm]
          have hj : j<K := by omega
          have hPrev := ih (v162Map n)
            (if n%2=0 then q else 3*q) j hj
          simpa only [iter,hShift] using hPrev

/-- Given any actual source prefix r and any desired next endpoint
    parity, exactly one of the two next source bits can be chosen.
    The theorem states constructive EXISTENCE; uniqueness follows
    independently from flip plus the two-element domain. -/
theorem v162_choose_one_more_bit
    (K r desired : Nat) (hDesired : desired<2) :
    ∃ d : Nat, d<2 ∧
      (iter v162Map K (r+2^K*d))%2=desired := by
  have hCurrent :
      (iter v162Map K r)%2 < 2 :=
    Nat.mod_lt _ (by decide)
  by_cases he : (iter v162Map K r)%2=desired
  · exact ⟨0,by decide,by simpa using he⟩
  · have hFlip := v162_flips_next_actual_parity r K
    refine ⟨1,by decide,?_⟩
    simpa only [Nat.mul_one] using (show
      (iter v162Map K (r+2^K))%2=desired by omega)

/-- All finite suffix parity words can be imposed after an
    arbitrary fixed k-bit original source prefix. The chosen
    source is a REAL nonnegative integer <2^(k+h).
    For r=0 and all-zero bits this source may be zero; the
    positive-source form follows by inserting a later nonzero
    high source bit, without changing the protected prefix. -/
theorem v162_every_finite_future_parity_word
    (k r : Nat) (hr : r<2^k) :
    ∀ h : Nat, ∀ bits : Nat → Nat,
      (∀ j : Nat, j<h → bits j<2) →
      ∃ n : Nat,
        n<2^(k+h) ∧ n%2^k=r ∧
        (∀ j : Nat, j<h →
          (iter v162Map (k+j) n)%2=bits j) := by
  intro h
  induction h with
  | zero =>
      intro bits _
      refine ⟨r,?_,Nat.mod_eq_of_lt hr,?_⟩
      · simpa using hr
      · intro j hj
        omega
  | succ h ih =>
      intro bits hBits
      have hShort (j : Nat) (hj : j<h) : bits j<2 :=
        hBits j (by omega)
      obtain ⟨n,hnBound,hnMod,hnBits⟩ := ih bits hShort
      have hDesired : bits h<2 := hBits h (by omega)
      obtain ⟨d,hd,hNewBit⟩ :=
        v162_choose_one_more_bit (k+h) n (bits h) hDesired
      have hD : d=0 ∨ d=1 := by omega
      let n' := n+2^(k+h)*d
      have hnBound' : n'<2^(k+(h+1)) := by
        have hExp : k+(h+1)=(k+h)+1 := by omega
        rw [hExp,Nat.pow_succ]
        dsimp [n']
        rcases hD with h0 | h1
        · simp [h0]
          omega
        · simp [h1]
          omega
      have hnMod' : n'%2^k=r := by
        have hPow : 2^(k+h)=2^k*2^h := Nat.pow_add 2 k h
        dsimp [n']
        rw [hPow]
        simpa [Nat.add_mod, Nat.mul_mod] using hnMod
      refine ⟨n',hnBound',hnMod',?_⟩
      intro j hj
      by_cases hjOld : j<h
      · have hSep : k+j < k+h := by omega
        have hPres :=
          v162_preserves_earlier_actual_parities
            (k+h) n d (k+j) hSep
        have hPrior := hnBits j hjOld
        exact (show
          (iter v162Map (k+j) n')%2 =
            (iter v162Map (k+j) n)%2 from hPres).trans hPrior
      · have heq : j=h := by omega
        subst j
        simpa only [n'] using hNewBit


/-- The two actual periodic futures are strictly distinct. -/
def v162CycleA (x : Nat) : Prop := x=7 ∨ x=14
def v162CycleB (x : Nat) : Prop :=
  x=5 ∨ x=11 ∨ x=20 ∨ x=10

theorem v162_cycleA_closed {x : Nat} (hx : v162CycleA x) :
    v162CycleA (v162Map x) := by
  rcases hx with h | h
  · subst x
    exact Or.inr (by decide)
  · subst x
    exact Or.inl (by decide)

theorem v162_cycleB_closed {x : Nat} (hx : v162CycleB x) :
    v162CycleB (v162Map x) := by
  rcases hx with h | h | h | h
  · subst x
    exact Or.inr (Or.inl (by decide))
  · subst x
    exact Or.inr (Or.inr (Or.inl (by decide)))
  · subst x
    exact Or.inr (Or.inr (Or.inr (by decide)))
  · subst x
    exact Or.inl (by decide)

theorem v162_cycle_sets_disjoint {x : Nat}
    (ha : v162CycleA x) (hb : v162CycleB x) : False := by
  unfold v162CycleA at ha
  unfold v162CycleB at hb
  omega

theorem v162_all_cyclesA (t : Nat) :
    v162CycleA (iter v162Map t 7) := by
  induction t with
  | zero =>
      exact Or.inl rfl
  | succ t ih =>
      rw [v162_iter_succ_last]
      exact v162_cycleA_closed ih

theorem v162_all_cyclesB (t : Nat) :
    v162CycleB (iter v162Map t 5) := by
  induction t with
  | zero => exact Or.inl rfl
  | succ t ih =>
      rw [v162_iter_succ_last]
      exact v162_cycleB_closed ih

theorem v162_disjoint_actual_positive_future_classes :
    ¬ (∃ i j : Nat,
      iter v162Map i 7=iter v162Map j 5) := by
  intro hh
  obtain ⟨i,j,hMeet⟩ := hh
  have ha := v162_all_cyclesA i
  have hb := v162_all_cyclesB j
  rw [hMeet] at ha
  exact v162_cycle_sets_disjoint ha hb

theorem v162_explicit_two_cycles :
    iter v162Map 2 7=7 ∧ iter v162Map 4 5=5 := by
  decide


#print axioms v162_exact_cylinder_affine
#print axioms v162_odd_target_mod3
#print axioms v162_pure_even_ancestry
#print axioms v162_same_ternary_sieve
#print axioms v162_flips_next_actual_parity
#print axioms v162_preserves_earlier_actual_parities
#print axioms v162_every_finite_future_parity_word
#print axioms v162_disjoint_actual_positive_future_classes
#print axioms v162_explicit_two_cycles

end SourceProduct
end CollatzFinal
