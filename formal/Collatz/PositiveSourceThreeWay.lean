import Collatz.RealCycleReturnFrontier
import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-- Port the independently qualified positive-source normalization from
collatz-v101-positive-source-episode-v102@2b3507bf, without importing that
branch's competing episode-stream shift declarations. -/
theorem positive_odd_to_episode_v104
    (x : Nat) (hx : 0 < x) (hodd : x % 2 = 1) :
    ∃ a : ValidEpisode, x = 2 ^ a.anchor * a.owner - 1 := by
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
    | succ r => omega
  refine ⟨⟨r, m, hrPos, hmPos, hmOdd⟩, ?_⟩
  change x = 2 ^ r * m - 1
  omega

/-- Preserve the original natural source through exact initial powers-of-two
stripping. This construction works for every positive natural, odd or even. -/
theorem positive_source_to_episode_v104
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n = 2 ^ a.anchor * a.owner - 1 := by
  obtain ⟨k, m, hpow, hmOdd⟩ :=
    nat_dyadic_decomposition n hn
  have hmPos : 0 < m := by
    have hmNe : m ≠ 0 := by
      intro hmZero
      have hbad : n = 0 := by
        simpa [hmZero] using hpow
      omega
    exact Nat.pos_of_ne_zero hmNe
  obtain ⟨a, hform⟩ := positive_odd_to_episode_v104 m hmPos hmOdd
  refine ⟨k, a, ?_⟩
  rw [hpow]
  rw [iter_pow_two_mul]
  exact hform

/-- Every episode index on the chosen continuation is a genuine shortcut
iterate of the SAME original positive natural source. -/
theorem positive_source_coherent_trace_v104
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n = 2 ^ a.anchor * a.owner - 1 ∧
      ∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) n =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1 := by
  obtain ⟨k, a, hstart⟩ :=
    positive_source_to_episode_v104 n hn
  refine ⟨k, a, hstart, ?_⟩
  intro j
  rw [iter_add, hstart]
  exact episode_stream_matches_actual_shortcut a j

/-- V103's actual three-way theorem now applies to every original positive
natural source, with a pinned finite initial prefix and an all-depth shortcut
trace back to that source.

No promise of eventual descent, anchor recurrence or nonterminal-cycle
exclusion is smuggled into the statement. -/
theorem positive_source_real_three_way_frontier_v104
    (n : Nat) (hn : 0 < n) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k n = 2 ^ a.anchor * a.owner - 1 ∧
      (∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) n =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1) ∧
      ((∃ i d t : Nat, 0 < d ∧ 0 < t ∧
        iter shortcut t
          (iter shortcut (k + episodeStreamTime a i) n) =
        iter shortcut (k + episodeStreamTime a i) n) ∨
       (∃ i d A B P q D : Nat,
         0 < d ∧
         (episodeStream a (i + d)).anchor =
           (episodeStream a i).anchor ∧
         A = 3 ^ q ∧ P = 2 ^ D ∧
         ReturnCylinderAdmissible
           (A : Int) (B : Int) D
             ((episodeStream a i).owner : Int) ∧
         P * (episodeStream a (i + d)).owner =
           A * (episodeStream a i).owner + B) ∨
       (∀ B : Nat, ∃ j : Nat,
         B < (episodeStream a j).anchor ∧
         2 ^ B ∣
           (iter shortcut (k + episodeStreamTime a j) n + 1))) := by
  obtain ⟨k, a, hstart, htrace⟩ :=
    positive_source_coherent_trace_v104 n hn
  refine ⟨k, a, hstart, htrace, ?_⟩
  rcases coherent_stream_cycle_or_nonzero_return_or_unbounded_anchor a with
      hperiod | hmore
  · obtain ⟨i, d, t, hd, ht, hp⟩ := hperiod
    left
    refine ⟨i, d, t, hd, ht, ?_⟩
    have hi := htrace i
    rw [hi]
    rw [← episode_stream_matches_actual_shortcut a i]
    exact hp
  · rcases hmore with hreturn | hfresh
    · exact Or.inr (Or.inl hreturn)
    · right
      right
      intro B
      obtain ⟨j, hb, hdiv⟩ := hfresh B
      refine ⟨j, hb, ?_⟩
      rw [htrace j]
      rw [← episode_stream_matches_actual_shortcut a j]
      exact hdiv

/-- The source-product unresolved ZeroTailLive state inherits the three-way
actual episode frontier with the identical original endpoint and real
shortcut trace. This removes arbitrary-positive-source normalization as a
premise from the active Collatz V85 residual. -/
theorem zero_tail_live_real_three_way_frontier_v104
    {s : State} (hs : ZeroTailLive s) :
    ∃ k : Nat, ∃ a : ValidEpisode,
      iter shortcut k (endpoint s) =
        2 ^ a.anchor * a.owner - 1 ∧
      (∀ j : Nat,
        iter shortcut (k + episodeStreamTime a j) (endpoint s) =
          2 ^ (episodeStream a j).anchor *
            (episodeStream a j).owner - 1) ∧
      ((∃ i d t : Nat, 0 < d ∧ 0 < t ∧
        iter shortcut t
          (iter shortcut (k + episodeStreamTime a i) (endpoint s)) =
        iter shortcut (k + episodeStreamTime a i) (endpoint s)) ∨
       (∃ i d A B P q D : Nat,
         0 < d ∧
         (episodeStream a (i + d)).anchor =
           (episodeStream a i).anchor ∧
         A = 3 ^ q ∧ P = 2 ^ D ∧
         ReturnCylinderAdmissible
           (A : Int) (B : Int) D
             ((episodeStream a i).owner : Int) ∧
         P * (episodeStream a (i + d)).owner =
           A * (episodeStream a i).owner + B) ∨
       (∀ B : Nat, ∃ j : Nat,
         B < (episodeStream a j).anchor ∧
         2 ^ B ∣
           (iter shortcut (k + episodeStreamTime a j)
             (endpoint s) + 1))) := by
  obtain ⟨n, d, hn, hstate⟩ := hs.1.1
  have hpos : 0 < endpoint s := by
    rw [hstate]
    simpa only [at_endpoint] using
      iter_positive shortcut shortcut_positive d n hn
  exact positive_source_real_three_way_frontier_v104 (endpoint s) hpos

#print axioms positive_odd_to_episode_v104
#print axioms positive_source_to_episode_v104
#print axioms positive_source_coherent_trace_v104
#print axioms positive_source_real_three_way_frontier_v104
#print axioms zero_tail_live_real_three_way_frontier_v104

end SourceProduct
end CollatzFinal
