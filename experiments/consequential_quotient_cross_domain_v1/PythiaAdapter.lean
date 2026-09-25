import Pythia.Finance.Portfolio.InformationRatio
import Pythia.MathGraphConsequentialQuotient

namespace MathGraphPythiaAdapter

open MathGraphConsequentialQuotient
open Pythia.Finance

structure IRState where
  alpha : ℝ
  trackingError : ℝ

def scaleIR (c : ℝ) (p : IRState) : IRState :=
  ⟨c * p.alpha, c * p.trackingError⟩

def PositiveScaleEq (p q : IRState) : Prop :=
  ∃ c : ℝ, 0 < c ∧ q = scaleIR c p

theorem positiveScale_refl (p : IRState) : PositiveScaleEq p p := by
  refine ⟨1, zero_lt_one, ?_⟩
  cases p
  simp [scaleIR]

theorem positiveScale_symm {p q : IRState}
    (h : PositiveScaleEq p q) : PositiveScaleEq q p := by
  rcases h with ⟨c, hc, rfl⟩
  refine ⟨c⁻¹, inv_pos.mpr hc, ?_⟩
  cases p
  simp [scaleIR, hc.ne']

theorem positiveScale_trans {p q r : IRState}
    (hpq : PositiveScaleEq p q) (hqr : PositiveScaleEq q r) :
    PositiveScaleEq p r := by
  rcases hpq with ⟨c, hc, rfl⟩
  rcases hqr with ⟨d, hd, rfl⟩
  refine ⟨d * c, mul_pos hd hc, ?_⟩
  cases p
  simp [scaleIR, mul_assoc]

noncomputable def irObserve (p : IRState) : ℝ :=
  informationRatio p.alpha p.trackingError

theorem irObserve_respects {p q : IRState} (h : PositiveScaleEq p q) :
    irObserve p = irObserve q := by
  rcases h with ⟨c, hc, rfl⟩
  unfold irObserve scaleIR
  exact (informationRatio_scale_invariant hc p.alpha p.trackingError).symm

noncomputable def irConsequenceSpec : ConsequenceSpec IRState ℝ where
  rel := PositiveScaleEq
  rel_refl := positiveScale_refl
  rel_symm := positiveScale_symm
  rel_trans := positiveScale_trans
  observe := irObserve
  observe_respects := irObserve_respects

theorem pythia_scale_states_collapse (p : IRState) (c : ℝ) (hc : 0 < c) :
    irConsequenceSpec.project p = irConsequenceSpec.project (scaleIR c p) :=
  irConsequenceSpec.project_eq_of_rel ⟨c, hc, rfl⟩

theorem pythia_information_ratio_factors :
    irConsequenceSpec.observe =
      fun x => irConsequenceSpec.quotientObserve (irConsequenceSpec.project x) :=
  irConsequenceSpec.factorization

end MathGraphPythiaAdapter
