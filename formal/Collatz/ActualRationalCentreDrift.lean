import Collatz.RationalCentreObservationQuotient
import Collatz.ParityCycleResidual

namespace CollatzFinal
namespace SourceProduct

/-!
V148 — CONSTRUCTIVE SEMANTIC SEPARATOR AGAINST FINITE ACTUAL
V147 CENTRE-CLASS STABILIZATION.

V147 proved quotient equivalence A'R=AR' is EXACTLY lawful for
the dyadic original-source observation family, for every n,B.

This file asks whether the *ACTUAL prefix certificate* of any one
positive source can eventually settle into a finite set of those
classes. The answer is NO, including the already-terminating 1↔2
cycle.

At time k:
  A_k=3^(oddCount n k), R_k=bias n k+2^k,
  source centre = -R_k/A_k.

If T^k(n) ODD, (A_(k+1),R_(k+1))=(3A_k,3R_k);
  the quotient centre is literally unchanged.

If T^k(n) EVEN, (A_(k+1),R_(k+1))=(A_k,R_k+2^k);
  the centre becomes strictly more negative, and can never revert
  because all subsequent centre evolution is nonincreasing.

V141 already formally proved any positive natural orbit has
arbitrarily late even times. Therefore, along the actual future of
EVERY positive n (including n=1), there are arbitrarily late
non-repeating V147 centre classes.

This disproves a proposed bridge that claims FINITENESS of the
actual evolving V147 source-centre classes from NoExit. It does
NOT refute a radically different NoExit-specific forcing theorem
producing OTHER rational-centre witnesses, and does not prove
Collatz. Future-coalescence, two-clock and original-source evidence
remain protected. GLOBAL COLLATZ UNKNOWN.
-/

def v148ActualCentre (n k : Nat) : RationalSourceCentreV147 :=
  ⟨3 ^ oddCount n k, bias n k + 2 ^ k,
    three_power_odd_mod_two (oddCount n k)⟩

/-- The actual ratio R/A is unchanged exactly at odd steps. -/
theorem v148_odd_step_preserves_exact_centre
    (n k : Nat)
    (ho : iter shortcut k n % 2 = 1) :
    v147CentreEquivalent
      (v148ActualCentre n k)
      (v148ActualCentre n (k + 1)) := by
  have he : ¬ iter shortcut k n % 2 = 0 := by omega
  have hA : (v148ActualCentre n (k+1)).oddCoefficient =
      3 * (v148ActualCentre n k).oddCoefficient := by
    simp [v148ActualCentre, oddCount, he, Nat.pow_succ,
      Nat.mul_comm]
  have hR : (v148ActualCentre n (k+1)).offset =
      3 * (v148ActualCentre n k).offset := by
    simp [v148ActualCentre, bias, he, Nat.pow_succ,
      Nat.mul_add, Nat.mul_assoc, Nat.mul_comm,
      Nat.mul_left_comm]
    omega
  change
    (v148ActualCentre n (k+1)).oddCoefficient *
      (v148ActualCentre n k).offset =
    (v148ActualCentre n k).oddCoefficient *
      (v148ActualCentre n (k+1)).offset
  rw [hA,hR]
  simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

/-- Even steps keep the denominator and add a positive 2^k
    to the numerator. This is STRICT drift of the exact rational
    source centre, not a heuristic approximation. -/
theorem v148_even_step_changes_numerator
    (n k : Nat)
    (he : iter shortcut k n % 2 = 0) :
    (v148ActualCentre n (k+1)).oddCoefficient =
      (v148ActualCentre n k).oddCoefficient ∧
    (v148ActualCentre n (k+1)).offset =
      (v148ActualCentre n k).offset + 2 ^ k := by
  constructor
  · simp [v148ActualCentre, oddCount, he]
  · change bias n (k+1) + 2^(k+1) =
        (bias n k + 2^k) + 2^k
    simp [bias, he, Nat.pow_succ]
    omega

def v148CrossLe
    (x y : RationalSourceCentreV147) : Prop :=
  y.oddCoefficient * x.offset ≤ x.oddCoefficient * y.offset

