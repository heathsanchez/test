import Collatz.ShiftedActualReturn

namespace CollatzFinal
namespace SourceProduct

/-- Elementary infinite pigeonhole principle, proved without a finite
sampling bound, an imported probability assumption, or an external solver:
any Nat-valued infinite sequence confined to {0,...,B} repeats a value.

Proof by induction on B, removing f(0) from the available alphabet for
all later indices when no later index repeats it. -/
theorem bounded_nat_sequence_repeats :
    ∀ (B : Nat) (f : Nat → Nat),
      (∀ i, f i ≤ B) →
      ∃ i j, i < j ∧ f i = f j := by
  intro B
  induction B with
  | zero =>
      intro f hf
      refine ⟨0, 1, by decide, ?_⟩
      have h0 := hf 0
      have h1 := hf 1
      omega
  | succ B ih =>
      intro f hf
      by_cases hrepeat : ∃ j, 0 < j ∧ f j = f 0
      · obtain ⟨j, hj, heq⟩ := hrepeat
        exact ⟨0, j, hj, heq.symm⟩
      · let v := f 0
        let g : Nat → Nat := fun i =>
          if f (i + 1) < v then f (i + 1) else f (i + 1) - 1
        have hnotv (i : Nat) : f (i + 1) ≠ v := by
          intro hv
          exact hrepeat ⟨i + 1, by omega, hv⟩
        have hgbound : ∀ i, g i ≤ B := by
          intro i
          dsimp [g]
          by_cases hlt : f (i + 1) < v
          · simp only [if_pos hlt]
            have h0 := hf 0
            have hi := hf (i + 1)
            dsimp [v] at hlt
            omega
          · simp only [if_neg hlt]
            have hi := hf (i + 1)
            have hne := hnotv i
            omega
        obtain ⟨i, j, hij, hgeq⟩ := ih g hgbound
        have hfeq : f (i + 1) = f (j + 1) := by
          dsimp [g] at hgeq
          by_cases hi : f (i + 1) < v
          · by_cases hj : f (j + 1) < v
            · simpa only [if_pos hi, if_pos hj] using hgeq
            · simp only [if_pos hi, if_neg hj] at hgeq
              have hne := hnotv j
              omega
          · by_cases hj : f (j + 1) < v
            · simp only [if_neg hi, if_pos hj] at hgeq
              have hne := hnotv i
              omega
            · simp only [if_neg hi, if_neg hj] at hgeq
              have hnei := hnotv i
              have hnej := hnotv j
              omega
        exact ⟨i + 1, j + 1, by omega, hfeq⟩

/-- The coherent actual episode stream cannot stay inside a fixed anchor
bound while every distinct episode index has a different anchor. Thus
an all-fresh episode stream necessarily visits arbitrarily high anchors. -/
theorem fresh_episode_anchors_unbounded
    (a : ValidEpisode)
    (hfresh : ∀ i k, 0 < k →
      (episodeStream a (i + k)).anchor ≠
        (episodeStream a i).anchor) :
    ∀ B, ∃ n, B < (episodeStream a n).anchor := by
  intro B
  by_contra hnone
  have hbound : ∀ n, (episodeStream a n).anchor ≤ B := by
    intro n
    by_contra hn
    exact hnone ⟨n, by omega⟩
  obtain ⟨i, j, hij, heq⟩ :=
    bounded_nat_sequence_repeats B
      (fun k => (episodeStream a k).anchor) hbound
  have hk : 0 < j - i := by omega
  have hsum : i + (j - i) = j := by omega
  have hsame :
      (episodeStream a (i + (j - i))).anchor =
        (episodeStream a i).anchor := by
    rw [hsum]
    exact heq.symm
  exact hfresh i (j - i) hk hsame

/-- Visiting a high anchor means an actual endpoint is divisible by
the corresponding dyadic modulus *after adding one*. This is a
precise 2-adic proximity statement about the current endpoint, and
not by itself a contradiction for a fixed natural starting source. -/
theorem actual_endpoint_dyadic_of_high_anchor
    (a : ValidEpisode) (n B : Nat)
    (hB : B ≤ (episodeStream a n).anchor) :
    2 ^ B ∣
      (iter shortcut (episodeStreamTime a n)
          (2 ^ a.anchor * a.owner - 1) + 1) := by
  rw [episode_stream_matches_actual_shortcut a n]
  let e := episodeStream a n
  have hprod : 0 < 2 ^ e.anchor * e.owner :=
    Nat.mul_pos (Nat.pow_pos (by decide)) e.owner_pos
  have hplus : 2 ^ e.anchor * e.owner - 1 + 1 =
      2 ^ e.anchor * e.owner := by
    omega
  rw [hplus]
  refine ⟨2 ^ (e.anchor - B) * e.owner, ?_⟩
  have hsum : e.anchor = B + (e.anchor - B) := by
    change B ≤ e.anchor at hB
    omega
  calc
    2 ^ e.anchor * e.owner =
        2 ^ (B + (e.anchor - B)) * e.owner := by rw [← hsum]
    _ = 2 ^ B * (2 ^ (e.anchor - B) * e.owner) := by
      simp [Nat.pow_add, Nat.mul_assoc]

/-- An unconditional, source-coupled boundary for one exact episode
stream: either a repeated anchor earns a genuine V98/V101 admitted
return somewhere on the actual orbit, or arbitrarily high dyadic
endpoint-nearness to -1 occurs.

The second alternative is not eliminated; nor does an admitted return
alone force descent. Those are the live Collatz residuals. -/
theorem actual_stream_admitted_return_or_unbounded_anchor
    (a : ValidEpisode) :
    (∃ i k, 0 < k ∧
      (episodeStream a (i + k)).anchor =
        (episodeStream a i).anchor ∧
      ∃ A B P q D : Nat,
        A = 3 ^ q ∧ P = 2 ^ D ∧
        (returnDefect (A : Int) (B : Int) ((2 : Int) ^ D)
          ((episodeStream a i).owner : Int) = 0 ∨
          ReturnCylinderAdmissible (A : Int) (B : Int) D
            ((episodeStream a i).owner : Int)) ∧
        P * (episodeStream a (i + k)).owner =
          A * (episodeStream a i).owner + B) ∨
    (∀ B, ∃ n,
      B < (episodeStream a n).anchor ∧
      2 ^ B ∣
        (iter shortcut (episodeStreamTime a n)
          (2 ^ a.anchor * a.owner - 1) + 1)) := by
  rcases coherent_stream_admitted_return_or_fresh_anchors a with
    hreturn | hfresh
  · exact Or.inl hreturn
  · right
    intro B
    obtain ⟨n, hn⟩ := fresh_episode_anchors_unbounded a hfresh B
    exact ⟨n, hn,
      actual_endpoint_dyadic_of_high_anchor a n B (by omega)⟩

#print axioms bounded_nat_sequence_repeats
#print axioms fresh_episode_anchors_unbounded
#print axioms actual_endpoint_dyadic_of_high_anchor
#print axioms actual_stream_admitted_return_or_unbounded_anchor

end SourceProduct
end CollatzFinal
