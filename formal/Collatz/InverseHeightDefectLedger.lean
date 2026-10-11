import Collatz.TwoClockMersenneHeightSeparator

namespace CollatzFinal
namespace SourceProduct

/-!
V189 — MINIMUM CONSEQUENTIAL SOURCE-CLOCK DEFECT LEDGER.

The strongest warrant from V188 does not require storing every
past parity bit. The smallest exact residual distinguishing a tight
odd predecessor chain from one containing even transitions is

  D(n,k) := 3^k*(n+1) - 2^k*(T^k(n)+1) >=0.

At each TRUE original-source clock k, write x=T^k(n) and

  E(x) = if x even then 2*x+1 else 0.

Then D(n,0)=0 and the exact law is

  D(n,k+1) = 3*D(n,k) + 2^k*E(x).

A genuine odd step adds ZERO new defect; an even step creates a
strictly positive new distinction. This is a proof-carrying
prospective account of why the all-odd Mersenne source height bound
is sharp. No arbitrary merging of states with different actual
source/clock consequences is admitted.

For any REAL two-clock meeting T^i(n)=T^j(p) we obtain the exact
necessary source/clock budget inequality:

  3^i*2^j*(n+1)
      <= 3^j*2^i*(p+1) + 2^j*D(n,i).

This is a CONSTRAINT on lawful meetings, not a theorem that a
smaller-source companion actually exists. The same equation
replays V188's impossible early-clock Mersenne comparisons when
D(n,i)=0.

The outcome of Collatz globally stays UNKNOWN. NO QED.
-/

/-- The genuine even step alone adds missing inverse-height
information: an integer that is ZERO on odd steps. -/
def V189EvenSlack (x : Nat) : Nat :=
  if x%2=0 then 2*x+1 else 0

/-- Exactly one true +1 transition, retaining a constructive
nonnegative slack for both odd and even transitions. -/
theorem v189_one_step_exact_slack (x : Nat) :
    2*(shortcut x+1)+V189EvenSlack x=3*(x+1) := by
  by_cases he : x%2=0
  · have hEven := v184_true_even_shortcut_identity x he
    simp only [V189EvenSlack,he,ite_true]
    omega
  · have hOdd : 2*shortcut x=3*x+1 := by
      simpa [he] using double_shortcut x
    simp only [V189EvenSlack,he,ite_false]
    omega

/-- Source-faithful prospective inverse-height loss; the
certificate explicitly uses original source n and original clock k. -/
def V189HeightDefect (n k : Nat) : Nat :=
  3^k*(n+1)-2^k*(iter shortcut k n+1)

theorem v189_defect_is_nonnegative_and_exact (n k : Nat) :
    2^k*(iter shortcut k n+1) +
      V189HeightDefect n k =3^k*(n+1) := by
  have hBound := v188_all_clock_inverse_height n k
  unfold V189HeightDefect
  omega

theorem v189_defect_zero_initial (n : Nat) :
    V189HeightDefect n 0=0 := by
  simp [V189HeightDefect,iter]

/-- Genuine all-clock source-specific defect recurrence.
The only newly generated distinction comes from an even step. -/
theorem v189_defect_one_step_recurrence (n k : Nat) :
    V189HeightDefect n (k+1) =
      3*V189HeightDefect n k +
        2^k*V189EvenSlack (iter shortcut k n) := by
  let x := iter shortcut k n
  have hStep := v189_one_step_exact_slack x
  have hPrev := v189_defect_is_nonnegative_and_exact n k
  have hNext := v189_defect_is_nonnegative_and_exact n (k+1)
  have hNextClock : iter shortcut (k+1) n=shortcut x := by
    dsimp [x]
    rw [iter_succ_last]
  have hScaled :
      2^(k+1)*(shortcut x+1)+2^k*V189EvenSlack x =
        3*(2^k*(x+1)) := by
    calc
      2^(k+1)*(shortcut x+1)+2^k*V189EvenSlack x =
          2^k*(2*(shortcut x+1)+V189EvenSlack x) := by
            simp only [Nat.pow_succ,Nat.mul_add]
            ac_rfl
      _ = 2^k*(3*(x+1)) := by rw [hStep]
      _ = 3*(2^k*(x+1)) := by ac_rfl
  have hOld :
      3*(2^k*(x+1))+3*V189HeightDefect n k =
        3^(k+1)*(n+1) := by
    calc
      3*(2^k*(x+1))+3*V189HeightDefect n k =
        3*(2^k*(iter shortcut k n+1)+V189HeightDefect n k) := by
          dsimp [x]
          simp [Nat.mul_add]
      _ = 3*(3^k*(n+1)) := by rw [hPrev]
      _ = 3^(k+1)*(n+1) := by
        simp only [Nat.pow_succ]
        ac_rfl
  rw [hNextClock] at hNext
  omega