def v148CrossLt
    (x y : RationalSourceCentreV147) : Prop :=
  y.oddCoefficient * x.offset < x.oddCoefficient * y.offset

theorem v148_centre_odd_coeff_positive
    (x : RationalSourceCentreV147) :
    0 < x.oddCoefficient := by
  have h := x.coefficientOdd
  omega

theorem v148_even_step_strict_new_class
    (n k : Nat)
    (he : iter shortcut k n % 2 = 0) :
    v148CrossLt (v148ActualCentre n k)
      (v148ActualCentre n (k+1)) ∧
    ¬ v147CentreEquivalent (v148ActualCentre n k)
      (v148ActualCentre n (k+1)) := by
  obtain ⟨hA,hR⟩ :=
    v148_even_step_changes_numerator n k he
  have hapos : 0 < (v148ActualCentre n k).oddCoefficient :=
    v148_centre_odd_coeff_positive (v148ActualCentre n k)
  have hpow : 0 < (2 : Nat)^k :=
    Nat.pow_pos (by decide)
  have hmul : 0 < (v148ActualCentre n k).oddCoefficient * 2^k :=
    Nat.mul_pos hapos hpow
  have hstrict : v148CrossLt
      (v148ActualCentre n k)
      (v148ActualCentre n (k+1)) := by
    change
      (v148ActualCentre n (k+1)).oddCoefficient *
        (v148ActualCentre n k).offset <
      (v148ActualCentre n k).oddCoefficient *
        (v148ActualCentre n (k+1)).offset
    rw [hA,hR, Nat.mul_add]
    omega
  constructor
  · exact hstrict
  · intro hEq
    change
      (v148ActualCentre n (k+1)).oddCoefficient *
        (v148ActualCentre n k).offset =
      (v148ActualCentre n k).oddCoefficient *
        (v148ActualCentre n (k+1)).offset at hEq
    change
      (v148ActualCentre n (k+1)).oddCoefficient *
        (v148ActualCentre n k).offset <
      (v148ActualCentre n k).oddCoefficient *
        (v148ActualCentre n (k+1)).offset at hstrict
    omega

theorem v148_cross_le_trans
    (x y z : RationalSourceCentreV147)
    (hxy : v148CrossLe x y) (hyz : v148CrossLe y z) :
    v148CrossLe x z := by
  have hypos : 0 < y.oddCoefficient :=
    v148_centre_odd_coeff_positive y
  have hscaled :
      (z.oddCoefficient * x.offset) * y.oddCoefficient ≤
      (x.oddCoefficient * z.offset) * y.oddCoefficient := by
    calc
      (z.oddCoefficient * x.offset) * y.oddCoefficient =
          z.oddCoefficient * (y.oddCoefficient * x.offset) := by
            simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ ≤ z.oddCoefficient * (x.oddCoefficient * y.offset) :=
        Nat.mul_le_mul_left _ hxy
      _ = x.oddCoefficient * (z.oddCoefficient * y.offset) := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ ≤ x.oddCoefficient * (y.oddCoefficient * z.offset) :=
        Nat.mul_le_mul_left _ hyz
      _ = (x.oddCoefficient * z.offset) * y.oddCoefficient := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  exact Nat.le_of_mul_le_mul_right hscaled hypos

theorem v148_step_cross_nondecreasing (n k : Nat) :
    v148CrossLe (v148ActualCentre n k)
      (v148ActualCentre n (k+1)) := by
  by_cases he : iter shortcut k n % 2 = 0
  · exact Nat.le_of_lt
      (v148_even_step_strict_new_class n k he).1
  · have ho : iter shortcut k n % 2 = 1 := by omega
    have hEq := v148_odd_step_preserves_exact_centre n k ho
    change
      (v148ActualCentre n (k+1)).oddCoefficient *
        (v148ActualCentre n k).offset =
      (v148ActualCentre n k).oddCoefficient *
        (v148ActualCentre n (k+1)).offset at hEq
    exact Nat.le_of_eq hEq

