import FunnelCore

/-!
# Finite closure under removable AC twists

The one-step funnel law composes.  Keeping relator j fixed, any finite list of
ambient words generates a finite product of conjugacy-difference factors on
relator i, and the resulting presentation remains AC-equivalent to the
original.

This is the constructive finite form of the higher-commutator direction
suggested by the mined funnel; no subgroup abstraction is needed.
-/

namespace AC

/-- Apply a finite list of removable left twists to one word, with fixed source
relator b. -/
def twistProduct {n : ℕ} (b : Word n) : List (Word n) → Word n → Word n
  | [], a => a
  | w :: ws, a => b⁻¹ * w * b * w⁻¹ * twistProduct b ws a

/-- Updating coordinate i leaves a distinct coordinate j unchanged. -/
theorem update_other_eq {n : ℕ} (R : Relators n) (i j : Fin n)
    (hij : i ≠ j) (a : Word n) :
    Function.update R i a j = R j := by
  simp [Ne.symm hij]

/-- Any finite product of removable twists contracts back to the original
presentation. -/
theorem twistProduct_contract {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) (ws : List (Word n)) :
    Reachable
      (Function.update R i (twistProduct (R j) ws (R i)))
      R := by
  induction ws with
  | nil =>
      simpa [twistProduct] using
        (Relation.ReflTransGen.refl : Reachable R R)
  | cons w ws ih =>
      let S : Relators n :=
        Function.update R i (twistProduct (R j) ws (R i))

      have hSj : S j = R j := by
        simp [S, Ne.symm hij]
      have hSi : S i = twistProduct (R j) ws (R i) := by
        simp [S]

      have hone :=
        commutatorTwist_contract S i j hij w

      have hstart :
          Function.update S i
              ((S j)⁻¹ * w * S j * w⁻¹ * S i)
            =
          Function.update R i
              (twistProduct (R j) (w :: ws) (R i)) := by
        funext q
        by_cases hqi : q = i
        · subst q
          simp [S, twistProduct, hSj, hSi]
        · simp [S, twistProduct, hqi]

      have hend :
          S = Function.update R i (twistProduct (R j) ws (R i)) := by
        rfl

      rw [hstart, hend] at hone
      exact hone.trans ih

/-- Finite twist products preserve every future reachability consequence. -/
theorem twistProduct_target_iff {n : ℕ} (R : Relators n)
    (i j : Fin n) (hij : i ≠ j) (ws : List (Word n)) (T : Relators n) :
    Reachable
        (Function.update R i (twistProduct (R j) ws (R i)))
        T
      ↔
    Reachable R T := by
  have h := twistProduct_contract R i j hij ws
  constructor
  · intro htw
    exact (reachable_symm h).trans htw
  · intro hRT
    exact h.trans hRT

end AC
