import Collatz.CoherentEpisodeStream

namespace CollatzFinal
namespace SourceProduct

/-- Elementary infinite pigeonhole principle for natural labels:
there is no injective infinite sequence whose values are all bounded by B.
This is proved in Lean directly by deleting the unique index whose value
is the top label; no external finite-cardinality oracle is used. -/
theorem bounded_nat_sequence_not_injective :
    ∀ B : Nat, ∀ f : Nat → Nat,
      (∀ i, f i ≤ B) → ¬ Function.Injective f := by
  intro B
  induction B with
  | zero =>
      intro f hbound hinj
      have h0 : f 0 = 0 := by
        have hb := hbound 0
        omega
      have h1 : f 1 = 0 := by
        have hb := hbound 1
        omega
      have h01 : (0 : Nat) = 1 :=
        hinj (h0.trans h1.symm)
      omega
  | succ B ih =>
      intro f hbound hinj
      by_cases htop : ∃ n, f n = B + 1
      · obtain ⟨n, hn⟩ := htop
        let shift : Nat → Nat := fun i =>
          if i < n then i else i + 1
        have hshift_ne : ∀ i, shift i ≠ n := by
          intro i
          by_cases hi : i < n
          · simp [shift, hi]
            omega
          · simp [shift, hi]
            omega
        have hshift_inj : Function.Injective shift := by
          intro i j heq
          dsimp [shift] at heq
          by_cases hi : i < n <;> by_cases hj : j < n
          <;> simp [hi, hj] at heq <;> omega
        have hnextbound : ∀ i, f (shift i) ≤ B := by
          intro i
          have hne : f (shift i) ≠ B + 1 := by
            intro heq
            have hidx : shift i = n := hinj (heq.trans hn.symm)
            exact hshift_ne i hidx
          have hle := hbound (shift i)
          omega
        have hbad :=
          ih (fun i => f (shift i)) hnextbound
        apply hbad
        intro i j hij
        exact hshift_inj (hinj hij)
      · have hsmaller : ∀ i, f i ≤ B := by
          intro i
          have hle := hbound i
          have hne : f i ≠ B + 1 := by
            intro heq
            exact htop ⟨i, heq⟩
          omega
        exact ih f hsmaller hinj

/-- A coherent actual episode stream with globally bounded anchors must
repeat an anchor at two strictly ordered episode indices. -/
theorem bounded_actual_stream_repeats_anchor
    (a : ValidEpisode) (B : Nat)
    (hbound : ∀ k, (episodeStream a k).anchor ≤ B) :
    ∃ i j : Nat, i < j ∧
      (episodeStream a i).anchor =
        (episodeStream a j).anchor := by
  classical
  apply Classical.byContradiction
  intro hnone
  let f : Nat → Nat := fun k => (episodeStream a k).anchor
  have hfinite : ∀ k, f k ≤ B := hbound
  have hinj : Function.Injective f := by
    intro i j heq
    by_cases hij : i < j
    · exact False.elim (hnone ⟨i, j, hij, heq⟩)
    · by_cases hji : j < i
      · exact False.elim (hnone ⟨j, i, hji, heq.symm⟩)
      · omega
  exact (bounded_nat_sequence_not_injective B f hfinite) hinj

/-- The unique actual episode trajectory commutes with advancing its origin:
the suffix starting at index i is itself the same canonical episode stream. -/
theorem episode_stream_shift
    (a : ValidEpisode) (i k : Nat) :
    episodeStream (episodeStream a i) k =
      episodeStream a (i + k) := by
  induction k with
  | zero =>
      simp [episodeStream]
  | succ k ih =>
      calc
        episodeStream (episodeStream a i) (k + 1) =
            episodeStep (episodeStream (episodeStream a i) k) := by
              rfl
        _ = episodeStep (episodeStream a (i + k)) := by
              rw [ih]
        _ = episodeStream a (i + (k + 1)) := by
              rw [show i + (k + 1) = (i + k) + 1 by omega]
              rfl

