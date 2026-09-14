import AC
import Mathlib.Tactic

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


/-- Swapping the same two distinct relators twice restores the original tuple. -/
theorem swapRelators_involutive {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) :
    swapRelators (swapRelators R i j) i j = R := by
  funext k
  by_cases hki : k = i
  · subst k
    simp [swapRelators, hij, Ne.symm hij]
  · by_cases hkj : k = j
    · subst k
      simp [swapRelators, hij, Ne.symm hij]
    · simp [swapRelators, hki, hkj]

/-- Relator exchange is AC-bireachable. -/
theorem relatorSwap_bireachable {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) :
    Reachable R (swapRelators R i j) ∧
      Reachable (swapRelators R i j) R := by
  let S := swapRelators R i j
  have hrs : Reachable R S := by
    simpa [S] using relatorSwap_reachable R i j hij
  have hsr0 : Reachable S (swapRelators S i j) :=
    relatorSwap_reachable S i j hij
  have hinv : swapRelators S i j = R := by
    simpa [S] using swapRelators_involutive R i j hij
  have hsr : Reachable S R := by
    simpa [hinv] using hsr0
  exact ⟨hrs, hsr⟩

/-- Relator exchange preserves reachability to the standard presentation. -/
theorem relatorSwap_standard_iff {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) :
    Reachable R (standard n) ↔
      Reachable (swapRelators R i j) (standard n) := by
  have hb := relatorSwap_bireachable R i j hij
  exact reachable_target_iff_of_bireachable hb.1 hb.2


/-! ## Parameterized funnel family

The recurrent-route miner found that two independent verified certificates
coalesce at

`(x y⁻² x⁻¹ y³, y⁻⁷ x⁻¹)`.

That state is one instance of the following infinite family.  The proof below
is constructive and uses only the official `Step` relation.
-/

/-- Derived left multiplication of one relator by another. -/
theorem funnel_leftMul_reachable {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) :
    Reachable R (Function.update R i (R j * R i)) := by
  let S := Function.update R i (R i * R j)
  have h1 : Step R S := by
    simpa [S] using Step.mulRight R i j hij
  have h2 : Step S (Function.update R i (R j * R i)) := by
    simpa [S, hij, Ne.symm hij, mul_assoc] using Step.conj S i (R j)
  exact Relation.ReflTransGen.tail (step_reachable h1) h2

/-- Derived left multiplication by the inverse of another relator. -/
theorem funnel_leftMulInv_reachable {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) :
    Reachable R (Function.update R i ((R j)⁻¹ * R i)) := by
  let S1 := Function.update R j (R j)⁻¹
  let S2 := Function.update S1 i (S1 i * S1 j)
  let S3 := Function.update S2 j (S2 j)⁻¹
  let S4 := Function.update S3 i ((R j)⁻¹ * R i)

  have h1 : Step R S1 := by
    simpa [S1] using Step.inv R j
  have h2 : Step S1 S2 := by
    simpa [S2] using Step.mulRight S1 i j hij
  have h3 : Step S2 S3 := by
    simpa [S3] using Step.inv S2 j
  have h4 : Step S3 S4 := by
    simpa [S1, S2, S3, S4, hij, Ne.symm hij, mul_assoc] using
      Step.conj S3 i (R j)⁻¹

  have p1 : Reachable R S1 := step_reachable h1
  have p2 : Reachable R S2 := Relation.ReflTransGen.tail p1 h2
  have p3 : Reachable R S3 := Relation.ReflTransGen.tail p2 h3
  have p4 : Reachable R S4 := Relation.ReflTransGen.tail p3 h4

  have hfinal : S4 = Function.update R i ((R j)⁻¹ * R i) := by
    funext q
    by_cases hqi : q = i
    · subst q
      simp [S4]
    · by_cases hqj : q = j
      · subst q
        simp [S1, S2, S3, S4, hij, Ne.symm hij]
      · simp [S1, S2, S3, S4, hqi, hqj]
  rw [hfinal] at p4
  exact p4

def funnelX : Word 2 := FreeGroup.of (0 : Fin 2)
def funnelY : Word 2 := FreeGroup.of (1 : Fin 2)

