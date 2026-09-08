import RankOneStress

/-! All-state minimality relative to the six-feature grammar frozen in
experiment.py at 2ea0ad0. The two cell means are always retained. This is a
quadratic-flux theorem, not a Navier–Stokes regularity theorem. -/
namespace CrossDomainResidual.Minimum

structure State where
  a : ℝ
  b : ℝ
  c : ℝ
  d : ℝ

inductive Feature where
  | mean_x | trace | xx | xy | yy | difference
  deriving DecidableEq, Repr

def means (s : State) : ℝ × ℝ := (s.a + s.c, s.b + s.d)
def flux (s : State) : ℝ × ℝ × ℝ :=
  (s.a*s.a+s.c*s.c, s.a*s.b+s.c*s.d, s.b*s.b+s.d*s.d)

def value : Feature → State → ℝ
  | .mean_x, s => s.a+s.c
  | .trace, s => s.a*s.a+s.c*s.c+s.b*s.b+s.d*s.d
  | .xx, s => s.a*s.a+s.c*s.c
  | .xy, s => s.a*s.b+s.c*s.d
  | .yy, s => s.b*s.b+s.d*s.d
  | .difference, s => s.a*s.a+s.c*s.c-(s.b*s.b+s.d*s.d)

def Determines (fs : List Feature) : Prop :=
  ∀ s t : State, means s = means t →
    (∀ f ∈ fs, value f s = value f t) → flux s = flux t

theorem two_features_suffice : Determines [.xy, .difference] := by
  intro s t hm hf
  have hxy := hf .xy (by simp)
  have hd := hf .difference (by simp)
  obtain ⟨hxx, _, hyy⟩ := CrossDomainResidual.twoCell_flux_determined
    s.a s.b s.c s.d t.a t.b t.c t.d
    (congrArg Prod.fst hm) (congrArg Prod.snd hm) hxy hd
  exact Prod.ext hxx (Prod.ext hxy hyy)

private def zero : State := ⟨0,0,0,0⟩
private def xPair : State := ⟨1,0,-1,0⟩
private def yPair : State := ⟨0,1,0,-1⟩
private def diagonal : State := ⟨1,1,-1,-1⟩

def witness : Feature → State × State
  | .mean_x => (xPair, zero)
  | .trace => (xPair, yPair)
  | .xx => (yPair, zero)
  | .xy => (xPair, zero)
  | .yy => (xPair, zero)
  | .difference => (diagonal, zero)

theorem witness_sound (f : Feature) :
    means (witness f).1 = means (witness f).2 ∧
    value f (witness f).1 = value f (witness f).2 ∧
    flux (witness f).1 ≠ flux (witness f).2 := by
  cases f <;> norm_num [witness, means, value, flux, xPair, yPair, diagonal, zero]

theorem no_single_feature (f : Feature) : ¬ Determines [f] := by
  intro h
  obtain ⟨hm, hv, hn⟩ := witness_sound f
  apply hn
  exact h (witness f).1 (witness f).2 hm (by
    intro g hg
    have he : g = f := by simpa using hg
    subst g
    exact hv)

theorem no_zero_features : ¬ Determines [] := by
  intro h
  have hw := witness_sound Feature.xx
  exact hw.2.2 (h (witness .xx).1 (witness .xx).2 hw.1 (by simp))

theorem minimum_two :
    Determines [.xy, .difference] ∧
    ¬ Determines [] ∧
    (∀ f : Feature, ¬ Determines [f]) :=
  ⟨two_features_suffice, no_zero_features, no_single_feature⟩

#print axioms minimum_two
end CrossDomainResidual.Minimum
