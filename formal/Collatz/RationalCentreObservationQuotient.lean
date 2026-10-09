import Collatz.SourceCentreTransportSeparator

namespace CollatzFinal
namespace SourceProduct

/-!
V147 — OBSERVATION-LAWFUL RATIONAL SOURCE-CENTRE QUOTIENT.

V146 rejected collapsing arbitrary actual source centres to finitely
many nonpositive INTEGERS, even under mod4=3 and three true steps of
no direct descent. V146 separately established the exact V95 affine
source congruence and the 27-root rational centre -13/9.

The correct candidate grammar keeps an ODD denominator A and
nonnegative numerator R. A source n obeys the dyadic source test
    2^B | (A*n + R).
Two such certificate states are merged only if
    A' * R = A * R',
meaning they represent the SAME exact nonpositive rational centre.
This is a proven congruence-preserving relation for EVERY source n
and EVERY dyadic precision B. The proof uses exact odd cancellation,
not a floating approximation or finite test corpus.

This quotient is NOT asserted finite and DOES NOT project the
original source, clocks, or genuine lower-positive-source witness
away. It is a typed observation stratum, not a new convergence QED.

Concrete adversarial controls:
  centres (-3) and (-1) for future-coalescent original sources
  21 and 3 are DISTINCT despite true two-clock meeting;
  (9,13) and (27,39) are exact congruence-equivalent
  presentations of the rational source centre -13/9;
  for ALL t, the V146 growing 27-root family admits the SAME
  rational source-centre certificate (9,13) at precision 6t+5,
  but no fixed finite integer-centre family covers it.
Only observation-equivalence, not universal NoExit exhaustion, is
established. GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- Cancel an ODD positive coefficient from divisibility by 2^B,
    for every natural B. This is the arithmetic kernel enabling
    faithful rational-centre observational equivalence. -/
