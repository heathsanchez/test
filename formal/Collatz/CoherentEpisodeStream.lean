import Collatz.ActualEpisodeHorizon

namespace CollatzFinal
namespace SourceProduct

/-- The smallest state of the actual episode iterator. Positivity and
owner parity are protected by construction, not rediscovered by a search. -/
structure ValidEpisode where
  anchor : Nat
  owner : Nat
  anchor_pos : 0 < anchor
  owner_pos : 0 < owner
  owner_odd : owner % 2 = 1

/-- A certified successor stores the actual even-strip count and the next
valid anchor/owner pair. -/
def ActualEpisodeMove
    (a : ValidEpisode) (p : Nat × ValidEpisode) : Prop :=
  NaturalEpisode
    a.anchor a.owner p.1 p.2.anchor p.2.owner

/-- Every valid episode has a certified next move. This chooses the unique
arithmetic successor warranted by V91/V92; no finite corpus is involved. -/
noncomputable def certifiedEpisodeSuccessor (a : ValidEpisode) :
    {p : Nat × ValidEpisode // ActualEpisodeMove a p} :=
  Classical.choice (by
    obtain ⟨s, r', m', he⟩ :=
      naturalEpisode_exists a.anchor_pos a.owner_pos a.owner_odd
    rcases he with
      ⟨hr, hm, hodd, hs, hr', hm', hodd',
        y, hy, hyodd, hmid, hend⟩
    refine ⟨(s,
      ⟨r', m', hr', hm', hodd'⟩), ?_⟩
    exact ⟨hr, hm, hodd, hs, hr', hm', hodd',
      y, hy, hyodd, hmid, hend⟩)

/-- The number of shortcut steps in the next genuine episode's even strip. -/
noncomputable def episodeStepEven (a : ValidEpisode) : Nat :=
  (certifiedEpisodeSuccessor a).val.1

/-- The next actual positive odd anchor/owner state. -/
noncomputable def episodeStep (a : ValidEpisode) : ValidEpisode :=
  (certifiedEpisodeSuccessor a).val.2

theorem episodeStep_correct (a : ValidEpisode) :
    NaturalEpisode a.anchor a.owner (episodeStepEven a)
      (episodeStep a).anchor (episodeStep a).owner :=
  (certifiedEpisodeSuccessor a).property

/-- One fixed coherent trajectory for every finite episode index. -/
noncomputable def episodeStream (a : ValidEpisode) : Nat → ValidEpisode
  | 0 => a
  | k + 1 => episodeStep (episodeStream a k)

/-- Cumulative exact shortcut time of that same coherent trajectory. -/
noncomputable def episodeStreamTime (a : ValidEpisode) : Nat → Nat
  | 0 => 0
  | k + 1 =>
      episodeStreamTime a k + (episodeStream a k).anchor +
        episodeStepEven (episodeStream a k)

/-- Every next actual episode consumes strictly positive shortcut time. -/
theorem episode_stream_time_increases
    (a : ValidEpisode) (k : Nat) :
    episodeStreamTime a k < episodeStreamTime a (k + 1) := by
  have hr := (episodeStream a k).anchor_pos
  simp only [episodeStreamTime]
  omega

/-- After k complete actual episodes, shortcut time is at least k.
This is a causal clock bound, not a well-founded Collatz rank. -/
theorem episode_stream_time_at_least_count
    (a : ValidEpisode) (k : Nat) :
    k ≤ episodeStreamTime a k := by
  induction k with
  | zero =>
      simp [episodeStreamTime]
  | succ k ih =>
      have hr := (episodeStream a k).anchor_pos
      simp only [episodeStreamTime]
      omega

/-- The coherent episode stream is literally the shortcut trajectory of
the initial anchored natural source, at every accumulated shortcut time.
It cannot stitch together unrelated trajectory witnesses. -/
theorem episode_stream_matches_actual_shortcut
    (a : ValidEpisode) (k : Nat) :
    iter shortcut (episodeStreamTime a k)
        (2 ^ a.anchor * a.owner - 1) =
      2 ^ (episodeStream a k).anchor *
          (episodeStream a k).owner - 1 := by
  induction k with
  | zero =>
      simp [episodeStreamTime, episodeStream, iter]
  | succ k ih =>
      have hstep :=
        naturalEpisode_actual (episodeStep_correct (episodeStream a k))
      calc
        iter shortcut (episodeStreamTime a (k + 1))
            (2 ^ a.anchor * a.owner - 1)
            = iter shortcut
                ((episodeStream a k).anchor +
                  episodeStepEven (episodeStream a k))
                (iter shortcut (episodeStreamTime a k)
                  (2 ^ a.anchor * a.owner - 1)) := by
                    rw [show episodeStreamTime a (k + 1) =
                      episodeStreamTime a k +
                        ((episodeStream a k).anchor +
                          episodeStepEven (episodeStream a k)) by
                            simp [episodeStreamTime, Nat.add_assoc]]
                    rw [iter_add]
        _ = iter shortcut
              ((episodeStream a k).anchor +
                episodeStepEven (episodeStream a k))
              (2 ^ (episodeStream a k).anchor *
                (episodeStream a k).owner - 1) := by rw [ih]
        _ = 2 ^ (episodeStream a (k + 1)).anchor *
              (episodeStream a (k + 1)).owner - 1 := by
                simpa [episodeStream] using hstep

/-- Every prefix of this *single* coherent stream is an exact V97
finite episode word, with a composed affine certificate. -/
theorem episode_stream_compiles_chain
    (a : ValidEpisode) (k : Nat) :
    ∃ A B P : Nat,
      ActualEpisodeChain
        a.anchor a.owner
        (episodeStream a k).anchor (episodeStream a k).owner
        (episodeStreamTime a k) A B P := by
  induction k with
  | zero =>
      exact ⟨1, 0, 1, ActualEpisodeChain.empty a.anchor a.owner⟩
  | succ k ih =>
      obtain ⟨A, B, P, hc⟩ := ih
      let cur := episodeStream a k
      let s := episodeStepEven cur
      let nxt := episodeStep cur
      refine ⟨3 ^ cur.anchor * A,
        3 ^ cur.anchor * B + (2 ^ s - 1) * P,
        2 ^ (s + nxt.anchor) * P, ?_⟩
      exact ActualEpisodeChain.append hc (episodeStep_correct cur)

/-- A later occurrence of the same anchor in this coherent stream
produces V98's exact source-admitted return cylinder (or a zero defect),
rather than an arbitrary algebraically patched certificate. -/
theorem episode_stream_return_admitted
    (a : ValidEpisode) (k : Nat)
    (hk : 0 < k)
    (hsame : (episodeStream a k).anchor = a.anchor) :
    ∃ A B P q D : Nat,
      A = 3 ^ q ∧ P = 2 ^ D ∧
      (returnDefect (A : Int) (B : Int)
        ((2 : Int) ^ D) (a.owner : Int) = 0 ∨
        ReturnCylinderAdmissible
          (A : Int) (B : Int) D (a.owner : Int)) ∧
      P * (episodeStream a k).owner = A * a.owner + B ∧
      iter shortcut (episodeStreamTime a k)
        (2 ^ a.anchor * a.owner - 1) =
          2 ^ a.anchor * (episodeStream a k).owner - 1 := by
  obtain ⟨A, B, P, hc⟩ := episode_stream_compiles_chain a k
  have ht : 0 < episodeStreamTime a k := by
    have hcount := episode_stream_time_at_least_count a k
    omega
  obtain ⟨q, D, hA, hP, hclass, hAff, hshortcut⟩ :=
    repeated_initial_anchor_yields_admitted_return hc
      a.anchor_pos a.owner_pos a.owner_odd ht hsame
  exact ⟨A, B, P, q, D, hA, hP, hclass, hAff, hshortcut⟩

#print axioms episodeStep_correct
#print axioms episode_stream_time_at_least_count
#print axioms episode_stream_matches_actual_shortcut
#print axioms episode_stream_compiles_chain
#print axioms episode_stream_return_admitted

end SourceProduct
end CollatzFinal
