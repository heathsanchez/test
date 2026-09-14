import AC

/-!
# Orbit soundness lemmas for Andrews--Curtis search

These lemmas isolate a distinction that is useful for shortest-path search but
irrelevant to bare AC reachability: cyclic rotation of an individual relator.

The Discovery-track experiments on branch `acc-competitive-residual-v1`
found that rotation information is causally useful for finding shorter atomic
certificates. In the shared Proof-track semantics, however, a cyclic rotation
is just conjugation in the ambient free group. Therefore it may change search
cost without changing the underlying reachability class.

This file is intentionally small and generic. It imports only the shared
official `AC` definitions.
-/

namespace AC

/-- One official AC step gives a finite AC path. -/
theorem step_reachable {n : ℕ} {R S : Relators n} (h : Step R S) :
    Reachable R S :=
  Relation.ReflTransGen.tail Relation.ReflTransGen.refl h

/-- Replacing one relator by an arbitrary conjugate is AC-reachable. -/
theorem conjugateRelator_reachable {n : ℕ} (R : Relators n) (i : Fin n)
    (w : Word n) :
    Reachable R (Function.update R i (w * R i * w⁻¹)) :=
  step_reachable (Step.conj R i w)

/-- Replacing one relator by its inverse is AC-reachable. -/
theorem invertRelator_reachable {n : ℕ} (R : Relators n) (i : Fin n) :
    Reachable R (Function.update R i (R i)⁻¹) :=
  step_reachable (Step.inv R i)

/-- A cyclic rotation `u * v ↦ v * u` of a relator is AC-reachable.

Indeed, conjugating `u * v` by `u⁻¹` gives `v * u`.
-/
theorem cyclicRotation_reachable {n : ℕ} (R : Relators n) (i : Fin n)
    (u v : Word n) (h : R i = u * v) :
    Reachable R (Function.update R i (v * u)) := by
  have hconj :
      Reachable R (Function.update R i (u⁻¹ * R i * (u⁻¹)⁻¹)) :=
    conjugateRelator_reachable R i u⁻¹
  simpa [h, mul_assoc] using hconj

/-- Cyclic rotation is reversible by another cyclic rotation, so the two
presentations lie in the same AC reachability class.
-/
theorem cyclicRotation_bireachable {n : ℕ} (R : Relators n) (i : Fin n)
    (u v : Word n) (h : R i = u * v) :
    let S := Function.update R i (v * u)
    Reachable R S ∧ Reachable S R := by
  let S := Function.update R i (v * u)
  have hrs : Reachable R S := by
    simpa [S] using cyclicRotation_reachable R i u v h
  have hSi : S i = v * u := by
    simp [S]
  have hsr0 : Reachable S (Function.update S i (u * v)) :=
    cyclicRotation_reachable S i v u hSi
  have hrestore : Function.update S i (u * v) = R := by
    funext j
    by_cases hj : j = i
    · subst j
      simp [S, h]
    · simp [S, hj]
  have hsr : Reachable S R := by
    simpa [hrestore] using hsr0
  exact ⟨hrs, hsr⟩


/-- Bireachable presentations have exactly the same reachability consequences. -/
theorem reachable_target_iff_of_bireachable {n : ℕ} {R S T : Relators n}
    (hRS : Reachable R S) (hSR : Reachable S R) :
    Reachable R T ↔ Reachable S T := by
  constructor
  · intro hRT
    exact hSR.trans hRT
  · intro hST
    exact hRS.trans hST

/-- Cyclic rotation of one relator preserves the AC question itself: the
original presentation reaches the standard tuple iff the rotated one does.
Thus rotation information may legitimately refine shortest-path search while
being quotiented away for bare AC solvability.
-/
theorem cyclicRotation_standard_iff {n : ℕ} (R : Relators n) (i : Fin n)
    (u v : Word n) (h : R i = u * v) :
    Reachable R (standard n) ↔
      Reachable (Function.update R i (v * u)) (standard n) := by
  have hb := cyclicRotation_bireachable R i u v h
  exact reachable_target_iff_of_bireachable hb.1 hb.2

/-- Invert a relator and then conjugate it. This captures the other half of
the usual cyclic/inverse orientation orbit used by search procedures.
-/
theorem inverseConjugateRelator_reachable {n : ℕ} (R : Relators n)
    (i : Fin n) (w : Word n) :
    Reachable R (Function.update R i (w * (R i)⁻¹ * w⁻¹)) := by
  let S := Function.update R i (R i)⁻¹
  have hRS : Reachable R S := by
    simpa [S] using invertRelator_reachable R i
  have hstep :
      Step S (Function.update S i (w * S i * w⁻¹)) :=
    Step.conj S i w
  have hpath :
      Reachable R (Function.update S i (w * S i * w⁻¹)) :=
    Relation.ReflTransGen.tail hRS hstep
  simpa [S] using hpath

end AC
