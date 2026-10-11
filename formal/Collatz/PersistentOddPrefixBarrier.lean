import Collatz.AllScaleHighOddBarrier

namespace CollatzFinal
namespace SourceProduct

/-!
V184 — PROTECTED-FUTURE, SOURCE-INDEPENDENT ALL-PREFIX ODD BARRIER.

Prior V181 bounds odd frequency only on a finite source-height
range n >= 2^(10*r). A genuinely LEAST positive bad source m has
a stronger protected FUTURE: its true shortcut orbit never falls
below the ORIGINAL positive m, at any clock.

That single warranted distinction removes the finite-height cutoff.
If all orbit values >=8, every odd step obeys
   16*T(x) = 8*(3*x+1) <= 25*x,
while every even step obeys 2*T(x)=x.

The exact integer product consequence at EVERY k is
   2^k * 8^oddCount(n,k) * T^k(n)
       <= n * 25^oddCount(n,k).

If additionally every future state >=n, cancel the positive n:
   2^k*8^a <=25^a  for all k, a=oddCount(n,k).

The 5r-prefix consequence then forces oddCount(n,5*r)>=3*r+1
for all positive r, WITHOUT an original source-height restriction.
This is necessary for a LEAST BAD SOURCE, not a new Collatz proof.
An actual G5 nonterminal 187-cycle supplies a negative comparator
to claims that perpetual high-odd bias itself implies terminality.

All source/clock semantics are genuine Nat shortcuts; no LLM,
assumed convergence, one-sided parity oracle or quotient ghost.
Global Collatz UNKNOWN — NO QED.
-/

/-- An exact real even step, including x=0. -/
theorem v184_true_even_shortcut_identity
    (x : Nat) (he : x%2=0) :
    2*shortcut x=x := by
  simpa [he] using double_shortcut x

/-- Exactly where +1, source HEIGHT and odd parity interact:
if x>=8, one true +1 odd transition has bounded expansion. -/
theorem v184_true_odd_step_barrier
    (x : Nat) (hx : 8<=x) (ho : x%2≠0) :
    16*shortcut x <= 25*x := by
  have hStep : 2*shortcut x=3*x+1 := by
    simpa [ho] using double_shortcut x
  omega

/-- THE essential all-prefix prospective inequality; its premise
is an actual protected FUTURE lower bound at EVERY clock. -/
theorem v184_orbit_protected_product
    (n k : Nat)
    (hFuture : ∀ t : Nat, 8 <= iter shortcut t n) :
    2^k * 8^(oddCount n k) * iter shortcut k n <=
      n*25^(oddCount n k) := by
  induction k with
  | zero =>
      simp [oddCount,iter]
  | succ k ih =>
      let x := iter shortcut k n
      have hx : 8<=x := hFuture k
      have hNext :
          iter shortcut (k+1) n=shortcut x := by
        dsimp [x]
        rw [iter_succ_last]
      by_cases he : x%2=0
      · have ha : oddCount n (k+1)=oddCount n k := by
          simp [oddCount,he,x]
        have hE : 2*shortcut x=x :=
          v184_true_even_shortcut_identity x he
        calc
          2^(k+1)*8^(oddCount n (k+1))*
                iter shortcut (k+1) n =
              (2^k*8^(oddCount n k))*(2*shortcut x) := by
                  rw [hNext,ha]
                  simp [Nat.pow_succ,Nat.mul_assoc,
                    Nat.mul_comm,Nat.mul_left_comm]
          _ = 2^k*8^(oddCount n k)*x := by rw [hE]
          _ <= n*25^(oddCount n k) := ih
          _ = n*25^(oddCount n (k+1)) := by rw [ha]
      · have ha : oddCount n (k+1)=oddCount n k+1 := by
          simp [oddCount,he,x]
        have hO : 16*shortcut x <=25*x :=
          v184_true_odd_step_barrier x hx he
        have hLift :
            (2^k*8^(oddCount n k))*(16*shortcut x) <=
              (2^k*8^(oddCount n k))*(25*x) :=
          Nat.mul_le_mul_left _ hO
        have hIH :
            (2^k*8^(oddCount n k))*(25*x) <=
              n*25^(oddCount n (k+1)) := by
          calc
            (2^k*8^(oddCount n k))*(25*x) =
                (2^k*8^(oddCount n k)*x)*25 := by ac_rfl
            _ <= (n*25^(oddCount n k))*25 :=
                Nat.mul_le_mul_right 25 ih
            _ = n*25^(oddCount n (k+1)) := by
                rw [ha]
                simp [Nat.pow_succ,Nat.mul_assoc]
        calc
          2^(k+1)*8^(oddCount n (k+1))*
              iter shortcut (k+1) n =
            (2^k*8^(oddCount n k))*(16*shortcut x) := by
              rw [hNext,ha]
              calc
                2^(k+1)*8^(oddCount n k+1)*shortcut x =
                    (2^k*8^(oddCount n k))*((2*8)*shortcut x) := by
                  simp only [Nat.pow_succ]
                  ac_rfl
                _ = (2^k*8^(oddCount n k))*(16*shortcut x) := by
                    rfl
          _ <= (2^k*8^(oddCount n k))*(25*x) := hLift
          _ <= n*25^(oddCount n (k+1)) := hIH

