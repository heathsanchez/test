import Collatz.SourceLockedDyadicFutureLift

namespace CollatzFinal
namespace SourceProduct

/-!
V161 — EXACT FINITE-HORIZON SOURCE-POPULATION PARITY MIXING.

For the real shortcut T and any initial source residue r (mod 2^k),
every binary future parity word of length h is realized by a genuine
source n in [0,2^(k+h)) with n mod 2^k = r.

This is proved by a recursively chosen source bit. At depth K,
n -> n+2^K does not change any earlier parity bits but flips the
parity of the genuine K-th endpoint. This follows directly from
V160's exact affine lift and the odd coefficient 3^a.

This theorem establishes FINITE-source-PREFIX controllability and
does not establish any terminal stopping-time estimate. Each finite
word may need a DIFFERENT large positive source; a consistent
2-adic infinite word need not be any positive natural source.

Protected negative control: S(n)=n/2 for even n and
S(n)=(n+3)/2 for odd n also has all finite parity prefixes
realizable (odd affine source slope 1), but 1 <-> 2 is a cycle
and 3 is a separate fixed point. Finite parity mixing alone
cannot force global Collatz convergence.

GLOBAL COLLATZ UNKNOWN. NO QED.
-/

theorem v161_odd_affine_coefficient (n k : Nat) :
    (3^(oddCount n k)) % 2 = 1 :=
  three_pow_mod_two _

/-- Raising the (K+1)-st SOURCE bit flips the exact K-th ENDPOINT
    parity, without any distribution/probability assumption. -/
theorem v161_flips_next_actual_parity (n K : Nat) :
    (iter shortcut K (n + 2^K)) % 2 =
      1 - (iter shortcut K n) % 2 := by
  have hLift := v160_exact_cylinder_affine K n 1
  simp only [Nat.mul_one] at hLift
  rw [hLift]
  have hOdd := v161_odd_affine_coefficient n K
  omega

/-- Adding any multiple of 2^K to the original source preserves
    every one of the first K ACTUAL parity decisions.
    The result follows from the exact source affine law, with no
    independence assumption or source ghost. -/
theorem v161_preserves_earlier_actual_parities :
    ∀ K n q j : Nat, j<K →
      (iter shortcut j (n+2^K*q))%2 =
        (iter shortcut j n)%2 := by
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
              shortcut (n+2^(K+1)*q) =
              shortcut n+2^K*(if n%2=0 then q else 3*q) := by
            rw [hStart,shortcut_shift]
            by_cases hEven : n%2=0
            · simp [hEven,Nat.mul_assoc]
            · simp [hEven,Nat.mul_assoc,Nat.mul_comm,
                Nat.mul_left_comm]
          have hj : j<K := by omega
          have hPrev := ih (shortcut n)
            (if n%2=0 then q else 3*q) j hj
          simpa only [iter,hShift] using hPrev

/-- Given any actual source prefix r and any desired next endpoint
    parity, exactly one of the two next source bits can be chosen.
    The theorem states constructive EXISTENCE; uniqueness follows
    independently from flip plus the two-element domain. -/
theorem v161_choose_one_more_bit
    (K r desired : Nat) (hDesired : desired<2) :
    ∃ d : Nat, d<2 ∧
      (iter shortcut K (r+2^K*d))%2=desired := by
  have hCurrent :
      (iter shortcut K r)%2 < 2 :=
    Nat.mod_lt _ (by decide)
  by_cases he : (iter shortcut K r)%2=desired
  · exact ⟨0,by decide,by simpa using he⟩
  · have hFlip := v161_flips_next_actual_parity r K
    refine ⟨1,by decide,?_⟩
    simpa only [Nat.mul_one] using (show
      (iter shortcut K (r+2^K))%2=desired by omega)

/-- All finite suffix parity words can be imposed after an
    arbitrary fixed k-bit original source prefix. The chosen
    source is a REAL nonnegative integer <2^(k+h).
    For r=0 and all-zero bits this source may be zero; the
    positive-source form follows by inserting a later nonzero
    high source bit, without changing the protected prefix. -/
theorem v161_every_finite_future_parity_word
    (k r : Nat) (hr : r<2^k) :
    ∀ h : Nat, ∀ bits : Nat → Nat,
      (∀ j : Nat, j<h → bits j<2) →
      ∃ n : Nat,
        n<2^(k+h) ∧ n%2^k=r ∧
        (∀ j : Nat, j<h →
          (iter shortcut (k+j) n)%2=bits j) := by
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
        v161_choose_one_more_bit (k+h) n (bits h) hDesired
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
          v161_preserves_earlier_actual_parities
            (k+h) n d (k+j) hSep
        have hPrior := hnBits j hjOld
        exact (show
          (iter shortcut (k+j) n')%2 =
            (iter shortcut (k+j) n)%2 from hPres).trans hPrior
      · have heq : j=h := by omega
        subst j
        simpa only [n'] using hNewBit

/-- For any nonzero fixed source prefix, the finite-word
    witness above is genuinely positive, not merely 2-adic. -/
theorem v161_real_positive_finite_suffix
    (k r h : Nat) (hr : r<2^k) (hrPos : 0<r)
    (bits : Nat → Nat)
    (hBits : ∀ j, j<h → bits j<2) :
    ∃ n : Nat,
      0<n ∧ n<2^(k+h) ∧ n%2^k=r ∧
      (∀ j, j<h →
        (iter shortcut (k+j) n)%2=bits j) := by
  obtain ⟨n,hnBound,hnResidue,hnBits⟩ :=
    v161_every_finite_future_parity_word k r hr h bits hBits
  have hnPos : 0<n := by
    by_cases hz : n=0
    · have hZero : (0:Nat)%2^k=r := by
        simpa [hz] using hnResidue
      omega
    · omega
  exact ⟨n,hnPos,hnBound,hnResidue,hnBits⟩

/-- A SECOND map with exactly the same even branch and
    the same source-parity controllability mechanism.
    It is NOT the Collatz map. -/
def v161TwoBasin (n : Nat) : Nat :=
  if n%2=0 then n/2 else (n+3)/2

theorem v161_two_basin_one_cycle :
    v161TwoBasin 1=2 ∧ v161TwoBasin 2=1 := by decide

theorem v161_two_basin_three_fixed :
    v161TwoBasin 3=3 := by decide

theorem v161_two_basin_even_source (n : Nat) :
    v161TwoBasin (2*n)=n := by
  simp [v161TwoBasin]

theorem v161_two_basin_odd_affine (n : Nat) :
    v161TwoBasin (2*n+1)=n+2 := by
  simp [v161TwoBasin]
  omega

#print axioms v161_odd_affine_coefficient
#print axioms v161_flips_next_actual_parity
#print axioms v161_preserves_earlier_actual_parities
#print axioms v161_choose_one_more_bit
#print axioms v161_every_finite_future_parity_word
#print axioms v161_real_positive_finite_suffix
#print axioms v161_two_basin_one_cycle
#print axioms v161_two_basin_three_fixed
#print axioms v161_two_basin_even_source
#print axioms v161_two_basin_odd_affine

end SourceProduct
end CollatzFinal
