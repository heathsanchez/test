import AC
import Mathlib.GroupTheory.QuotientGroup.Basic

/-!
# The standard Andrews--Curtis presentation is trivial

This closes the semantic base case used by constructive proof families:
the normal closure of the standard relators is the whole ambient free group,
so the corresponding presented group is subsingleton at every finite rank.
-/

namespace AC

/-- The standard tuple normally generates the entire ambient free group. -/
theorem standard_normalClosure_eq_top (n : ℕ) :
    Subgroup.normalClosure (Set.range (standard n)) =
      (⊤ : Subgroup (Word n)) := by
  change
    Subgroup.normalClosure
        (Set.range (FreeGroup.of : Fin n → FreeGroup (Fin n))) =
      (⊤ : Subgroup (FreeGroup (Fin n)))
  apply top_unique
  rw [← FreeGroup.closure_range_of (Fin n)]
  exact Subgroup.closure_le_normalClosure

/-- The official standard presentation presents the trivial group at every
finite rank, including rank zero. -/
theorem standard_presentsTrivialGroup (n : ℕ) :
    PresentsTrivialGroup (standard n) := by
  unfold PresentsTrivialGroup PresentedGroup
  rw [standard_normalClosure_eq_top n]
  exact QuotientGroup.subsingleton_quotient_top

end AC
