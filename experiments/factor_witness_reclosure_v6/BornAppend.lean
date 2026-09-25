
/-! V6 reclosure probe: QLF rational Born probability. -/

namespace QLF.StateSpace

open scoped BigOperators
open MathGraphGenericGauge
open MathGraphFactorWitness

theorem mathgraph_v6_bornProb_global_scale
    {n : ℕ} (g : GaussianInt) (v : Fin n → GaussianInt)
    (k : Fin n) (hg : (Zsqrtd.norm g : ℚ) ≠ 0) :
    bornProb (fun j => g * v j) k = bornProb v k := by
  simp only [bornProb, Zsqrtd.norm_mul]
  push_cast
  rw [← Finset.mul_sum]
  let p : RatioState ℚ :=
    ⟨(Zsqrtd.norm (v k) : ℚ),
      ∑ j, (Zsqrtd.norm (v j) : ℚ)⟩
  let q : RatioState ℚ :=
    ⟨(Zsqrtd.norm g : ℚ) * (Zsqrtd.norm (v k) : ℚ),
      (Zsqrtd.norm g : ℚ) * ∑ j, (Zsqrtd.norm (v j) : ℚ)⟩
  have w : CommonFactorWitness p q := by
    refine {
      factor := (Zsqrtd.norm g : ℚ)
      factor_ne_zero := hg
      num_eq := ?_
      den_eq := ?_
    }
    · rfl
    · rfl
  simpa [p, q, observe] using (compileObservation w).symm

end QLF.StateSpace
