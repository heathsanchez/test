import MathGraphGenericGauge

namespace MathGraphFactorWitness

open MathGraphGenericGauge

structure CommonFactorWitness
    {K : Type*} [CommGroupWithZero K]
    (p q : RatioState K) where
  factor : K
  factor_ne_zero : factor ≠ 0
  num_eq : q.num = factor * p.num
  den_eq : q.den = factor * p.den

theorem toGaugeEq
    {K : Type*} [CommGroupWithZero K]
    {p q : RatioState K}
    (w : CommonFactorWitness p q) :
    GaugeEq p q := by
  refine ⟨w.factor, w.factor_ne_zero, ?_⟩
  apply RatioState.ext
  · simpa [scale] using w.num_eq
  · simpa [scale] using w.den_eq

/-- Compiled protected consequence: a verified common-factor witness is enough. -/
theorem compileObservation
    {K : Type*} [CommGroupWithZero K]
    {p q : RatioState K}
    (w : CommonFactorWitness p q) :
    observe p = observe q :=
  observe_eq_of_gauge (toGaugeEq w)

end MathGraphFactorWitness
