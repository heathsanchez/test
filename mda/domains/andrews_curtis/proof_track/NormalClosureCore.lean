import ReachabilityEquivalence
import Mathlib.Algebra.Group.Subgroup.Basic
import Mathlib.Tactic

/-!
# Minimal normal-closure coordinate law

This is the distilled theorem underneath the funnel/commutator development.

For a presentation R and coordinate i, let N_{-i} be the normal closure of
all relators except R_i.  Any h ∈ N_{-i} may be left-multiplied into R_i by a
finite ordinary Andrews--Curtis path while every other relator is restored.

The proof uses only:
* the official AC primitive moves;
* reversibility/transitivity of finite AC reachability;
* the definition of subgroup normal closure.

No funnel, commutator, theorem-mining, rank-two, or search-specific machinery
is required.
-/

namespace AC

def otherRelatorsCore {n : ℕ} (R : Relators n) (i : Fin n) : Set (Word n) :=
  {b | ∃ j : Fin n, j ≠ i ∧ R j = b}

def otherNormalClosureCore {n : ℕ} (R : Relators n) (i : Fin n) :
    Subgroup (Word n) :=
  Subgroup.normalClosure (otherRelatorsCore R i)

instance otherNormalClosureCore_normal {n : ℕ}
    (R : Relators n) (i : Fin n) :
    (otherNormalClosureCore R i).Normal := by
  unfold otherNormalClosureCore
  infer_instance

/-- Derived left multiplication by a distinct relator. -/
theorem core_leftMul_reachable {n : ℕ}
    (R : Relators n) (i j : Fin n) (hij : i ≠ j) :
    Reachable R (Function.update R i (R j * R i)) := by
  let S := Function.update R i (R i * R j)
  have h1 : Step R S := by
    simpa [S] using Step.mulRight R i j hij
  have h2 : Step S (Function.update R i (R j * R i)) := by
    simpa [S, hij, Ne.symm hij, mul_assoc] using
      Step.conj S i (R j)
  exact (step_reachable' h1).trans (step_reachable' h2)

/-- Insert an arbitrary conjugate of another relator on the left of coordinate
i, restoring the source relator afterwards. -/
theorem core_conjugate_insert_reachable {n : ℕ}
    (R : Relators n) (i j : Fin n) (hij : i ≠ j)
    (a c : Word n) :
    Reachable
      (Function.update R i a)
      (Function.update R i ((c * R j * c⁻¹) * a)) := by
  let P : Relators n := Function.update R i a
  let Q : Relators n := Function.update P j (c * P j * c⁻¹)
  let M : Relators n := Function.update Q i (Q j * Q i)
  let F : Relators n := Function.update R i ((c * R j * c⁻¹) * a)

  have p1 : Reachable P Q := by
    exact step_reachable' (by
      simpa [Q] using Step.conj P j c)

  have p2raw := core_leftMul_reachable Q i j hij
  have p2 : Reachable Q M := by
    simpa [M] using p2raw

  have hs3 := Step.conj M j c⁻¹
  have hrestore :
      Function.update M j (c⁻¹ * M j * (c⁻¹)⁻¹) = F := by
    funext q
    by_cases hqj : q = j
    · subst q
      simp [M, Q, P, F, hij, Ne.symm hij]
      group
    · by_cases hqi : q = i
      · subst q
        simp [M, Q, P, F, hij, Ne.symm hij]
      · simp [M, Q, P, F, hqi, hqj]
  rw [hrestore] at hs3
  have p3 : Reachable M F := step_reachable' hs3

  have p := (p1.trans p2).trans p3
  simpa [P, F] using p

/-- Minimal auxiliary form: any element in the normal closure of the other
relators may be absorbed into an arbitrary current value at coordinate i. -/
theorem core_normalClosure_coordinate_reachable_aux {n : ℕ}
    (R : Relators n) (i : Fin n) {h : Word n}
    (hh : h ∈ otherNormalClosureCore R i)
    (a : Word n) :
    Reachable
      (Function.update R i a)
      (Function.update R i (h * a)) := by
  unfold otherNormalClosureCore at hh
  change h ∈
    Subgroup.closure (Group.conjugatesOfSet (otherRelatorsCore R i)) at hh
  induction hh using Subgroup.closure_induction generalizing a with
  | mem x hx =>
      rw [Group.mem_conjugatesOfSet_iff] at hx
      rcases hx with ⟨b, hb, hconj⟩
      rcases hb with ⟨j, hji, hjb⟩
      obtain ⟨c, rfl⟩ := isConj_iff.1 hconj
      subst b
      exact core_conjugate_insert_reachable
        R i j (Ne.symm hji) a c
  | one =>
      simpa using
        (Relation.ReflTransGen.refl :
          Reachable (Function.update R i a)
            (Function.update R i a))
  | mul x y hx hy ihx ihy =>
      have p1 :
          Reachable
            (Function.update R i a)
            (Function.update R i (y * a)) :=
        ihy a
      have p2 :
          Reachable
            (Function.update R i (y * a))
            (Function.update R i (x * (y * a))) :=
        ihx (y * a)
      simpa [mul_assoc] using p1.trans p2
  | inv x hx ih =>
      have p :
          Reachable
            (Function.update R i (x⁻¹ * a))
            (Function.update R i (x * (x⁻¹ * a))) :=
        ih (x⁻¹ * a)
      have p' :
          Reachable
            (Function.update R i (x⁻¹ * a))
            (Function.update R i a) := by
        simpa [mul_assoc] using p
      exact reachable_symm p'

/-- Distilled rank-independent coordinate law. -/
theorem core_normalClosure_coordinate_reachable {n : ℕ}
    (R : Relators n) (i : Fin n) {h : Word n}
    (hh : h ∈ otherNormalClosureCore R i) :
    Reachable R (Function.update R i (h * R i)) := by
  have p :=
    core_normalClosure_coordinate_reachable_aux R i hh (R i)
  simpa using p

/-- Congruence modulo the normal closure of the other relators preserves every
future ordinary-AC target consequence. -/
theorem core_normalClosure_target_iff {n : ℕ}
    (R T : Relators n) (i : Fin n) {h : Word n}
    (hh : h ∈ otherNormalClosureCore R i) :
    Reachable R T ↔
      Reachable (Function.update R i (h * R i)) T := by
  exact reachable_target_iff_of_reachable
    (core_normalClosure_coordinate_reachable R i hh)

end AC
