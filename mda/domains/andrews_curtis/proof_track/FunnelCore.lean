import ReachabilityEquivalence
import Mathlib.Tactic

/-!
# The AC funnel law

The concrete two-parameter family discovered by route mining is an instance of
one general local law.

If relator i satisfies

  R_j * R_i = (w * R_j * w⁻¹) * y,

then four derived AC operations replace R_i by y while restoring R_j and
leaving every other relator unchanged.

Equivalently, the twist

  R_i ↦ R_j⁻¹ * w * R_j * w⁻¹ * R_i

is removable by AC moves.

This is the compressed theorem behind the mined funnel.
-/

namespace AC

/-- Derived left multiplication of relator i by a distinct relator j. -/
theorem funnelCore_leftMul_reachable {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) :
    Reachable R (Function.update R i (R j * R i)) := by
  let S := Function.update R i (R i * R j)
  have h1 : Step R S := by
    simpa [S] using Step.mulRight R i j hij
  have h2 : Step S (Function.update R i (R j * R i)) := by
    simpa [S, hij, Ne.symm hij, mul_assoc] using Step.conj S i (R j)
  exact Relation.ReflTransGen.tail (step_reachable' h1) h2

/-- Derived left multiplication by the inverse of a distinct relator. -/
theorem funnelCore_leftMulInv_reachable {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) :
    Reachable R (Function.update R i ((R j)⁻¹ * R i)) := by
  let S1 := Function.update R j (R j)⁻¹
  have h1 : Reachable R S1 :=
    step_reachable' (by simpa [S1] using Step.inv R j)

  have h2raw :=
    funnelCore_leftMul_reachable S1 i j hij
  let S2 := Function.update S1 i ((R j)⁻¹ * R i)
  have h2 : Reachable S1 S2 := by
    simpa [S1, S2, hij, Ne.symm hij] using h2raw

  let S3 := Function.update S2 j (R j)
  have hs3 : Step S2 S3 := by
    simpa [S1, S2, S3, hij, Ne.symm hij] using Step.inv S2 j
  have h3 : Reachable R S3 :=
    Relation.ReflTransGen.tail (h1.trans h2) hs3

  have hfinal : S3 = Function.update R i ((R j)⁻¹ * R i) := by
    funext q
    by_cases hqi : q = i
    · subst q
      simp [S1, S2, S3, hij, Ne.symm hij]
    · by_cases hqj : q = j
      · subst q
        simp [S1, S2, S3, hij, Ne.symm hij]
      · simp [S1, S2, S3, hqi, hqj]
  rw [hfinal] at h3
  exact h3


/-- Generic funnel contraction.

If left-multiplying relator i by relator j exposes a conjugate of relator j
followed by a desired word y, then the presentation can replace relator i by y
without changing any other final relator. -/
theorem funnel_contract {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) (w y : Word n)
    (h : R j * R i = (w * R j * w⁻¹) * y) :
    Reachable R (Function.update R i y) := by
  let C : Word n := w * R j * w⁻¹
  let S1 : Relators n := Function.update R i (C * y)

  have h1raw := funnelCore_leftMul_reachable R i j hij
  have h1 : Reachable R S1 := by
    simpa [S1, C, h] using h1raw

  let S2 : Relators n := Function.update S1 j C
  have hs2 : Step S1 S2 := by
    simpa [S1, S2, C, hij, Ne.symm hij] using Step.conj S1 j w
  have h2 : Reachable R S2 :=
    Relation.ReflTransGen.tail h1 hs2

  have h3raw := funnelCore_leftMulInv_reachable S2 i j hij
  have hcollapse : (S2 j)⁻¹ * S2 i = y := by
    simp [S1, S2, C, hij, Ne.symm hij]
    group
  rw [hcollapse] at h3raw
  let S3 : Relators n := Function.update S2 i y
  have h3local : Reachable S2 S3 := by
    simpa [S3] using h3raw
  have h3 : Reachable R S3 := h2.trans h3local

  let S4 : Relators n := Function.update S3 j (R j)
  have hS3j : S3 j = C := by
    simp [S1, S2, S3, C, hij, Ne.symm hij]
  have hback : w⁻¹ * S3 j * (w⁻¹)⁻¹ = R j := by
    rw [hS3j]
    simp [C, mul_assoc]
  have hs4raw :
      Step S3 (Function.update S3 j (w⁻¹ * S3 j * (w⁻¹)⁻¹)) :=
    Step.conj S3 j w⁻¹
  rw [hback] at hs4raw
  have hs4 : Step S3 S4 := by
    simpa [S4] using hs4raw
  have h4 : Reachable R S4 :=
    Relation.ReflTransGen.tail h3 hs4

  have hfinal : S4 = Function.update R i y := by
    funext q
    by_cases hqi : q = i
    · subst q
      simp [S1, S2, S3, S4, hij, Ne.symm hij]
    · by_cases hqj : q = j
      · subst q
        simp [S1, S2, S3, S4, hij, Ne.symm hij]
      · simp [S1, S2, S3, S4, hqi, hqj]
  rw [hfinal] at h4
  exact h4

/-- The removable-twist form of the funnel law.

Starting from a presentation R, modify relator i by

  R_j⁻¹ * w * R_j * w⁻¹ * R_i.

The modified presentation AC-reduces back to R.  Thus this transformation
generates no new ordinary-AC solvability class. -/
theorem commutatorTwist_contract {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) (w : Word n) :
    Reachable
      (Function.update R i ((R j)⁻¹ * w * R j * w⁻¹ * R i))
      R := by
  let S : Relators n :=
    Function.update R i ((R j)⁻¹ * w * R j * w⁻¹ * R i)

  have hSj : S j = R j := by
    simp [S, Ne.symm hij]
  have hSi : S i = (R j)⁻¹ * w * R j * w⁻¹ * R i := by
    simp [S]
  have heq : S j * S i = (w * S j * w⁻¹) * R i := by
    rw [hSj, hSi]
    group

  have hred :=
    funnel_contract S i j hij w (R i) heq

  have hfinal : Function.update S i (R i) = R := by
    funext q
    by_cases hqi : q = i
    · subst q
      simp [S]
    · simp [S, hqi]
  rw [hfinal] at hred
  exact hred

/-- Therefore adding a removable twist preserves every future reachability
consequence. -/
theorem commutatorTwist_target_iff {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) (w : Word n) (T : Relators n) :
    Reachable
      (Function.update R i ((R j)⁻¹ * w * R j * w⁻¹ * R i))
      T ↔ Reachable R T := by
  have h :=
    commutatorTwist_contract R i j hij w
  constructor
  · intro htw
    exact (reachable_symm h).trans htw
  · intro hRT
    exact h.trans hRT

end AC