/-- A genuine least bad source has an all-clock lower bound from
V99/V155. No finite source-height assumption is slipped in. -/
theorem v184_minimal_bad_all_future_bounded_below
    (n : Nat) (hBad : MinimalBad PositiveBad n)
    (hEight : 8<=n) :
    ∀ t : Nat, 8<=iter shortcut t n := by
  intro t
  exact Nat.le_trans hEight
    (minimal_positive_bad_never_below_source hBad t)

/-- The ALL-CLOCK odd exponent inequality is a genuine arithmetic
necessity of a nondecreasing-from-original-source orbit. -/
theorem v184_nondecreasing_orbit_forces_odd_power
    (n k : Nat) (hn : 0<n) (hEight : 8<=n)
    (hNeverBelow : ∀ t : Nat, n<=iter shortcut t n) :
    2^k*8^(oddCount n k) <=25^(oddCount n k) := by
  have hProduct :=
    v184_orbit_protected_product n k
      (fun t => Nat.le_trans hEight (hNeverBelow t))
  have hBelow : n<=iter shortcut k n := hNeverBelow k
  have hMult :
      (2^k*8^(oddCount n k))*n <=
        (2^k*8^(oddCount n k))*iter shortcut k n :=
    Nat.mul_le_mul_left _ hBelow
  have hTotal :
      (2^k*8^(oddCount n k))*n <=
        (25^(oddCount n k))*n := by
    calc
      (2^k*8^(oddCount n k))*n <=
          (2^k*8^(oddCount n k))*iter shortcut k n := hMult
      _ <= n*25^(oddCount n k) := by
        simpa only [Nat.mul_assoc] using hProduct
      _ = (25^(oddCount n k))*n := by ac_rfl
  apply Classical.byContradiction
  intro hNot
  have hLess :
      25^(oddCount n k) <2^k*8^(oddCount n k) := by omega
  have hOne :
      25^(oddCount n k)+1 <=2^k*8^(oddCount n k) := by omega
  have hWeighted :=
    Nat.mul_le_mul_right n hOne
  have hWeighted' :
      25^(oddCount n k)*n+n <=
        (2^k*8^(oddCount n k))*n := by
    simpa [Nat.add_mul] using hWeighted
  have hStrict :
      25^(oddCount n k)*n <
        (2^k*8^(oddCount n k))*n := by omega
  omega

/-- The fully general source-locked least-bad necessary inequality:
the original source is FIXED, all true future k are quantified. -/
theorem v184_least_bad_all_clock_odd_power
    (n k : Nat) (hBad : MinimalBad PositiveBad n)
    (hEight : 8<=n) :
    2^k*8^(oddCount n k) <=25^(oddCount n k) := by
  exact v184_nondecreasing_orbit_forces_odd_power
    n k (by omega) hEight
    (minimal_positive_bad_never_below_source hBad)

/-- Simple independent power comparison used to show that a 3/5
high-odd bound holds at EVERY future 5r clocks, not just clock12. -/
theorem v184_pow_mono_8_25 (d : Nat) :
    8^d <=25^d := by
  induction d with
  | zero => decide
  | succ d ih =>
      calc
        8^(d+1)=8^d*8 := by simp [Nat.pow_succ]
        _ <=25^d*8 := Nat.mul_le_mul_right 8 ih
        _ <=25^d*25 :=
            Nat.mul_le_mul_left _ (by decide)
        _ =25^(d+1) := by simp [Nat.pow_succ]

