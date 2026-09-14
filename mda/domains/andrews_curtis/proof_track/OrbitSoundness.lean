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


/-- Exchange two distinct relators, leaving every other relator fixed. -/
def swapRelators {n : ℕ} (R : Relators n) (i j : Fin n) : Relators n :=
  Function.update (Function.update R i (R j)) j (R i)

/-- Relator exchange is derivable from the three primitive AC moves.

The seven-step Nielsen sequence is
`(A,B) → (AB,B) → ((AB)⁻¹,B) → ((AB)⁻¹,A⁻¹)
→ (AB,A⁻¹) → (ABA⁻¹,A⁻¹) → (B,A⁻¹) → (B,A)`.
-/
theorem relatorSwap_reachable {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) :
    Reachable R (swapRelators R i j) := by
  let S1 := Function.update R i (R i * R j)
  let S2 := Function.update S1 i ((R i * R j)⁻¹)
  let S3 := Function.update S2 j (R i)⁻¹
  let S4 := Function.update S3 i (R i * R j)
  let S5 := Function.update S4 i (R i * R j * (R i)⁻¹)
  let S6 := Function.update S5 i (R j)
  let S7 := Function.update S6 j (R i)

  have h1 : Step R S1 := by
    simpa [S1] using Step.mulRight R i j hij
  have h2 : Step S1 S2 := by
    simpa [S1, S2] using Step.inv S1 i
  have h3 : Step S2 S3 := by
    simpa [S1, S2, S3, hij, Ne.symm hij, mul_assoc] using
      Step.mulRight S2 j i (Ne.symm hij)
  have h4 : Step S3 S4 := by
    simpa [S1, S2, S3, S4, hij, Ne.symm hij] using Step.inv S3 i
  have h5 : Step S4 S5 := by
    simpa [S1, S2, S3, S4, S5, hij, Ne.symm hij, mul_assoc] using
      Step.mulRight S4 i j hij
  have h6 : Step S5 S6 := by
    simpa [S1, S2, S3, S4, S5, S6, hij, Ne.symm hij, mul_assoc] using
      Step.conj S5 i (R i)⁻¹
  have h7 : Step S6 S7 := by
    simpa [S1, S2, S3, S4, S5, S6, S7, hij, Ne.symm hij] using Step.inv S6 j

  have p1 : Reachable R S1 := step_reachable h1
  have p2 : Reachable R S2 := Relation.ReflTransGen.tail p1 h2
  have p3 : Reachable R S3 := Relation.ReflTransGen.tail p2 h3
  have p4 : Reachable R S4 := Relation.ReflTransGen.tail p3 h4
  have p5 : Reachable R S5 := Relation.ReflTransGen.tail p4 h5
  have p6 : Reachable R S6 := Relation.ReflTransGen.tail p5 h6
  have p7 : Reachable R S7 := Relation.ReflTransGen.tail p6 h7

  have hfinal : S7 = swapRelators R i j := by
    funext k
    by_cases hki : k = i
    · subst k
      simp [S1, S2, S3, S4, S5, S6, S7, swapRelators, hij, Ne.symm hij]
    · by_cases hkj : k = j
      · subst k
        simp [S1, S2, S3, S4, S5, S6, S7, swapRelators, hij, Ne.symm hij]
      · simp [S1, S2, S3, S4, S5, S6, S7, swapRelators, hki, hkj]
  simpa [hfinal] using p7

end AC
