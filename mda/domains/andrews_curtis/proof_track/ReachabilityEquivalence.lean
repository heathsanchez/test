import AC

/-!
# Reachability is an equivalence relation

The shared ACC statement defines `AC.Reachable` as the reflexive-transitive
closure of the primitive Andrews--Curtis moves.  The official source comments
that every move can be undone by a finite sequence, but does not package that
fact as a theorem.  This file proves the missing symmetry layer directly from
the official primitives.

This is useful for theorem mining: once a transformation is shown reachable,
all bare reachability consequences may be transported across it.
-/

namespace AC

/-- A single AC step gives an AC path. -/
theorem step_reachable' {n : ℕ} {R S : Relators n} (h : Step R S) :
    Reachable R S :=
  Relation.ReflTransGen.tail Relation.ReflTransGen.refl h

/-- Right multiplication by the inverse of another relator is derivable:
invert the other relator, multiply, then invert it back. -/
theorem mulRightInv_reachable {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) :
    Reachable R (Function.update R i (R i * (R j)⁻¹)) := by
  let S1 := Function.update R j (R j)⁻¹
  let S2 := Function.update S1 i (S1 i * S1 j)
  let S3 := Function.update S2 j (S2 j)⁻¹

  have h1 : Step R S1 := by
    simpa [S1] using Step.inv R j
  have h2 : Step S1 S2 := by
    simpa [S2] using Step.mulRight S1 i j hij
  have h3 : Step S2 S3 := by
    simpa [S3] using Step.inv S2 j

  have p1 : Reachable R S1 := step_reachable' h1
  have p2 : Reachable R S2 := Relation.ReflTransGen.tail p1 h2
  have p3 : Reachable R S3 := Relation.ReflTransGen.tail p2 h3

  have hfinal : S3 = Function.update R i (R i * (R j)⁻¹) := by
    funext k
    by_cases hki : k = i
    · subst k
      simp [S1, S2, S3, hij, Ne.symm hij]
    · by_cases hkj : k = j
      · subst k
        simp [S1, S2, S3, hij, Ne.symm hij]
      · simp [S1, S2, S3, hki, hkj]
  simpa [hfinal] using p3

/-- Every primitive AC step can be undone by a finite AC path. -/
theorem step_reverse_reachable {n : ℕ} {R S : Relators n}
    (h : Step R S) : Reachable S R := by
  cases h with
  | inv R i =>
      have hback :
          Step (Function.update R i (R i)⁻¹) R := by
        simpa using Step.inv (Function.update R i (R i)⁻¹) i
      exact step_reachable' hback

  | mulRight R i j hij =>
      let S := Function.update R i (R i * R j)
      have hback0 :
          Reachable S (Function.update S i (S i * (S j)⁻¹)) :=
        mulRightInv_reachable S i j hij
      have hrestore :
          Function.update S i (S i * (S j)⁻¹) = R := by
        funext k
        by_cases hki : k = i
        · subst k
          simp [S, hij]
        · simp [S, hki]
      simpa [S, hrestore] using hback0

  | conj R i w =>
      let S := Function.update R i (w * R i * w⁻¹)
      have hback0 :
          Reachable S
            (Function.update S i (w⁻¹ * S i * (w⁻¹)⁻¹)) :=
        step_reachable' (Step.conj S i w⁻¹)
      have hrestore :
          Function.update S i (w⁻¹ * S i * (w⁻¹)⁻¹) = R := by
        funext k
        by_cases hki : k = i
        · subst k
          simp [S, mul_assoc]
        · simp [S, hki]
      simpa [S, hrestore] using hback0

/-- AC reachability is symmetric. -/
theorem reachable_symm {n : ℕ} {R S : Relators n}
    (h : Reachable R S) : Reachable S R := by
  induction h with
  | refl =>
      exact Relation.ReflTransGen.refl
  | tail hprefix hstep ih =>
      exact (step_reverse_reachable hstep).trans ih

/-- Any reachable change of presentation preserves all future AC reachability
consequences. -/
theorem reachable_target_iff_of_reachable {n : ℕ} {R S T : Relators n}
    (hRS : Reachable R S) :
    Reachable R T ↔ Reachable S T := by
  constructor
  · intro hRT
    exact (reachable_symm hRS).trans hRT
  · intro hST
    exact hRS.trans hST

/-- In particular, any reachable change preserves the ordinary AC solvability
question for the standard target. -/
theorem standard_reachable_iff_of_reachable {n : ℕ} {R S : Relators n}
    (hRS : Reachable R S) :
    Reachable R (standard n) ↔ Reachable S (standard n) :=
  reachable_target_iff_of_reachable hRS

end AC