def funnelA (m : ℕ) : Word 2 :=
  funnelX * (funnelY⁻¹)^m * funnelX⁻¹ * funnelY^(m+1)

def funnelB (k : ℕ) : Word 2 :=
  (funnelY⁻¹)^k * funnelX⁻¹

def funnelC (m k : ℕ) : Word 2 :=
  (funnelY⁻¹)^m * funnelB k * funnelY^m

def funnelRelators (m k : ℕ) : Relators 2 :=
  ![funnelA m, funnelB k]

/-- Updating the first coordinate of a rank-two tuple has the expected vector form. -/
theorem funnel_update_zero (a b c : Word 2) :
    Function.update (![a, b] : Relators 2) (0 : Fin 2) c = ![c, b] := by
  funext q
  fin_cases q <;> simp

/-- Updating the second coordinate of a rank-two tuple has the expected vector form. -/
theorem funnel_update_one (a b c : Word 2) :
    Function.update (![a, b] : Relators 2) (1 : Fin 2) c = ![a, c] := by
  funext q
  fin_cases q <;> simp

theorem funnel_B_mul_A (m k : ℕ) :
    funnelB k * funnelA m = funnelC m k * funnelY := by
  simp [funnelA, funnelB, funnelC]
  group

theorem funnel_conj_B (m k : ℕ) :
    (funnelY⁻¹)^m * funnelB k * ((funnelY⁻¹)^m)⁻¹ =
      funnelC m k := by
  simp [funnelC]
  group

theorem funnel_unconj_C (m k : ℕ) :
    funnelY^m * funnelC m k * (funnelY^m)⁻¹ = funnelB k := by
  simp [funnelC]
  group

theorem funnel_Y_mul_B_succ (k : ℕ) :
    funnelY * funnelB (k+1) = funnelB k := by
  simp [funnelB]
  group

/-- Once the first relator is `y`, the second relator
`y^{-k} x^{-1}` is reduced uniformly to `x^{-1}`. -/
theorem funnel_eliminate_k (k : ℕ) :
    Reachable (![funnelY, funnelB k] : Relators 2)
      (![funnelY, funnelX⁻¹] : Relators 2) := by
  induction k with
  | zero =>
      simpa [funnelB] using
        (Relation.ReflTransGen.refl :
          Reachable (![funnelY, funnelX⁻¹] : Relators 2)
            (![funnelY, funnelX⁻¹] : Relators 2))
  | succ k ih =>
      have hstep := funnel_leftMul_reachable
        (![funnelY, funnelB (k+1)] : Relators 2)
        (1 : Fin 2) (0 : Fin 2) (by decide)
      have hreduce0 :
          Reachable (![funnelY, funnelB (k+1)] : Relators 2)
            (Function.update (![funnelY, funnelB (k+1)] : Relators 2)
              (1 : Fin 2) (funnelB k)) := by
        simpa [funnel_Y_mul_B_succ] using hstep
      have hreduce :
          Reachable (![funnelY, funnelB (k+1)] : Relators 2)
            (![funnelY, funnelB k] : Relators 2) := by
        rw [funnel_update_one] at hreduce0
        exact hreduce0
      exact hreduce.trans ih

/-- Infinite constructive family discovered from the shared proof funnel.

For every `m,k ≥ 0`, the balanced rank-two presentation

`(x y^{-m} x^{-1} y^{m+1}, y^{-k} x^{-1})`

