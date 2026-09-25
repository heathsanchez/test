import Mathlib

namespace MathGraphGenericGauge

structure RatioState (K : Type*) [CommGroupWithZero K] where
  num : K
  den : K
deriving Repr

def scale {K : Type*} [CommGroupWithZero K]
    (c : K) (p : RatioState K) : RatioState K :=
  ⟨c * p.num, c * p.den⟩

def observe {K : Type*} [CommGroupWithZero K]
    (p : RatioState K) : K :=
  p.num / p.den

def GaugeEq {K : Type*} [CommGroupWithZero K]
    (p q : RatioState K) : Prop :=
  ∃ c : K, c ≠ 0 ∧ q = scale c p

theorem gauge_refl {K : Type*} [CommGroupWithZero K]
    (p : RatioState K) : GaugeEq p p := by
  refine ⟨1, one_ne_zero, ?_⟩
  cases p
  simp [scale]

theorem gauge_symm {K : Type*} [CommGroupWithZero K]
    {p q : RatioState K} (h : GaugeEq p q) : GaugeEq q p := by
  rcases h with ⟨c, hc, rfl⟩
  refine ⟨c⁻¹, inv_ne_zero hc, ?_⟩
  cases p
  simp [scale, hc]

theorem gauge_trans {K : Type*} [CommGroupWithZero K]
    {p q r : RatioState K}
    (hpq : GaugeEq p q) (hqr : GaugeEq q r) : GaugeEq p r := by
  rcases hpq with ⟨c, hc, rfl⟩
  rcases hqr with ⟨d, hd, rfl⟩
  refine ⟨d * c, mul_ne_zero hd hc, ?_⟩
  cases p
  simp [scale, mul_assoc]

def gaugeSetoid (K : Type*) [CommGroupWithZero K] : Setoid (RatioState K) where
  r := GaugeEq
  iseqv := ⟨gauge_refl, gauge_symm, gauge_trans⟩

/-- Normalized observation is invariant under shared nonzero scale. -/
theorem observe_eq_of_gauge {K : Type*} [CommGroupWithZero K]
    {p q : RatioState K} (h : GaugeEq p q) :
    observe p = observe q := by
  rcases h with ⟨c, hc, rfl⟩
  unfold observe scale
  exact (mul_div_mul_left p.num p.den hc).symm

abbrev GaugeQuotient (K : Type*) [CommGroupWithZero K] :=
  Quotient (gaugeSetoid K)

def quotientObserve {K : Type*} [CommGroupWithZero K] :
    GaugeQuotient K → K :=
  Quotient.lift observe (fun _ _ h => observe_eq_of_gauge h)

@[simp] theorem quotientObserve_mk {K : Type*} [CommGroupWithZero K]
    (p : RatioState K) :
    quotientObserve (Quotient.mk (gaugeSetoid K) p) = observe p := rfl

end MathGraphGenericGauge
