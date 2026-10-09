import Collatz.FirstResidualRefinement

set_option maxRecDepth 16384
set_option maxHeartbeats 2000000

namespace CollatzFinal
namespace SourceProduct

/-!
# Source 27: every possible earlier positive source avoids F(27)=83, at ALL clocks

The orbit closure is a genuine finite invariant: it is checked under the
actual shortcut transition, not a search truncated at an arbitrary time.

This rejects *every* source-p<27 reverse presentation at the fixed F(27)
endpoint, irrespective of reverse-word length. It does NOT make n=27
nonconvergent: T^59(27)=23, which supplies a later genuine lower-source
coalescence. Neither fact implies the universal Collatz conjecture.
-/

/-- The EXACT forward-invariant reachable envelope of all 1≤p<27.
    Its greatest element is 80; in particular 83 is absent. -/
private def orbitBelow27 : List Nat :=
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 32, 35, 38, 40, 44, 53, 80]

private theorem orbitBelow27_contains_all_initial (p : Nat)
    (hpos : 0 < p) (hsmall : p < 27) :
    p ∈ orbitBelow27 := by
  simp only [orbitBelow27, List.mem_cons, List.not_mem_nil, or_false]
  omega

/-- Every one of these 34 concrete elements maps back into the envelope.
    The long induction is avoided by checking this one complete set. -/
private theorem orbitBelow27_closed (p : Nat)
    (hmem : p ∈ orbitBelow27) :
    shortcut p ∈ orbitBelow27 := by
  simp only [orbitBelow27, List.mem_cons, List.not_mem_nil, or_false] at hmem
  rcases hmem with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
  all_goals decide

private theorem orbitBelow27_iter (p k : Nat)
    (hmem : p ∈ orbitBelow27) :
    iter shortcut k p ∈ orbitBelow27 := by
  induction k generalizing p with
  | zero => simpa [iter] using hmem
  | succ k ih =>
      change iter shortcut k (shortcut p) ∈ orbitBelow27
      exact ih (shortcut p) (orbitBelow27_closed p hmem)

/-- A mathematically ALL-TIME negative result for the first
    previously-unresolved fixed-phase source.  F(27)=83 cannot be
    reached by ANY positive smaller source at ANY shortcut clock. -/
theorem no_smaller_positive_source_hits_F27
    (p k : Nat) (hpos : 0 < p) (hsmall : p < 27) :
    iter shortcut k p ≠ 83 := by
  have hin : iter shortcut k p ∈ orbitBelow27 :=
    orbitBelow27_iter p k
      (orbitBelow27_contains_all_initial p hpos hsmall)
  intro he
  rw [he] at hin
  exact (show 83 ∉ orbitBelow27 by decide) hin

/-- All-clock elimination of the entire fixed endpoint F(27), not just
    reverse-word budgets 12, 14 or 100. -/
theorem F27_has_no_earlier_positive_preimage :
    ¬ ∃ p k : Nat, 0 < p ∧ p < 27 ∧ iter shortcut k p = 83 := by
  intro h
  obtain ⟨p, k, hp, hsmall, hit⟩ := h
  exact no_smaller_positive_source_hits_F27 p k hp hsmall hit

/-- But the same original source DOES have a strictly smaller
    asynchronous coalescent through a LATER real forward endpoint. -/
theorem source27_later_joins_23 :
    LowerMerge shortcut 27 23 := by
  refine ⟨by decide, 59, 0, ?_⟩
  simpa [iter] using source27_first_below_at_59

/-- The complete separator: rigid F(27) reclosure is impossible for
    smaller sources, while a later original-source join already exists. -/
theorem source27_F_obstruction_and_late_join :
    (¬ ∃ p k : Nat, 0 < p ∧ p < 27 ∧
      iter shortcut k p = 83) ∧
    LowerMerge shortcut 27 23 :=
  ⟨F27_has_no_earlier_positive_preimage, source27_later_joins_23⟩


/-- A stronger *all-source-clock* lower bound: before shortcut time 59
    the source 27 has never entered the forward-invariant closure of
    any smaller positive starting source. -/
private theorem source27_no_smaller_orbit_contact_before59
    (i : Nat) (hi : i < 59) :
    iter shortcut i 27 ∉ orbitBelow27 := by
  have hfinite :
      ∀ k : Fin 59, iter shortcut k.val 27 ∉ orbitBelow27 := by
    decide
  exact hfinite ⟨i, hi⟩

/-- Every earlier positive source and EVERY predecessor clock are
    excluded until the 59th ACTUAL forward step of 27. This is
    stronger than forbidding a reverse word into F(27)=83. -/
theorem source27_no_positive_lower_meeting_before59
    (p i j : Nat)
    (hpos : 0 < p) (hsmall : p < 27) (hi : i < 59) :
    iter shortcut i 27 ≠ iter shortcut j p := by
  intro heq
  have horbit : iter shortcut j p ∈ orbitBelow27 :=
    orbitBelow27_iter p j
      (orbitBelow27_contains_all_initial p hpos hsmall)
  have hnot := source27_no_smaller_orbit_contact_before59 i hi
  apply hnot
  rw [heq]
  exact horbit

/-- The earliest possible original-source clock for a genuine smaller
    future coalescence from 27 is EXACTLY 59, attained at p=23, j=0. -/
theorem source27_first_lower_meeting_exactly59 :
    (∀ p i j : Nat,
      0 < p → p < 27 → i < 59 →
      iter shortcut i 27 ≠ iter shortcut j p) ∧
    (∃ p j : Nat,
      0 < p ∧ p < 27 ∧
      iter shortcut 59 27 = iter shortcut j p) := by
  constructor
  · intro p i j hp hsmall hi
    exact source27_no_positive_lower_meeting_before59 p i j hp hsmall hi
  · refine ⟨23, 0, by decide, by decide, ?_⟩
    simpa [iter] using source27_first_below_at_59

#print axioms source27_no_positive_lower_meeting_before59
#print axioms source27_first_lower_meeting_exactly59

#print axioms no_smaller_positive_source_hits_F27
#print axioms F27_has_no_earlier_positive_preimage
#print axioms source27_later_joins_23
#print axioms source27_F_obstruction_and_late_join

end SourceProduct
end CollatzFinal
