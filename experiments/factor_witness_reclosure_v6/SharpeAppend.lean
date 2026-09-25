
/-! V6 reclosure probe: Pythia Sharpe ratio. -/

namespace Pythia.Finance

open MathGraphGenericGauge
open MathGraphFactorWitness

theorem mathgraph_v6_sharpeRatio_scale_invariant
    {α : ℝ} (hα : 0 < α) (μ rf σ : ℝ) :
    sharpeRatio (α * μ) (α * rf) (α * σ) = sharpeRatio μ rf σ := by
  unfold sharpeRatio
  rw [← mul_sub]
  let p : RatioState ℝ := ⟨μ - rf, σ⟩
  let q : RatioState ℝ := ⟨α * (μ - rf), α * σ⟩
  have w : CommonFactorWitness p q := by
    refine {
      factor := α
      factor_ne_zero := hα.ne'
      num_eq := ?_
      den_eq := ?_
    }
    · rfl
    · rfl
  simpa [p, q, observe] using (compileObservation w).symm

end Pythia.Finance