/-- A protected, real, positive-time episode return certificate at the
present episode state; all data come from the same executable trace. -/
def StreamAdmittedReturn (a : ValidEpisode) : Prop :=
  ∃ k A B P q D : Nat,
    0 < k ∧
    (episodeStream a k).anchor = a.anchor ∧
    A = 3 ^ q ∧ P = 2 ^ D ∧
    (returnDefect (A : Int) (B : Int)
        ((2 : Int) ^ D) (a.owner : Int) = 0 ∨
      ReturnCylinderAdmissible (A : Int) (B : Int) D (a.owner : Int)) ∧
    P * (episodeStream a k).owner = A * a.owner + B ∧
    iter shortcut (episodeStreamTime a k)
      (2 ^ a.anchor * a.owner - 1) =
        2 ^ a.anchor * (episodeStream a k).owner - 1

/-- V100 turns a repeated initial anchor into the full source-admitted
return certificate automatically. -/
theorem repeated_initial_anchor_is_certified
    (a : ValidEpisode) (k : Nat)
    (hk : 0 < k)
    (hsame : (episodeStream a k).anchor = a.anchor) :
    StreamAdmittedReturn a := by
  obtain ⟨A, B, P, q, D, hA, hP, hclass, hAff, htrace⟩ :=
    episode_stream_return_admitted a k hk hsame
  exact ⟨k, A, B, P, q, D, hk, hsame,
    hA, hP, hclass, hAff, htrace⟩

/-- The bounded-anchor case of the universal episode-stream frontier is now
closed: some actual reached episode state has a *genuine* admitted same-anchor
return. This is NOT an assertion that its return has a favourable sign or
that the original orbit descends. -/
theorem bounded_actual_stream_has_admitted_return
    (a : ValidEpisode) (B : Nat)
    (hbound : ∀ k, (episodeStream a k).anchor ≤ B) :
    ∃ i : Nat,
      StreamAdmittedReturn (episodeStream a i) := by
  obtain ⟨i, j, hij, heq⟩ :=
    bounded_actual_stream_repeats_anchor a B hbound
  have hk : 0 < j - i := by omega
  have hsame :
      (episodeStream (episodeStream a i) (j - i)).anchor =
        (episodeStream a i).anchor := by
    rw [episode_stream_shift]
    have hidx : i + (j - i) = j := by omega
    rw [hidx]
    exact heq.symm
  exact ⟨i,
    repeated_initial_anchor_is_certified
      (episodeStream a i) (j - i) hk hsame⟩

/-- Exact all-depth alternative for the *one coherent actual source orbit*:

1. Some actual episode state has a machine-admitted positive-time return, or
2. the actual episode anchors are unbounded.

The theorem does not claim either branch has already produced a
lower-source exit. The second branch is an explicit source-coupled
unbounded-anchor obstruction requiring new mathematics. -/
theorem admitted_return_or_unbounded_anchors
    (a : ValidEpisode) :
    (∃ i : Nat, StreamAdmittedReturn (episodeStream a i)) ∨
    (∀ B : Nat, ∃ k : Nat, B < (episodeStream a k).anchor) := by
  classical
  by_cases hbounded :
      ∃ B : Nat, ∀ k, (episodeStream a k).anchor ≤ B
  · obtain ⟨B, hb⟩ := hbounded
    exact Or.inl (bounded_actual_stream_has_admitted_return a B hb)
  · right
    intro B
    apply Classical.byContradiction
    intro hnot
    have hle : ∀ k, (episodeStream a k).anchor ≤ B := by
      intro k
      apply Classical.byContradiction
      intro hk
      have hgt : B < (episodeStream a k).anchor := by omega
      exact hnot ⟨k, hgt⟩
    exact hbounded ⟨B, hle⟩

#print axioms bounded_nat_sequence_not_injective
#print axioms bounded_actual_stream_repeats_anchor
#print axioms episode_stream_shift
#print axioms repeated_initial_anchor_is_certified
#print axioms bounded_actual_stream_has_admitted_return
#print axioms admitted_return_or_unbounded_anchors

end SourceProduct
end CollatzFinal
