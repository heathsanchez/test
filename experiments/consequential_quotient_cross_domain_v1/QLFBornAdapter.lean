import QLF_StateSpace
import MathGraphConsequentialQuotient

namespace MathGraphQLFBornAdapter

open MathGraphConsequentialQuotient
open QLF.StateSpace
open scoped BigOperators

abbrev WeightState (n : Nat) := Fin n → ℚ

def scaleWeights {n : Nat} (c : ℚ) (w : WeightState n) : WeightState n :=
  fun j => c * w j

noncomputable def normalizedWeights {n : Nat} (w : WeightState n) : Fin n → ℚ :=
  fun k => w k / ∑ j, w j

def WeightGaugeEq {n : Nat} (w₁ w₂ : WeightState n) : Prop :=
  ∃ c : ℚ, c ≠ 0 ∧ w₂ = scaleWeights c w₁

theorem weightGauge_refl {n : Nat} (w : WeightState n) : WeightGaugeEq w w := by
  refine ⟨1, one_ne_zero, ?_⟩
  funext j
  simp [scaleWeights]

theorem weightGauge_symm {n : Nat} {w₁ w₂ : WeightState n}
    (h : WeightGaugeEq w₁ w₂) : WeightGaugeEq w₂ w₁ := by
  rcases h with ⟨c, hc, rfl⟩
  refine ⟨c⁻¹, inv_ne_zero hc, ?_⟩
  funext j
  simp [scaleWeights, hc]

theorem weightGauge_trans {n : Nat} {w₁ w₂ w₃ : WeightState n}
    (h12 : WeightGaugeEq w₁ w₂) (h23 : WeightGaugeEq w₂ w₃) :
    WeightGaugeEq w₁ w₃ := by
  rcases h12 with ⟨c, hc, rfl⟩
  rcases h23 with ⟨d, hd, rfl⟩
  refine ⟨d * c, mul_ne_zero hd hc, ?_⟩
  funext j
  simp [scaleWeights, mul_assoc]

theorem normalizedWeights_respects {n : Nat} {w₁ w₂ : WeightState n}
    (h : WeightGaugeEq w₁ w₂) :
    normalizedWeights w₁ = normalizedWeights w₂ := by
  rcases h with ⟨c, hc, rfl⟩
  funext k
  unfold normalizedWeights scaleWeights
  rw [← Finset.mul_sum]
  exact (mul_div_mul_left _ _ hc).symm

noncomputable def bornConsequenceSpec (n : Nat) :
    ConsequenceSpec (WeightState n) (Fin n → ℚ) where
  rel := WeightGaugeEq
  rel_refl := weightGauge_refl
  rel_symm := weightGauge_symm
  rel_trans := weightGauge_trans
  observe := normalizedWeights
  observe_respects := normalizedWeights_respects

noncomputable def gaussianWeights {n : Nat} (v : Fin n → GaussianInt) : WeightState n :=
  fun j => (Zsqrtd.norm (v j) : ℚ)

theorem bornProb_eq_generic_observer {n : Nat} (v : Fin n → GaussianInt) (k : Fin n) :
    QLF.StateSpace.bornProb v k = (bornConsequenceSpec n).observe (gaussianWeights v) k := by
  rfl

theorem gaussian_global_scale_gauge {n : Nat}
    (g : GaussianInt) (v : Fin n → GaussianInt)
    (hg : (Zsqrtd.norm g : ℚ) ≠ 0) :
    WeightGaugeEq (gaussianWeights v) (gaussianWeights (fun j => g * v j)) := by
  refine ⟨(Zsqrtd.norm g : ℚ), hg, ?_⟩
  funext j
  simp [gaussianWeights, scaleWeights, Zsqrtd.norm_mul]
  push_cast
  ring

theorem qlf_scaled_states_collapse {n : Nat}
    (g : GaussianInt) (v : Fin n → GaussianInt)
    (hg : (Zsqrtd.norm g : ℚ) ≠ 0) :
    (bornConsequenceSpec n).project (gaussianWeights v) =
      (bornConsequenceSpec n).project (gaussianWeights (fun j => g * v j)) :=
  (bornConsequenceSpec n).project_eq_of_rel (gaussian_global_scale_gauge g v hg)

theorem source_born_scale_matches_generic {n : Nat}
    (g : GaussianInt) (v : Fin n → GaussianInt)
    (hg : (Zsqrtd.norm g : ℚ) ≠ 0) :
    (bornConsequenceSpec n).observe (gaussianWeights (fun j => g * v j))
      = (bornConsequenceSpec n).observe (gaussianWeights v) := by
  funext k
  rw [← bornProb_eq_generic_observer, ← bornProb_eq_generic_observer]
  exact QLF.StateSpace.bornProb_global_scale g v k hg

end MathGraphQLFBornAdapter
