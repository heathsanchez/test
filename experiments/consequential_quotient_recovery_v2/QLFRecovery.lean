import QLF_StateSpace
import MathGraphConsequentialQuotient
import MathGraphObservationKernel
import MathGraphQLFBornAdapter

namespace MathGraphQLFRecovery

open MathGraphConsequentialQuotient
open MathGraphObservationKernel
open MathGraphQLFBornAdapter
open scoped BigOperators

abbrev ValidWeightState (n : Nat) :=
  {w : WeightState n // (∑ j, w j) ≠ 0}

noncomputable def validWeightObserve {n : Nat}
    (w : ValidWeightState n) : Fin n → ℚ :=
  normalizedWeights w.1

def ValidWeightGaugeEq {n : Nat}
    (w₁ w₂ : ValidWeightState n) : Prop :=
  WeightGaugeEq w₁.1 w₂.1

theorem validWeightGaugeEq_iff_observationEq {n : Nat}
    (w₁ w₂ : ValidWeightState n) :
    ValidWeightGaugeEq w₁ w₂ ↔
      ObservationEq validWeightObserve w₁ w₂ := by
  constructor
  · intro h
    exact normalizedWeights_respects h
  · intro h
    change normalizedWeights w₁.1 = normalizedWeights w₂.1 at h
    let s₁ : ℚ := ∑ j, w₁.1 j
    let s₂ : ℚ := ∑ j, w₂.1 j
    have hs₁ : s₁ ≠ 0 := by
      simpa [s₁] using w₁.property
    have hs₂ : s₂ ≠ 0 := by
      simpa [s₂] using w₂.property
    refine ⟨s₂ / s₁, div_ne_zero hs₂ hs₁, ?_⟩
    funext k
    have hk := congrFun h k
    unfold normalizedWeights at hk
    have hcross : w₁.1 k * s₂ = w₂.1 k * s₁ := by
      dsimp [s₁, s₂]
      exact (div_eq_div_iff w₁.property w₂.property).mp hk
    unfold scaleWeights
    calc
      w₂.1 k = (w₂.1 k * s₁) / s₁ := by
        rw [mul_div_cancel_right₀ _ hs₁]
      _ = (w₁.1 k * s₂) / s₁ := by
        rw [← hcross]
      _ = (s₂ / s₁) * w₁.1 k := by ring

theorem validWeightGauge_greatest_safe {n : Nat}
    {R : ValidWeightState n → ValidWeightState n → Prop}
    (hR : SafeRelation validWeightObserve R) :
    ∀ ⦃p q⦄, R p q → ValidWeightGaugeEq p q := by
  intro p q hpq
  exact (validWeightGaugeEq_iff_observationEq p q).2 (hR hpq)

end MathGraphQLFRecovery
