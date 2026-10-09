import Collatz.RootSelectorCompletenessSeparator

namespace CollatzFinal

/-!
V129 — the minimum *warranted* relational odd-three-root class interface.

A root-class identity transports an original source to ANY legitimate
odd multiple-of-three representative, with BOTH actual meeting clocks.
It is not a source-decreasing theorem. The root may be larger than source.

Three independent protected separators reject weaker representations:
  (1) endpoint 8 has at least TWO distinct valid roots 3 and 21;
  (2) source 6 coalesces with odd root 3, but NO odd root can reach 6
      at a backwards-only clock (3-divisible reverse roots are doubling);
  (3) source 1's valid root 21 is larger than the original source.

This type may reclose future CLASS identity, but only a separate proof
of strictly earlier original source may populate LowerClassMerge.
All-positive termination remains UNKNOWN.
-/

structure OddThreeRootClassWitness (source : Nat) where
  root : Nat
  sourceClock : Nat
  rootClock : Nat
  positive : 0 < root
  residue : root % 6 = 3
  common : iter shortcut sourceClock source =
           iter shortcut rootClock root

/-- Generic all-positive class-identity admission, constructed from
    the formally qualified V127 future-coalescence domain reduction. -/
theorem root_witness_exists_for_every_positive
    (n : Nat) (hn : 0 < n) :
    Nonempty (OddThreeRootClassWitness n) := by
  obtain ⟨r,a,b,hpos,hodd,hthree,hmeet⟩ :=
    every_positive_meets_odd_three_root n hn
  exact ⟨{
    root := r
    sourceClock := a
    rootClock := b
    positive := hpos
    residue := odd_three_root_mod_six r hodd hthree
    common := hmeet }⟩

/-- Two DISTINCT certified root representations for the SAME endpoint 8. -/
def eight_from_three : OddThreeRootClassWitness 8 := {
  root := 3
  sourceClock := 0
  rootClock := 2
  positive := by decide
  residue := by decide
  common := by decide
}

def eight_from_twentyone : OddThreeRootClassWitness 8 := {
  root := 21
  sourceClock := 0
  rootClock := 3
  positive := by decide
  residue := by decide
  common := by decide
}

/-- True future-class identity is RELATIONAL, not a unique chosen root. -/
theorem endpoint_eight_has_two_distinct_root_witnesses :
    ∃ w1 w2 : OddThreeRootClassWitness 8,
      w1.root = 3 ∧ w2.root = 21 ∧ w1.root ≠ w2.root := by
  exact ⟨eight_from_three, eight_from_twentyone,
    rfl, rfl, by decide⟩

/-- A positive even 3-multiple may have a genuine root FUTURE witness
    but not a backward-only source rooted at an odd 3-multiple. -/
def six_meets_three : OddThreeRootClassWitness 6 := {
  root := 3
  sourceClock := 1
  rootClock := 0
  positive := by decide
  residue := by decide
  common := by decide
}

/-- ALL-CLOCK obstruction: a positive odd three-root cannot be a direct
    shortcut PREIMAGE of endpoint six, because the reverse tree is pure
    doubling. -/
theorem no_odd_three_root_can_reach_six
    (r k : Nat) (hoddthree : r % 6 = 3) :
    iter shortcut k r ≠ 6 := by
  intro h
  have hrmod3 : (6 : Nat) % 3 = 0 := by decide
  have hsource : r = 2 ^ k * 6 :=
    (all_preimages_of_three_multiple k r 6 hrmod3).mp h
  have heven : (2 ^ k * 6) % 2 = 0 := by omega
  have hodd : r % 2 = 1 := by omega
  rw [hsource] at hodd
  omega

/-- The two-clock obligation is genuinely necessary even for a root-class
    presentation whose future-coalescence is already certified. -/
theorem six_root_relation_needs_nonzero_source_clock :
    ∃ w : OddThreeRootClassWitness 6,
      0 < w.sourceClock ∧
      (∀ r k : Nat, r % 6 = 3 → iter shortcut k r ≠ 6) := by
  refine ⟨six_meets_three, by decide, ?_⟩
  intro r k hr
  exact no_odd_three_root_can_reach_six r k hr

/-- Class normalization is NOT lower-source progress: 1 is represented
    by root 21, which is larger than the original positive source. -/
def one_meets_twentyone : OddThreeRootClassWitness 1 := {
  root := 21
  sourceClock := 0
  rootClock := 6
  positive := by decide
  residue := by decide
  common := by decide
}

theorem root_identity_can_increase_original_source :
    ∃ w : OddThreeRootClassWitness 1, 1 < w.root := by
  exact ⟨one_meets_twentyone, by decide⟩

/-- Reusable protected separator: source21 has the smaller real root3
    despite the permanently stalled preferred-root selector. -/
theorem source21_typed_multi_root_repairs_preferred_stutter :
    (∀ k : Nat,
      preferredThreeRoot (iter shortcut k 21) = 21) ∧
    (∃ w : OddThreeRootClassWitness 21,
      w.root = 3 ∧ w.root < 21) := by
  constructor
  · exact source21_preferred_root_stutters_everywhere
  · let w : OddThreeRootClassWitness 21 := {
      root := 3
      sourceClock := 3
      rootClock := 2
      positive := by decide
      residue := by decide
      common := by decide }
    exact ⟨w, rfl, by decide⟩

#print axioms root_witness_exists_for_every_positive
#print axioms endpoint_eight_has_two_distinct_root_witnesses
#print axioms no_odd_three_root_can_reach_six
#print axioms six_root_relation_needs_nonzero_source_clock
#print axioms root_identity_can_increase_original_source
#print axioms source21_typed_multi_root_repairs_preferred_stutter

end CollatzFinal