theorem v184_pow_mono_15625_16384 (d : Nat) :
    15625^d <=16384^d := by
  induction d with
  | zero => decide
  | succ d ih =>
      calc
        15625^(d+1)=15625^d*15625 := by simp [Nat.pow_succ]
        _ <=16384^d*15625 := Nat.mul_le_mul_right _ ih
        _ <=16384^d*16384 :=
            Nat.mul_le_mul_left _ (by decide)
        _ =16384^(d+1) := by simp [Nat.pow_succ]

theorem v184_pow_strict_15625_16384
    (d : Nat) (hd : 0<d) :
    15625^d <16384^d := by
  cases d with
  | zero => omega
  | succ d =>
      have hMon :=
        v184_pow_mono_15625_16384 d
      have hPos : 0<16384^d :=
        Nat.pow_pos (by decide)
      have hStrict : 16384^d*15625 <16384^d*16384 := by
        omega
      calc
        15625^(d+1)=15625^d*15625 := by simp [Nat.pow_succ]
        _ <=16384^d*15625 :=
          Nat.mul_le_mul_right _ hMon
        _ <16384^d*16384 := hStrict
        _ =16384^(d+1) := by simp [Nat.pow_succ]

/-- A strict 5-clock source-period test with NO moving
source-height cutoff. For any positive r and any real trajectory
that never falls below its starting source n>=8, more than 3r
of the first 5r shortcut steps MUST be odd. -/
theorem v184_nondecreasing_all_five_block_prefixes
    (n r : Nat) (hn : 0<n) (hEight : 8<=n)
    (hr : 0<r)
    (hNeverBelow : ∀ t : Nat, n<=iter shortcut t n) :
    3*r+1 <= oddCount n (5*r) := by
  let a := oddCount n (5*r)
  have hPower :=
    v184_nondecreasing_orbit_forces_odd_power
      n (5*r) hn hEight hNeverBelow
  apply Classical.byContradiction
  intro hBad
  have ha : a<=3*r := by dsimp [a];omega
  let d : Nat :=3*r-a
  have hd : a+d=3*r := by dsimp [d];omega
  have hP : 8^d<=25^d :=v184_pow_mono_8_25 d
  have hIneq :
      2^(5*r)*8^(3*r) <=25^(3*r) := by
    calc
      2^(5*r)*8^(3*r) =
          (2^(5*r)*8^a)*8^d := by
            have heq :8^(3*r)=8^a*8^d := by
              rw [← Nat.pow_add,hd]
            rw [heq]
            ac_rfl
      _ <= 25^a*8^d := Nat.mul_le_mul_right _ hPower
      _ <= 25^a*25^d := Nat.mul_le_mul_left _ hP
      _ = 25^(3*r) := by
           rw [← Nat.pow_add,hd]
  have hLeft :
      2^(5*r)*8^(3*r)=16384^r := by
    calc
      2^(5*r)*8^(3*r) = (2^5)^r*(8^3)^r := by
        simp [Nat.pow_mul]
      _ = (2^5*8^3)^r := by
        rw [Nat.mul_pow]
      _ = 16384^r := by
        have hBase : (2^5*8^3 : Nat)=16384 := by decide
        rw [hBase]
  have hRight :25^(3*r)=15625^r := by
    calc
      25^(3*r)=(25^3)^r := by simp [Nat.pow_mul]
      _=15625^r := by
        have hBase : (25^3:Nat)=15625 := by decide
        rw [hBase]
  rw [hLeft,hRight] at hIneq
  have hStrict :=v184_pow_strict_15625_16384 r hr
  omega

/-- END-TO-END: for a hypothetical LEAST positive bad source, this
all-scale parity constraint holds at all future horizons 5r,
WITHOUT V181's restrictive n>=2^(10r) guard. -/
theorem v184_least_bad_perpetual_three_fifths_odd
    (n r : Nat) (hBad : MinimalBad PositiveBad n)
    (hEight : 8<=n) (hr : 0<r) :
    3*r+1 <= oddCount n (5*r) := by
  exact v184_nondecreasing_all_five_block_prefixes
    n r (by omega) hEight hr
    (minimal_positive_bad_never_below_source hBad)

#print axioms v184_true_even_shortcut_identity
#print axioms v184_true_odd_step_barrier
#print axioms v184_orbit_protected_product
#print axioms v184_minimal_bad_all_future_bounded_below
#print axioms v184_nondecreasing_orbit_forces_odd_power
#print axioms v184_least_bad_all_clock_odd_power
#print axioms v184_nondecreasing_all_five_block_prefixes
#print axioms v184_least_bad_perpetual_three_fifths_odd

end SourceProduct
end CollatzFinal