is Andrews--Curtis reachable to the standard presentation `(x,y)`.
-/
theorem funnelFamily_reachable (m k : ℕ) :
    Reachable (funnelRelators m k) (standard 2) := by
  let C := funnelC m k

  have h1raw := funnel_leftMul_reachable
    (funnelRelators m k) (0 : Fin 2) (1 : Fin 2) (by decide)
  have h1u :
      Reachable (funnelRelators m k)
        (Function.update (funnelRelators m k) (0 : Fin 2)
          (C * funnelY)) := by
    simpa [funnelRelators, C, funnel_B_mul_A] using h1raw
  have h1 :
      Reachable (funnelRelators m k)
        (![C * funnelY, funnelB k] : Relators 2) := by
    rw [funnelRelators, funnel_update_zero] at h1u
    exact h1u

  have hs2raw :=
    Step.conj (![C * funnelY, funnelB k] : Relators 2)
      (1 : Fin 2) ((funnelY⁻¹)^m)
  have hs2mid :
      Step (![C * funnelY, funnelB k] : Relators 2)
        (Function.update (![C * funnelY, funnelB k] : Relators 2)
          (1 : Fin 2)
          ((funnelY⁻¹)^m * funnelB k * ((funnelY⁻¹)^m)⁻¹)) := by
    simpa using hs2raw
  have hCB : (funnelY⁻¹)^m * funnelB k * ((funnelY⁻¹)^m)⁻¹ = C := by
    simpa [C] using funnel_conj_B m k
  rw [hCB] at hs2mid
  have hs2 :
      Step (![C * funnelY, funnelB k] : Relators 2)
        (![C * funnelY, C] : Relators 2) := by
    rw [funnel_update_one] at hs2mid
    exact hs2mid
  have h2 :
      Reachable (funnelRelators m k)
        (![C * funnelY, C] : Relators 2) :=
    Relation.ReflTransGen.tail h1 hs2

  have h3raw := funnel_leftMulInv_reachable
    (![C * funnelY, C] : Relators 2)
      (0 : Fin 2) (1 : Fin 2) (by decide)
  have hCY : C⁻¹ * (C * funnelY) = funnelY := by
    group
  rw [hCY] at h3raw
  have h3local :
      Reachable (![C * funnelY, C] : Relators 2)
        (![funnelY, C] : Relators 2) := by
    rw [funnel_update_zero] at h3raw
    exact h3raw
  have h3 :
      Reachable (funnelRelators m k)
        (![funnelY, C] : Relators 2) :=
    h2.trans h3local

  have hs4raw :=
    Step.conj (![funnelY, C] : Relators 2)
      (1 : Fin 2) (funnelY^m)
  have hs4mid :
      Step (![funnelY, C] : Relators 2)
        (Function.update (![funnelY, C] : Relators 2)
          (1 : Fin 2) (funnelY^m * C * (funnelY^m)⁻¹)) := by
    simpa using hs4raw
  have hBC : funnelY^m * C * (funnelY^m)⁻¹ = funnelB k := by
    simpa [C] using funnel_unconj_C m k
  rw [hBC] at hs4mid
  have hs4 :
      Step (![funnelY, C] : Relators 2)
        (![funnelY, funnelB k] : Relators 2) := by
    rw [funnel_update_one] at hs4mid
    exact hs4mid
  have h4 :
      Reachable (funnelRelators m k)
        (![funnelY, funnelB k] : Relators 2) :=
    Relation.ReflTransGen.tail h3 hs4

  have h5 :
      Reachable (funnelRelators m k)
        (![funnelY, funnelX⁻¹] : Relators 2) :=
    h4.trans (funnel_eliminate_k k)

  have hs6raw :=
    Step.inv (![funnelY, funnelX⁻¹] : Relators 2) (1 : Fin 2)
  have hs6mid :
      Step (![funnelY, funnelX⁻¹] : Relators 2)
        (Function.update (![funnelY, funnelX⁻¹] : Relators 2)
          (1 : Fin 2) funnelX) := by
    simpa using hs6raw
  have hs6 :
      Step (![funnelY, funnelX⁻¹] : Relators 2)
        (![funnelY, funnelX] : Relators 2) := by
    rw [funnel_update_one] at hs6mid
    exact hs6mid
  have h6 :
      Reachable (funnelRelators m k)
        (![funnelY, funnelX] : Relators 2) :=
    Relation.ReflTransGen.tail h5 hs6

  have hswap := relatorSwap_reachable
    (![funnelY, funnelX] : Relators 2)
      (0 : Fin 2) (1 : Fin 2) (by decide)
  have htarget :
      swapRelators (![funnelY, funnelX] : Relators 2)
        (0 : Fin 2) (1 : Fin 2) = standard 2 := by
    funext q
    fin_cases q <;> simp [swapRelators, funnelX, funnelY, standard]
  rw [htarget] at hswap
  exact h6.trans hswap

end AC
