import Collatz.EpisodeBridge

namespace CollatzFinal
namespace SourceProduct

/-- Source-relative precision at an episode start. -/
def episodeSourcePrecision (H r : Nat) : Nat := H + r

/-- Each genuine episode strictly increases the certified dyadic precision
of the original source, independently of the next anchor's magnitude. -/
theorem actual_episode_precision_gain
    {r m s r' m' H : Nat}
    (he : NaturalEpisode r m s r' m') :
    episodeSourcePrecision H r <
      episodeSourcePrecision (H + r + s) r' := by
  rcases he with
    ⟨hr, hm, hodd, hs, hr', hm', hm'odd, y,
      hy, hyodd, hmid, hend⟩
  unfold episodeSourcePrecision
  omega

/-- Every positive odd anchor-owner pair has a real next episode with
strictly increased global dyadic source precision. -/
theorem actual_next_episode_precision_gain
    {r m H : Nat}
    (hr : 0 < r) (hm : 0 < m) (hodd : m % 2 = 1) :
    ∃ s r' m' : Nat,
      NaturalEpisode r m s r' m' ∧
      episodeSourcePrecision H r <
        episodeSourcePrecision (H + r + s) r' := by
  obtain ⟨s, r', m', he, hactual⟩ :=
    actual_next_episode_exists hr hm hodd
  exact ⟨s, r', m', he, actual_episode_precision_gain he⟩

#print axioms actual_episode_precision_gain
#print axioms actual_next_episode_precision_gain

end SourceProduct
end CollatzFinal
