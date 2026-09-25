import Pythia.MathGraphConsequentialQuotient
import Pythia.MathGraphObservationKernel
import Pythia.MathGraphPythiaAdapter

namespace MathGraphPythiaRecovery

open MathGraphObservationKernel
open MathGraphPythiaAdapter
open Pythia.Finance

@[ext] theorem IRState.ext {p q : IRState}
    (ha : p.alpha = q.alpha)
    (ht : p.trackingError = q.trackingError) : p = q := by
  cases p
  cases q
  simp_all

abbrev ValidIRState := {p : IRState // 0 < p.trackingError}

noncomputable def validIRObserve (p : ValidIRState) : ℝ :=
  irObserve p.1

def ValidPositiveScaleEq (p q : ValidIRState) : Prop :=
  PositiveScaleEq p.1 q.1

theorem validPositiveScaleEq_iff_observationEq
    (p q : ValidIRState) :
    ValidPositiveScaleEq p q ↔
      ObservationEq validIRObserve p q := by
  constructor
  · intro h
    exact irObserve_respects h
  · intro h
    change irObserve p.1 = irObserve q.1 at h
    unfold irObserve informationRatio at h
    have hcross :
        p.1.alpha * q.1.trackingError =
          q.1.alpha * p.1.trackingError :=
      (div_eq_div_iff (ne_of_gt p.property) (ne_of_gt q.property)).mp h
    let c : ℝ := q.1.trackingError / p.1.trackingError
    refine ⟨c, div_pos q.property p.property, ?_⟩
    apply IRState.ext
    · dsimp [scaleIR, c]
      calc
        q.1.alpha =
            (q.1.alpha * p.1.trackingError) / p.1.trackingError := by
              field_simp [ne_of_gt p.property]
        _ = (p.1.alpha * q.1.trackingError) / p.1.trackingError := by
              rw [← hcross]
        _ = (q.1.trackingError / p.1.trackingError) * p.1.alpha := by ring
    · dsimp [scaleIR, c]
      field_simp [ne_of_gt p.property]

theorem validPositiveScale_greatest_safe
    {R : ValidIRState → ValidIRState → Prop}
    (hR : SafeRelation validIRObserve R) :
    ∀ ⦃p q⦄, R p q → ValidPositiveScaleEq p q := by
  intro p q hpq
  exact (validPositiveScaleEq_iff_observationEq p q).2 (hR hpq)

end MathGraphPythiaRecovery
