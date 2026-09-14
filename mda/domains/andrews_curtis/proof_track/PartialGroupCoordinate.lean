import NormalClosureCoordinate
import Mathlib.GroupTheory.QuotientGroup.Defs

namespace AC

/-- The group presented by every relator except coordinate i. -/
abbrev PartialPresentationGroup {n : ℕ} (R : Relators n) (i : Fin n) :=
  Word n ⧸ otherRelatorNormalClosure R i

/-- The semantic value carried by coordinate i: its image in the group
presented by all the other relators. -/
def coordinateClass {n : ℕ} (R : Relators n) (i : Fin n) :
    PartialPresentationGroup R i :=
  (R i : PartialPresentationGroup R i)

/-- Equality of semantic coordinate classes is exactly congruence modulo the
normal closure of the other relators. -/
theorem partial_group_class_eq_iff {n : ℕ}
    (R : Relators n) (i : Fin n) (a c : Word n) :
    (c : PartialPresentationGroup R i) =
        (a : PartialPresentationGroup R i)
      ↔
    c / a ∈ otherRelatorNormalClosure R i := by
  exact QuotientGroup.eq_iff_div_mem

/-- Replacing one relator by any word with the same image in the partial
presentation group preserves ordinary AC reachability. -/
theorem same_partial_group_class_reachable {n : ℕ}
    (R : Relators n) (i : Fin n) (c : Word n)
    (hq :
      (c : PartialPresentationGroup R i) = coordinateClass R i) :
    Reachable R (Function.update R i c) := by
  have hmem :
      c / R i ∈ otherRelatorNormalClosure R i :=
    (partial_group_class_eq_iff R i (R i) c).mp hq
  have p :=
    otherRelatorNormalClosure_coordinate_reachable
      R i (h := c / R i) hmem
  have heq : (c / R i) * R i = c := by
    group
  rw [heq] at p
  exact p

/-- Semantic coordinate replacement preserves every future target consequence. -/
theorem same_partial_group_class_target_iff {n : ℕ}
    (R T : Relators n) (i : Fin n) (c : Word n)
    (hq :
      (c : PartialPresentationGroup R i) = coordinateClass R i) :
    Reachable R T ↔ Reachable (Function.update R i c) T := by
  exact reachable_target_iff_of_reachable
    (same_partial_group_class_reachable R i c hq)

end AC
