import VeriTile.MathGraphObservationKernel
import VeriTile.MathGraphNormalizationQuotient

namespace MathGraphVeriTileRecovery

open MathGraphObservationKernel
open MathGraphNormalizationQuotient

abbrev ValidRatioState := {p : RatioState // p.den ≠ 0}

noncomputable def validObserve (p : ValidRatioState) : ℝ :=
  observe p.1

def ValidGaugeEq (p q : ValidRatioState) : Prop :=
  GaugeEq p.1 q.1

theorem validGaugeEq_iff_observationEq (p q : ValidRatioState) :
    ValidGaugeEq p q ↔ ObservationEq validObserve p q := by
  constructor
  · intro h
    exact observe_eq_of_gauge h
  · intro h
    change observe p.1 = observe q.1 at h
    unfold observe at h
    have hcross :
        p.1.num * q.1.den = q.1.num * p.1.den :=
      (div_eq_div_iff p.property q.property).mp h
    let c : ℝ := q.1.den / p.1.den
    refine ⟨c, div_ne_zero q.property p.property, ?_⟩
    apply RatioState.ext
    · dsimp [scale, c]
      calc
        q.1.num = (q.1.num * p.1.den) / p.1.den := by
          field_simp [p.property]
        _ = (p.1.num * q.1.den) / p.1.den := by
          rw [← hcross]
        _ = (q.1.den / p.1.den) * p.1.num := by ring
    · dsimp [scale, c]
      field_simp [p.property]

/--
On admissible ratio states, the V4 gauge relation is not merely safe: it is
exactly the canonical observation kernel, hence the greatest safe relation.
-/
theorem validGauge_greatest_safe
    {R : ValidRatioState → ValidRatioState → Prop}
    (hR : SafeRelation validObserve R) :
    ∀ ⦃p q⦄, R p q → ValidGaugeEq p q := by
  intro p q hpq
  exact (validGaugeEq_iff_observationEq p q).2 (hR hpq)

end MathGraphVeriTileRecovery
