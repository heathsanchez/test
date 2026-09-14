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
  QuotientGroup.mk' (otherRelatorNormalClosure R i) (R i)

/-- Replacing one relator by any word with the same image in the partial
presentation group preserves ordinary AC reachability. -/
theorem same_partial_group_class_reachable {n : ℕ}
    (R : Relators n) (i : Fin n) (c : Word n)
    (hq :
      QuotientGroup.mk' (otherRelatorNormalClosure R i) c =
        coordinateClass R i) :
    Reachable R (Function.update R i c) := by
  let N := otherRelatorNormalClosure R i
  letI : N.Normal := by
    unfold N otherRelatorNormalClosure sourceNormalClosure
    infer_instance

  have hmem : c / R i ∈ N := by
    apply (QuotientGroup.eq_iff_div_mem).mp
    simpa [N, coordinateClass] using hq

  have p :=
    otherRelatorNormalClosure_coordinate_reachable
      R i (h := c / R i) hmem
  simpa [N, div_eq_mul_inv, mul_assoc] using p

/-- Semantic coordinate replacement preserves every future target consequence. -/
theorem same_partial_group_class_target_iff {n : ℕ}
    (R T : Relators n) (i : Fin n) (c : Word n)
    (hq :
      QuotientGroup.mk' (otherRelatorNormalClosure R i) c =
        coordinateClass R i) :
    Reachable R T ↔ Reachable (Function.update R i c) T := by
  exact reachable_target_iff_of_reachable
    (same_partial_group_class_reachable R i c hq)

/-- Equality of semantic coordinate classes is exactly congruence modulo the
normal closure of the other relators. -/
theorem partial_group_class_eq_iff {n : ℕ}
    (R : Relators n) (i : Fin n) (a c : Word n) :
    QuotientGroup.mk' (otherRelatorNormalClosure R i) c =
        QuotientGroup.mk' (otherRelatorNormalClosure R i) a
      ↔
    c / a ∈ otherRelatorNormalClosure R i := by
  let N := otherRelatorNormalClosure R i
  letI : N.Normal := by
    unfold N otherRelatorNormalClosure sourceNormalClosure
    infer_instance
  simpa [N] using
    (QuotientGroup.eq_iff_div_mem
      (N := N) (x := c) (y := a))

end AC
