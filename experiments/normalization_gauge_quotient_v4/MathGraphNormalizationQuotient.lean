import Mathlib
import VeriTile.MathGraphGaugeCapability

namespace MathGraphNormalizationQuotient

structure RatioState where
  num : ℝ
  den : ℝ
deriving Repr

def scale (c : ℝ) (p : RatioState) : RatioState :=
  ⟨c * p.num, c * p.den⟩

def observe (p : RatioState) : ℝ :=
  p.num / p.den

/-- Representation equivalence under a shared nonzero scalar. -/
def GaugeEq (p q : RatioState) : Prop :=
  ∃ c : ℝ, c ≠ 0 ∧ q = scale c p

theorem gauge_refl (p : RatioState) : GaugeEq p p := by
  refine ⟨1, one_ne_zero, ?_⟩
  cases p
  simp [scale]

theorem gauge_symm {p q : RatioState} (h : GaugeEq p q) : GaugeEq q p := by
  rcases h with ⟨c, hc, rfl⟩
  refine ⟨c⁻¹, inv_ne_zero hc, ?_⟩
  cases p
  simp [scale, hc]

theorem gauge_trans {p q r : RatioState}
    (hpq : GaugeEq p q) (hqr : GaugeEq q r) : GaugeEq p r := by
  rcases hpq with ⟨c, hc, rfl⟩
  rcases hqr with ⟨d, hd, rfl⟩
  refine ⟨d * c, mul_ne_zero hd hc, ?_⟩
  cases p
  simp [scale, mul_assoc]

def gaugeSetoid : Setoid RatioState where
  r := GaugeEq
  iseqv := ⟨gauge_refl, gauge_symm, gauge_trans⟩

/--
The protected normalized observation is constant on a gauge-equivalence class.
The arithmetic authority is delegated to the previously qualified
`common_factor_ratio` capability.
-/
theorem observe_eq_of_gauge {p q : RatioState} (h : GaugeEq p q) :
    observe p = observe q := by
  rcases h with ⟨c, hc, rfl⟩
  unfold observe scale
  exact (MathGraphGaugeCapability.common_factor_ratio
    c p.num p.den (c * p.num) (c * p.den) hc rfl rfl)

abbrev GaugeQuotient := Quotient gaugeSetoid

def quotientObserve : GaugeQuotient → ℝ :=
  Quotient.lift observe (fun _ _ h => observe_eq_of_gauge h)

@[simp] theorem quotientObserve_mk (p : RatioState) :
    quotientObserve (Quotient.mk gaugeSetoid p) = observe p := rfl

end MathGraphNormalizationQuotient
