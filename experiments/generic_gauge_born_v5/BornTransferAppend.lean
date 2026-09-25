
/-! MathGraph V5 cross-domain quotient-transfer probe.

This theorem is appended only in the ephemeral qualification checkout.
It does not call QLF.StateSpace.bornProb_global_scale.
-/

namespace QLF.StateSpace

open scoped BigOperators
open MathGraphGenericGauge

theorem mathgraph_v5_bornProb_global_scale
    {n : ℕ} (g : GaussianInt) (v : Fin n → GaussianInt)
    (k : Fin n) (hg : (Zsqrtd.norm g : ℚ) ≠ 0) :
    bornProb (fun j => g * v j) k = bornProb v k := by
  simp only [bornProb, Zsqrtd.norm_mul]
  push_cast
  rw [← Finset.mul_sum]
  have hGauge :
      GaugeEq
        (K := ℚ)
        ⟨(Zsqrtd.norm (v k) : ℚ),
          ∑ j, (Zsqrtd.norm (v j) : ℚ)⟩
        ⟨(Zsqrtd.norm g : ℚ) * (Zsqrtd.norm (v k) : ℚ),
          (Zsqrtd.norm g : ℚ) * ∑ j, (Zsqrtd.norm (v j) : ℚ)⟩ := by
    refine ⟨(Zsqrtd.norm g : ℚ), hg, rfl⟩
  simpa [observe] using (observe_eq_of_gauge hGauge).symm

end QLF.StateSpace
