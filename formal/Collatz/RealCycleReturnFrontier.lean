import Collatz.FreshAnchorBoundary

namespace CollatzFinal
namespace SourceProduct

/-- A source-admitted return between any two occurrences of the same
episode anchor is either an actual positive-time shortcut period at
the first occurrence, or a nonzero return admitted by the exact V88/V96
cylinder. A fixed point of a *symbolic* law is not enough for the
periodic branch: the V101 real-orbit trace is consumed here. -/
theorem repeated_anchor_real_cycle_or_admitted_nonzero_return
    (a : ValidEpisode) (i k : Nat)
    (hk : 0 < k)
    (hsame :
      (episodeStream a (i + k)).anchor =
        (episodeStream a i).anchor) :
    (∃ t, 0 < t ∧
      iter shortcut t
        (iter shortcut (episodeStreamTime a i)
          (2 ^ a.anchor * a.owner - 1)) =
      iter shortcut (episodeStreamTime a i)
        (2 ^ a.anchor * a.owner - 1)) ∨
    (∃ A B P q D : Nat,
      A = 3 ^ q ∧ P = 2 ^ D ∧
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D
          ((episodeStream a i).owner : Int) ∧
      P * (episodeStream a (i + k)).owner =
        A * (episodeStream a i).owner + B ∧
      iter shortcut (episodeStreamTime (episodeStream a i) k)
        (iter shortcut (episodeStreamTime a i)
          (2 ^ a.anchor * a.owner - 1)) =
        2 ^ (episodeStream a (i + k)).anchor *
            (episodeStream a (i + k)).owner - 1) := by
  obtain ⟨A, B, P, q, D, hA, hP, hclass, hAff, hTrace, hTime⟩ :=
    any_repeated_anchor_has_actual_admitted_return a i k hk hsame
  rcases hclass with hzero | hadm
  · have hCast :=
      congrArg (fun z : Nat => (z : Int)) hAff
    have hEqInt :
        (2 : Int) ^ D * ((episodeStream a (i + k)).owner : Int) =
          (A : Int) * ((episodeStream a i).owner : Int) + (B : Int) := by
      simpa [hP] using hCast
    have hEqOwner :
        ((episodeStream a (i + k)).owner : Int) =
          ((episodeStream a i).owner : Int) :=
      return_zero_defect_fixed_point
        (A : Int) (B : Int) ((2 : Int) ^ D)
        ((episodeStream a i).owner : Int)
        ((episodeStream a (i + k)).owner : Int)
        (Int.pow_ne_zero (by decide)) hEqInt hzero
    have hNatOwner :
        (episodeStream a (i + k)).owner =
          (episodeStream a i).owner :=
      Int.ofNat_inj.mp hEqOwner
    have hEqEndpoint :
        2 ^ (episodeStream a (i + k)).anchor *
            (episodeStream a (i + k)).owner - 1 =
          2 ^ (episodeStream a i).anchor *
            (episodeStream a i).owner - 1 := by
      rw [hsame, hNatOwner]
    have hClockPositive :
        0 < episodeStreamTime (episodeStream a i) k := by
      have ht := episode_stream_time_at_least_count
        (episodeStream a i) k
      omega
    refine Or.inl ⟨episodeStreamTime (episodeStream a i) k,
      hClockPositive, ?_⟩
    calc
      iter shortcut (episodeStreamTime (episodeStream a i) k)
          (iter shortcut (episodeStreamTime a i)
            (2 ^ a.anchor * a.owner - 1)) =
        2 ^ (episodeStream a (i + k)).anchor *
            (episodeStream a (i + k)).owner - 1 := hTrace
      _ = 2 ^ (episodeStream a i).anchor *
            (episodeStream a i).owner - 1 := hEqEndpoint
      _ = iter shortcut (episodeStreamTime a i)
            (2 ^ a.anchor * a.owner - 1) :=
        (episode_stream_matches_actual_shortcut a i).symm
  · exact Or.inr ⟨A, B, P, q, D, hA, hP, hadm, hAff, hTrace⟩

/-- The fully source-coupled three-way boundary for every coherent
positive odd episode stream.

The cases are:
(1) a genuinely periodic positive-time shortcut endpoint;
(2) a nonzero, source-admitted actual affine return requiring
    future progress or a different owner/centre refinement;
(3) arbitrarily high fresh episode anchors.

These cases are not claimed disjoint or impossible. In particular
the legitimate 1↔2 shortcut cycle belongs to case (1). -/
theorem coherent_stream_cycle_or_nonzero_return_or_unbounded_anchor
    (a : ValidEpisode) :
    (∃ i k t, 0 < k ∧ 0 < t ∧
      iter shortcut t
        (iter shortcut (episodeStreamTime a i)
          (2 ^ a.anchor * a.owner - 1)) =
      iter shortcut (episodeStreamTime a i)
        (2 ^ a.anchor * a.owner - 1)) ∨
    (∃ i k A B P q D : Nat,
      0 < k ∧
      (episodeStream a (i + k)).anchor =
        (episodeStream a i).anchor ∧
      A = 3 ^ q ∧ P = 2 ^ D ∧
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D
          ((episodeStream a i).owner : Int) ∧
      P * (episodeStream a (i + k)).owner =
        A * (episodeStream a i).owner + B) ∨
    (∀ B, ∃ n,
      B < (episodeStream a n).anchor ∧
      2 ^ B ∣
        (iter shortcut (episodeStreamTime a n)
          (2 ^ a.anchor * a.owner - 1) + 1)) := by
  rcases actual_stream_admitted_return_or_unbounded_anchor a with
      hreturn | hfresh
  · obtain ⟨i, k, hk, hsame, A, B, P, q, D,
      hA, hP, hclass, hAff⟩ := hreturn
    rcases repeated_anchor_real_cycle_or_admitted_nonzero_return
      a i k hk hsame with hperiod | hadm
    · obtain ⟨t, ht, hfixed⟩ := hperiod
      exact Or.inl ⟨i, k, t, hk, ht, hfixed⟩
    · obtain ⟨A', B', P', q', D', hA', hP',
        hadm', hAff', htrace⟩ := hadm
      exact Or.inr (Or.inl ⟨i, k, A', B', P', q', D',
        hk, hsame, hA', hP', hadm', hAff'⟩)
  · exact Or.inr (Or.inr hfresh)

#print axioms repeated_anchor_real_cycle_or_admitted_nonzero_return
#print axioms coherent_stream_cycle_or_nonzero_return_or_unbounded_anchor

end SourceProduct
end CollatzFinal
