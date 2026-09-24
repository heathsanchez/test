
/-! ## MathGraph bounded capability-transfer probe

This theorem is appended only in the ephemeral CI checkout. It intentionally
does not call the file's existing `srWeightedSum_shift_invariant`; it unfolds
the held-out closed form and instantiates the independently compiled generic
capability directly.
-/

namespace VeriTile.Bench.TritonBenchG.SoftmaxReducev

theorem mathgraph_transfer_srWeightedSum_shift_invariant
    {S BLOCK_DMODEL : Nat} (qk : Fin S → ℝ)
    (v : Fin S → Fin BLOCK_DMODEL → ℝ) (d : Fin BLOCK_DMODEL) (M₁ M₂ : ℝ) :
    softmaxReducevWeightedSum qk M₁ v d
      = softmaxReducevWeightedSum qk M₂ v d := by
  unfold softmaxReducevWeightedSum softmaxReducevAcc softmaxReducevDenom softmaxWeight
  exact MathGraphShiftCapability.weighted_shift_invariant qk v d M₁ M₂

end VeriTile.Bench.TritonBenchG.SoftmaxReducev