theorem odd_factor_cancel_dyadic_divisibility
    (a B : Nat) (ha : a % 2 = 1) :
    ∀ m : Nat, (2 ^ B ∣ a * m) → 2 ^ B ∣ m := by
  induction B with
  | zero =>
      intro m _
      simp
  | succ B ih =>
      intro m hdiv
      obtain ⟨q, hq⟩ := hdiv
      have hevenProduct : (a * m) % 2 = 0 := by
        rw [hq, Nat.pow_succ]
        simp [Nat.mul_mod, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      have hevenM : m % 2 = 0 := by
        rw [Nat.mul_mod, ha] at hevenProduct
        omega
      have hdecomp : m = 2 * (m / 2) := by omega
      have hsmaller : 2 ^ B ∣ a * (m / 2) := by
        refine ⟨q, ?_⟩
        have hscaled : 2 * (a * (m / 2)) =
            2 * (2 ^ B * q) := by
          calc
            2 * (a * (m / 2)) = a * m := by
              rw [hdecomp]
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
            _ = 2 ^ (B + 1) * q := hq
            _ = 2 * (2 ^ B * q) := by
              simp [Nat.pow_succ, Nat.mul_assoc,
                Nat.mul_comm, Nat.mul_left_comm]
        omega
      obtain ⟨v, hv⟩ := ih (m / 2) hsmaller
      refine ⟨v, ?_⟩
      rw [hdecomp, hv]
      simp [Nat.pow_succ, Nat.mul_assoc,
        Nat.mul_comm, Nat.mul_left_comm]

structure RationalSourceCentreV147 where
  oddCoefficient : Nat
  offset : Nat
  coefficientOdd : oddCoefficient % 2 = 1

/-- Exact 2-adic source congruence test, retaining the original n. -/
def v147Observes
    (c : RationalSourceCentreV147) (n B : Nat) : Prop :=
  2 ^ B ∣ c.oddCoefficient * n + c.offset

/-- Cross-multiplication, not a heuristic ratio comparison. -/
def v147CentreEquivalent
    (x y : RationalSourceCentreV147) : Prop :=
  y.oddCoefficient * x.offset = x.oddCoefficient * y.offset

/-- A one-direction exact observation-preserving transport. The
    cancellation condition is GUARANTEED by the declared odd
    denominator, for all original sources and all future precisions. -/
theorem v147_cross_equal_transports_source_observation
    (x y : RationalSourceCentreV147)
    (n B : Nat)
    (heq : v147CentreEquivalent x y)
    (hobs : v147Observes x n B) :
    v147Observes y n B := by
  obtain ⟨q, hq⟩ := hobs
  have hscaled :
      2 ^ B ∣ y.oddCoefficient *
        (x.oddCoefficient * n + x.offset) := by
    refine ⟨y.oddCoefficient * q, ?_⟩
    rw [hq]
    simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hcross :
      y.oddCoefficient * (x.oddCoefficient * n + x.offset) =
        x.oddCoefficient * (y.oddCoefficient * n + y.offset) := by
    calc
      y.oddCoefficient * (x.oddCoefficient * n + x.offset) =
          y.oddCoefficient * x.oddCoefficient * n +
            y.oddCoefficient * x.offset := by
            simp [Nat.mul_add, Nat.mul_assoc]
      _ = x.oddCoefficient * y.oddCoefficient * n +
            x.oddCoefficient * y.offset := by
            rw [Nat.mul_comm y.oddCoefficient x.oddCoefficient]
            exact congrArg (fun z =>
                x.oddCoefficient * y.oddCoefficient * n + z) heq
      _ = x.oddCoefficient * (y.oddCoefficient * n + y.offset) := by
            simp [Nat.mul_add, Nat.mul_assoc]
  rw [hcross] at hscaled
  exact odd_factor_cancel_dyadic_divisibility
    x.oddCoefficient B x.coefficientOdd
    (y.oddCoefficient * n + y.offset) hscaled

theorem v147_centre_equivalent_refl
    (x : RationalSourceCentreV147) :
    v147CentreEquivalent x x := rfl

theorem v147_centre_equivalent_symm
    (x y : RationalSourceCentreV147)
    (h : v147CentreEquivalent x y) :
    v147CentreEquivalent y x := h.symm

/-- Genuine rational-centre equivalence is transitive because every
    denominator is odd, hence strictly positive. -/
theorem v147_centre_equivalent_trans
    (x y z : RationalSourceCentreV147)
    (hxy : v147CentreEquivalent x y)
    (hyz : v147CentreEquivalent y z) :
    v147CentreEquivalent x z := by
  have hpos : 0 < y.oddCoefficient := by
    have hh := y.coefficientOdd
    omega
  have hscaled :
      y.oddCoefficient * (z.oddCoefficient * x.offset) =
      y.oddCoefficient * (x.oddCoefficient * z.offset) := by
    calc
      y.oddCoefficient * (z.oddCoefficient * x.offset) =
          z.oddCoefficient *
            (y.oddCoefficient * x.offset) := by
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ = z.oddCoefficient *
            (x.oddCoefficient * y.offset) := by rw [hxy]
      _ = x.oddCoefficient *
            (z.oddCoefficient * y.offset) := by
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ = x.oddCoefficient *
            (y.oddCoefficient * z.offset) := by rw [hyz]
      _ = y.oddCoefficient *
            (x.oddCoefficient * z.offset) := by
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  exact Nat.eq_of_mul_eq_mul_left hpos hscaled

def v147RationalCentreSetoid : Setoid RationalSourceCentreV147 where
  r := v147CentreEquivalent
  iseqv := ⟨(fun x => v147_centre_equivalent_refl x),
    (fun x y h => v147_centre_equivalent_symm x y h),
    (fun x y z hxy hyz => v147_centre_equivalent_trans x y z hxy hyz)⟩

def V147RationalCentreClass : Type :=
  Quotient v147RationalCentreSetoid

/-- The quotient is admissible ONLY because both implications have
    just been proved against every protected source-congruence test. -/
theorem v147_observation_iff_for_exact_centre_class
    (x y : RationalSourceCentreV147)
    (n B : Nat)
    (hxy : v147CentreEquivalent x y) :
    v147Observes x n B ↔ v147Observes y n B := by
  constructor
  · exact v147_cross_equal_transports_source_observation x y n B hxy
  · exact v147_cross_equal_transports_source_observation y x n B hxy.symm

/-- The protected original-source observation actually factors
    through the proven quotient, for all n and all B. -/
def v147QuotientObservation
    (n B : Nat) : V147RationalCentreClass → Prop :=
  Quotient.lift (fun x => v147Observes x n B)
    (by
      intro x y h
      exact propext (v147_observation_iff_for_exact_centre_class x y n B h))

theorem v147_exact_observation_factors_through_quotient
    (x : RationalSourceCentreV147) (n B : Nat) :
    v147QuotientObservation n B
      (Quotient.mk v147RationalCentreSetoid x) ↔
      v147Observes x n B := by
  rfl

/-- Two notationally distinct pairs for EXACTLY the same -13/9
    rational source centre belong to one protected observation class. -/
def v147CentreNineThirteen : RationalSourceCentreV147 :=
  ⟨9, 13, by decide⟩

def v147CentreTwentySevenThirtyNine : RationalSourceCentreV147 :=
  ⟨27, 39, by decide⟩

theorem v147_positive_rational_equivalence :
    v147CentreEquivalent
      v147CentreNineThirteen
      v147CentreTwentySevenThirtyNine := by
  decide

/-- The V146 family uses ONE exact rational centre-class for
    infinitely many distinct positive ORIGINAL sources, although no
    finite integer-centre family can explain the congruences.

    Sources change with t, as V146 explicitly protects. -/
theorem v147_source27_shadow_family_same_rational_observation
    (t : Nat) :
    v147Observes v147CentreNineThirteen
      (shadowSource t) (shadowPrecision t) := by
  refine ⟨8, ?_⟩
  change 9 * shadowSource t + 13 =
    2 ^ shadowPrecision t * 8
  have h := shadow_source_affine_identity t
  simpa [shadowModulus, Nat.mul_comm] using h

theorem v147_equivalent_form_27_39_observes_same_sources
    (n B : Nat) :
    v147Observes v147CentreNineThirteen n B ↔
    v147Observes v147CentreTwentySevenThirtyNine n B :=
  v147_observation_iff_for_exact_centre_class
    _ _ n B v147_positive_rational_equivalence

/-- This exact rational centre is NOT an integer centre -d for any
    d≥0; do not force it into V146's rejected integer-only grammar. -/
theorem v147_nine_thirteen_no_integer_centre
    (d : Nat) :
    ¬ v147CentreEquivalent
        v147CentreNineThirteen
        (⟨1, d, by decide⟩ : RationalSourceCentreV147) := by
  intro h
  change 13 = 9 * d at h
  omega

/-- The coalescent V128 true source pair 21↔3 has two distinct
    rational source-centre classes despite a genuine two-clock
    common endpoint 8. The equivalence relation on FUTURE ORBITS
    is therefore NOT the equivalence relation on this new proof type. -/
theorem v147_coalescence_does_not_identify_source_centre :
    iter shortcut 3 21 = iter shortcut 2 3 ∧
      ¬ v147CentreEquivalent
        (⟨3, 9, by decide⟩ : RationalSourceCentreV147)
        (⟨9, 9, by decide⟩ : RationalSourceCentreV147) := by
  decide

#print axioms odd_factor_cancel_dyadic_divisibility
#print axioms v147_cross_equal_transports_source_observation
#print axioms v147_centre_equivalent_trans
#print axioms v147_observation_iff_for_exact_centre_class
#print axioms v147_exact_observation_factors_through_quotient
#print axioms v147_positive_rational_equivalence
#print axioms v147_source27_shadow_family_same_rational_observation
#print axioms v147_equivalent_form_27_39_observes_same_sources
#print axioms v147_nine_thirteen_no_integer_centre
#print axioms v147_coalescence_does_not_identify_source_centre

end SourceProduct
end CollatzFinal
