
/-! MathGraph V4 quotient-factorization probe: softmax_reducev. -/

namespace VeriTile.Bench.TritonBenchG.SoftmaxReducev

open MathGraphNormalizationQuotient
open scoped BigOperators

theorem mathgraph_v4_softmax_reducev_gauge
    {S BLOCK_DMODEL : Nat} (qk : Fin S → ℝ) (M : ℝ)
    (v : Fin S → Fin BLOCK_DMODEL → ℝ) (d : Fin BLOCK_DMODEL) :
    GaugeEq
      ⟨(∑ n : Fin S, Real.exp (qk n) * v n d),
        (∑ n : Fin S, Real.exp (qk n))⟩
      ⟨softmaxReducevAcc qk M v d, softmaxReducevDenom qk M⟩ := by
  refine ⟨Real.exp (-M), Real.exp_ne_zero _, ?_⟩
  apply RatioState.ext
  · exact srWeightedSum_acc_shift qk M v d
  · exact srWeightedSum_denom_shift qk M

theorem mathgraph_v4_softmax_reducev_observation
    {S BLOCK_DMODEL : Nat} (qk : Fin S → ℝ) (M : ℝ)
    (v : Fin S → Fin BLOCK_DMODEL → ℝ) (d : Fin BLOCK_DMODEL) :
    observe ⟨softmaxReducevAcc qk M v d, softmaxReducevDenom qk M⟩
      =
    observe
      ⟨(∑ n : Fin S, Real.exp (qk n) * v n d),
        (∑ n : Fin S, Real.exp (qk n))⟩ :=
  (observe_eq_of_gauge (mathgraph_v4_softmax_reducev_gauge qk M v d)).symm

end VeriTile.Bench.TritonBenchG.SoftmaxReducev
