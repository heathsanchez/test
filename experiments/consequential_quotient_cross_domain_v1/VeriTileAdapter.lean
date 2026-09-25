import VeriTile.MathGraphConsequentialQuotient
import VeriTile.MathGraphNormalizationQuotient

namespace MathGraphVeriTileAdapter

open MathGraphConsequentialQuotient
open MathGraphNormalizationQuotient

noncomputable def gaugeConsequenceSpec : ConsequenceSpec RatioState ℝ where
  rel := GaugeEq
  rel_refl := gauge_refl
  rel_symm := gauge_symm
  rel_trans := gauge_trans
  observe := observe
  observe_respects := observe_eq_of_gauge

theorem v4_is_generic_consequence_quotient :
    gaugeConsequenceSpec.observe =
      fun x => gaugeConsequenceSpec.quotientObserve (gaugeConsequenceSpec.project x) :=
  gaugeConsequenceSpec.factorization

theorem v4_gauge_states_collapse {p q : RatioState} (h : GaugeEq p q) :
    gaugeConsequenceSpec.project p = gaugeConsequenceSpec.project q :=
  gaugeConsequenceSpec.project_eq_of_rel h

end MathGraphVeriTileAdapter