/-- The exact rational drift is monotone across arbitrary true
    forward clocks: the quotient cannot return to an older centre
    once an EVEN-step strict change has occurred. -/
theorem v148_cross_nondecreasing_arbitrary_clocks
    (n i j : Nat) (hij : i ≤ j) :
    v148CrossLe (v148ActualCentre n i)
      (v148ActualCentre n j) := by
  have hstep : ∀ d : Nat,
      v148CrossLe (v148ActualCentre n i)
        (v148ActualCentre n (i+d)) := by
    intro d
    induction d with
    | zero =>
      change
        (v148ActualCentre n i).oddCoefficient *
          (v148ActualCentre n i).offset ≤
        (v148ActualCentre n i).oddCoefficient *
          (v148ActualCentre n i).offset
      omega
    | succ d ih =>
      have hle := v148_step_cross_nondecreasing n (i+d)
      have ht := v148_cross_le_trans
        (v148ActualCentre n i)
        (v148ActualCentre n (i+d))
        (v148ActualCentre n (i+d+1)) ih hle
      simpa [Nat.add_assoc] using ht
  have hsum : i + (j-i) = j := by omega
  simpa only [hsum] using hstep (j-i)

/-- V141 guarantees an even step beyond every clock for ALL
    positive original sources. Therefore the dynamically evolving
    V147 centre can NEVER stabilize: from every source-clock i
    there is a later true clock with a different quotient class.
    In fact, its strictly monotone sequence has infinitely many
    classes. The latter is not assumed as a finite-state lemma. -/
theorem v148_no_eventually_fixed_actual_centre_class
    (n : Nat) (hn : 0 < n) (i : Nat) :
    ∃ j : Nat, i < j ∧
      ¬ v147CentreEquivalent
        (v148ActualCentre n i)
        (v148ActualCentre n j) := by
  obtain ⟨e, hie, heven⟩ :=
    (every_positive_source_revisits_both_parities n hn).1 i
  have hle := v148_cross_nondecreasing_arbitrary_clocks n i e hie
  have hstrict := (v148_even_step_strict_new_class n e heven).1
  refine ⟨e+1, by omega, ?_⟩
  intro heq
  have hreverse : v148CrossLe
      (v148ActualCentre n (e+1))
      (v148ActualCentre n i) := by
    change
      (v148ActualCentre n i).oddCoefficient *
        (v148ActualCentre n (e+1)).offset ≤
      (v148ActualCentre n (e+1)).oddCoefficient *
        (v148ActualCentre n i).offset
    exact Nat.le_of_eq heq.symm
  have hback := v148_cross_le_trans
    (v148ActualCentre n (e+1))
    (v148ActualCentre n i)
    (v148ActualCentre n e) hreverse hle
  change
    (v148ActualCentre n e).oddCoefficient *
      (v148ActualCentre n (e+1)).offset ≤
    (v148ActualCentre n (e+1)).oddCoefficient *
      (v148ActualCentre n e).offset at hback
  change
    (v148ActualCentre n (e+1)).oddCoefficient *
      (v148ActualCentre n e).offset <
    (v148ActualCentre n e).oddCoefficient *
      (v148ActualCentre n (e+1)).offset at hstrict
  omega

/-- The terminal 1↔2 cycle itself witnesses the separation.
    Same eventual success does not mean any finite horizon of
    actual rational centre observations stops changing. -/
theorem v148_terminal_one_has_arbitrarily_late_new_centres
    (i : Nat) :
    ∃ j, i<j ∧ ¬ v147CentreEquivalent
        (v148ActualCentre 1 i) (v148ActualCentre 1 j) :=
  v148_no_eventually_fixed_actual_centre_class 1 (by decide) i

#print axioms v148_odd_step_preserves_exact_centre
#print axioms v148_even_step_changes_numerator
#print axioms v148_even_step_strict_new_class
#print axioms v148_cross_nondecreasing_arbitrary_clocks
#print axioms v148_no_eventually_fixed_actual_centre_class
#print axioms v148_terminal_one_has_arbitrarily_late_new_centres

end SourceProduct
end CollatzFinal
