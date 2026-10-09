import Collatz.AnchorReturnDichotomy
import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-- Every positive odd natural source is exactly the natural-number value
of a valid positive odd episode anchor/owner pair.

The episode anchor is the dyadic order of x+1; it is positive because x
is odd and x+1 is even. -/
theorem positive_odd_has_valid_episode
    (x : Nat) (hx : 0 < x) (hodd : x % 2 = 1) :
    ∃ a : ValidEpisode,
      x = 2 ^ a.anchor * a.owner - 1 := by
  obtain ⟨r, m, hpow, hmOdd⟩ :=
    nat_dyadic_decomposition (x + 1) (by omega)
  have hmPos : 0 < m := by
    have hmNe : m ≠ 0 := by
      intro hmZero
      have hbad : x + 1 = 0 := by
        simpa [hmZero] using hpow
      omega
    exact Nat.pos_of_ne_zero hmNe
  have hrPos : 0 < r := by
    cases r with
    | zero =>
        have hsum : x + 1 = m := by
          simpa using hpow
        omega
    | succ r =>
        omega
  refine ⟨⟨r, m, hrPos, hmPos, hmOdd⟩, ?_⟩
  omega

/-- Every positive natural n reaches a positive odd episode start after
finitely many shortcut steps. The skipped steps are exactly its initial
power-of-two stripping; this is a source-preserving actual trace. -/
theorem positive_source_reaches_valid_episode
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n =
        2 ^ a.anchor * a.owner - 1 := by
  obtain ⟨k, m, hpow, hmOdd⟩ :=
    nat_dyadic_decomposition n hn
  have hmPos : 0 < m := by
    have hmn : m ≠ 0 := by
      intro hzero
      have hbad : n = 0 := by
        simpa [hzero] using hpow
      omega
    exact Nat.pos_of_ne_zero hmn
  obtain ⟨a, hform⟩ :=
    positive_odd_has_valid_episode m hmPos hmOdd
  refine ⟨k, a, ?_⟩
  rw [hpow]
  rw [iter_pow_two_mul]
  exact hform

/-- Every coherent future episode is a genuine shortcut iterate of the
*same original positive natural source*, not an unconstrained successor
of a separate odd-number generator. -/
theorem positive_source_has_coherent_episode_stream
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n =
        2 ^ a.anchor * a.owner - 1 ∧
      ∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) n =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1 := by
  obtain ⟨k, a, hstart⟩ :=
    positive_source_reaches_valid_episode n hn
  refine ⟨k, a, hstart, ?_⟩
  intro j
  rw [iter_add, hstart]
  exact episode_stream_matches_actual_shortcut a j

/-- The V101 result now applies from *every positive natural source*:
after an exact finite initial prefix, the actual continuation either
contains a certified positive-time same-anchor return at some reached
episode state or has unbounded episode anchor labels.

Neither alternative is claimed to terminate the orbit. -/
theorem positive_source_admitted_return_or_unbounded_anchors
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n =
        2 ^ a.anchor * a.owner - 1 ∧
      (∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) n =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1) ∧
      ((∃ i : Nat,
          StreamAdmittedReturn (episodeStream a i)) ∨
        (∀ B : Nat, ∃ j : Nat,
          B < (episodeStream a j).anchor)) := by
  obtain ⟨k, a, hstart, htrace⟩ :=
    positive_source_has_coherent_episode_stream n hn
  exact ⟨k, a, hstart, htrace,
    admitted_return_or_unbounded_anchors a⟩

/-- The same dichotomy is source-admitted on any arbitrary ZeroTailLive
SourceProduct state. It uses only the already-proved positive-shortcut
property and V101's coherent actual episode semantics. -/
theorem zero_tail_live_admitted_return_or_unbounded_anchors
    {s : State} (hs : ZeroTailLive s) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k (endpoint s) =
        2 ^ a.anchor * a.owner - 1 ∧
      (∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) (endpoint s) =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1) ∧
      ((∃ i : Nat,
          StreamAdmittedReturn (episodeStream a i)) ∨
        (∀ B : Nat, ∃ j : Nat,
          B < (episodeStream a j).anchor)) := by
  obtain ⟨n, d, hn, hstate⟩ := hs.1.1
  have hpos : 0 < endpoint s := by
    rw [hstate]
    simpa only [at_endpoint] using
      iter_positive shortcut shortcut_positive d n hn
  exact positive_source_admitted_return_or_unbounded_anchors
    (endpoint s) hpos

#print axioms positive_odd_has_valid_episode
#print axioms positive_source_reaches_valid_episode
#print axioms positive_source_has_coherent_episode_stream
#print axioms positive_source_admitted_return_or_unbounded_anchors
#print axioms zero_tail_live_admitted_return_or_unbounded_anchors

end SourceProduct
end CollatzFinal