/-- If every original endpoint before clock k is odd, there is
NO inverse-height loss: all those states may be identified under
this particular protected consequence. -/
theorem v189_all_odd_prefix_has_zero_defect
    (n k : Nat)
    (hOdd : ∀ t : Nat, t<k → iter shortcut t n%2≠0) :
    V189HeightDefect n k=0 := by
  induction k with
  | zero => exact v189_defect_zero_initial n
  | succ k ih =>
      have hPrev : ∀ t : Nat, t<k → iter shortcut t n%2≠0 := by
        intro t ht
        exact hOdd t (by omega)
      have hLast := hOdd k (by omega)
      rw [v189_defect_one_step_recurrence]
      rw [ih hPrev]
      simp [V189EvenSlack,hLast]

/-- In a true two-clock source meeting, the whole effect of
the first source's even-step history on the inverse-height
comparison is the SINGLE certified scalar D(n,i). -/
theorem v189_true_two_clock_source_budget
    (n p i j : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p) :
    3^i*2^j*(n+1) <=
      3^j*2^i*(p+1) + 2^j*V189HeightDefect n i := by
  let y := iter shortcut i n
  have hD : 2^i*(y+1)+V189HeightDefect n i =
      3^i*(n+1) := by
    simpa only [y] using v189_defect_is_nonnegative_and_exact n i
  have hBack : 2^j*(y+1)<=3^j*(p+1) := by
    have hp := v188_all_clock_inverse_height p j
    rw [←hMeet] at hp
    exact hp
  have hScaled :
      2^i*(2^j*(y+1)) <= 2^i*(3^j*(p+1)) :=
    Nat.mul_le_mul_left _ hBack
  calc
    3^i*2^j*(n+1) = 2^j*(3^i*(n+1)) := by ac_rfl
    _ = 2^j*(2^i*(y+1)+V189HeightDefect n i) := by rw [hD]
    _ = 2^i*(2^j*(y+1))+2^j*V189HeightDefect n i := by
      simp only [Nat.mul_add]
      ac_rfl
    _ <= 2^i*(3^j*(p+1))+2^j*V189HeightDefect n i :=
      Nat.add_le_add_right hScaled _
    _ = 3^j*2^i*(p+1)+2^j*V189HeightDefect n i := by ac_rfl

/-- All-odd Mersenne prefixes have ZERO defect; we therefore
recover the V188 sharp early-clock lower-source impossibility
without allocating a per-parity-step history. -/
theorem v189_mersenne_prefix_defect_zero
    (K i : Nat) (hi : i<=K) :
    V189HeightDefect (2^K-1) i = 0 := by
  apply v189_all_odd_prefix_has_zero_defect
  intro t ht
  have htK : t<K := by omega
  have h := v182_mersenne_odd_at_each_prefix_step K t htK
  omega

#print axioms v189_one_step_exact_slack
#print axioms v189_defect_is_nonnegative_and_exact
#print axioms v189_defect_one_step_recurrence
#print axioms v189_all_odd_prefix_has_zero_defect
#print axioms v189_true_two_clock_source_budget
#print axioms v189_mersenne_prefix_defect_zero

end SourceProduct
end CollatzFinal
