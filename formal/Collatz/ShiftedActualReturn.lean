import Collatz.CoherentEpisodeStream

namespace CollatzFinal
namespace SourceProduct

/-- Shifting the episode stream to an arbitrary already-reached episode
does not change any future episode. This uses the single deterministic
successor, not a patched family of independent finite trajectories. -/
theorem episode_stream_shift (a : ValidEpisode) (i j : Nat) :
    episodeStream a (i + j) =
      episodeStream (episodeStream a i) j := by
  induction j with
  | zero =>
      simp [episodeStream]
  | succ j ih =>
      change episodeStep (episodeStream a (i + j)) =
        episodeStep (episodeStream (episodeStream a i) j)
      rw [ih]

/-- The cumulative shortcut clock composes exactly across arbitrary
episode boundaries, preserving the original source's time coordinate. -/
theorem episode_stream_time_shift (a : ValidEpisode) (i j : Nat) :
    episodeStreamTime a (i + j) =
      episodeStreamTime a i +
        episodeStreamTime (episodeStream a i) j := by
  induction j with
  | zero =>
      simp [episodeStreamTime]
  | succ j ih =>
      change
        episodeStreamTime a (i + j) +
            (episodeStream a (i + j)).anchor +
            episodeStepEven (episodeStream a (i + j)) =
          episodeStreamTime a i +
            (episodeStreamTime (episodeStream a i) j +
              (episodeStream (episodeStream a i) j).anchor +
              episodeStepEven (episodeStream (episodeStream a i) j))
      rw [ih, episode_stream_shift a i j]
      omega

/-- A repeated anchor at *any* positive offset earns a genuine admitted
return for the intermediate source, with an exact shortcut trace starting
at the original source after i complete episodes. The extra prefix clock
is transported, not ignored. -/
theorem any_repeated_anchor_has_actual_admitted_return
    (a : ValidEpisode) (i k : Nat)
    (hk : 0 < k)
    (hsame :
      (episodeStream a (i + k)).anchor =
        (episodeStream a i).anchor) :
    ∃ A B P q D : Nat,
      A = 3 ^ q ∧ P = 2 ^ D ∧
      (returnDefect (A : Int) (B : Int) ((2 : Int) ^ D)
        ((episodeStream a i).owner : Int) = 0 ∨
        ReturnCylinderAdmissible
          (A : Int) (B : Int) D
          ((episodeStream a i).owner : Int)) ∧
      P * (episodeStream a (i + k)).owner =
        A * (episodeStream a i).owner + B ∧
      iter shortcut (episodeStreamTime (episodeStream a i) k)
        (iter shortcut (episodeStreamTime a i)
          (2 ^ a.anchor * a.owner - 1)) =
        2 ^ (episodeStream a (i + k)).anchor *
            (episodeStream a (i + k)).owner - 1 ∧
      episodeStreamTime a (i + k) =
        episodeStreamTime a i +
          episodeStreamTime (episodeStream a i) k := by
  let start := episodeStream a i
  have hreturn :
      (episodeStream start k).anchor = start.anchor := by
    change (episodeStream (episodeStream a i) k).anchor =
      (episodeStream a i).anchor
    rw [← episode_stream_shift a i k]
    exact hsame
  obtain ⟨A, B, P, q, D, hA, hP, hclass, hAff, hTrace⟩ :=
    episode_stream_return_admitted start k hk hreturn
  refine ⟨A, B, P, q, D, hA, hP, hclass, ?_, ?_, ?_⟩
  · simpa only [episode_stream_shift] using hAff
  · have hPrefix := episode_stream_matches_actual_shortcut a i
    rw [hPrefix]
    simpa only [episode_stream_shift] using hTrace
  · exact episode_stream_time_shift a i k

/-- The genuine remaining infinite-stream split. An arbitrary coherent
Collatz episode stream either contains a source-admitted actual return
at some pair of episode indices, or all distinct episode indices have
different anchors.

This case split proves neither that the first branch is progressive nor
that the second branch is impossible; it defines the *two exact* open
residuals without assuming either away. -/
theorem coherent_stream_admitted_return_or_fresh_anchors
    (a : ValidEpisode) :
    (∃ i k, 0 < k ∧
      (episodeStream a (i + k)).anchor = (episodeStream a i).anchor ∧
      ∃ A B P q D : Nat,
        A = 3 ^ q ∧ P = 2 ^ D ∧
        (returnDefect (A : Int) (B : Int) ((2 : Int) ^ D)
          ((episodeStream a i).owner : Int) = 0 ∨
          ReturnCylinderAdmissible
            (A : Int) (B : Int) D
            ((episodeStream a i).owner : Int)) ∧
        P * (episodeStream a (i + k)).owner =
          A * (episodeStream a i).owner + B) ∨
    (∀ i k, 0 < k →
      (episodeStream a (i + k)).anchor ≠
        (episodeStream a i).anchor) := by
  by_cases hrepeat : ∃ i k, 0 < k ∧
      (episodeStream a (i + k)).anchor = (episodeStream a i).anchor
  · obtain ⟨i, k, hk, hsame⟩ := hrepeat
    obtain ⟨A, B, P, q, D, hA, hP, hclass, hAff, _, _⟩ :=
      any_repeated_anchor_has_actual_admitted_return a i k hk hsame
    exact Or.inl ⟨i, k, hk, hsame,
      A, B, P, q, D, hA, hP, hclass, hAff⟩
  · right
    intro i k hk hsame
    exact hrepeat ⟨i, k, hk, hsame⟩

#print axioms episode_stream_shift
#print axioms episode_stream_time_shift
#print axioms any_repeated_anchor_has_actual_admitted_return
#print axioms coherent_stream_admitted_return_or_fresh_anchors

end SourceProduct
end CollatzFinal
