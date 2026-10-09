import Collatz.EpisodePrecisionGain

namespace CollatzFinal
namespace SourceProduct

/-- Strip the globally elapsed shortcut depth from V93's episode precision.
This is the minimal normalization needed to avoid counting progress merely
because time has advanced. -/
def episodeExcessPrecision (H r : Nat) : Nat :=
  episodeSourcePrecision H r - H

/-- The normalized precision is exactly the current episode anchor. -/
theorem episode_excess_eq_anchor (H r : Nat) :
    episodeExcessPrecision H r = r := by
  simp [episodeExcessPrecision, episodeSourcePrecision]

/-- V93's absolute precision increase is *exactly* the elapsed
episode length plus the next anchor, independent of the original anchor. -/
theorem episode_total_precision_growth (H r s r' : Nat) :
    episodeSourcePrecision (H + r + s) r' =
      episodeSourcePrecision H r + s + r' := by
  unfold episodeSourcePrecision
  omega

/-- Concrete actual shortcut episode:
7 = 2^3 * 1 - 1 ->(three odd steps + one even step) 13
  = 2^1 * 7 - 1.
Its anchor falls from 3 to 1. -/
theorem seven_to_thirteen_natural_episode :
    NaturalEpisode 3 1 1 1 7 := by
  unfold NaturalEpisode
  refine ⟨by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, 13,
    by decide, by decide, by decide, by decide⟩

/-- The certificate is attached to the actual shortcut orbit, not a
synthetic affine transition. -/
theorem seven_to_thirteen_actual :
    iter shortcut 4 7 = 13 := by
  decide

/-- Unnormalized V93 source precision rises on this very episode. -/
theorem seven_episode_total_precision_grows (H : Nat) :
    episodeSourcePrecision H 3 <
      episodeSourcePrecision (H + 3 + 1) 1 :=
  actual_episode_precision_gain
    (H := H) seven_to_thirteen_natural_episode

/-- Removing automatic global-depth growth reverses the inequality:
the meaningful episode-anchor component strictly *decreases*. -/
theorem seven_episode_excess_precision_drops (H : Nat) :
    episodeExcessPrecision (H + 3 + 1) 1 <
      episodeExcessPrecision H 3 := by
  rw [episode_excess_eq_anchor, episode_excess_eq_anchor]
  decide

/-- A universal claim of monotone normalized episode-anchor precision
is refuted by a kernel-checked actual orbit. -/
theorem episode_excess_monotonicity_false :
    ¬ (∀ r m s r' m' H : Nat,
       NaturalEpisode r m s r' m' →
       episodeExcessPrecision H r <
         episodeExcessPrecision (H + r + s) r') := by
  intro hall
  have hbad := hall 3 1 1 1 7 0 seven_to_thirteen_natural_episode
  have hdrop := seven_episode_excess_precision_drops 0
  omega

#print axioms episode_excess_eq_anchor
#print axioms episode_total_precision_growth
#print axioms seven_to_thirteen_natural_episode
#print axioms seven_to_thirteen_actual
#print axioms seven_episode_total_precision_grows
#print axioms seven_episode_excess_precision_drops
#print axioms episode_excess_monotonicity_false

end SourceProduct
end CollatzFinal
