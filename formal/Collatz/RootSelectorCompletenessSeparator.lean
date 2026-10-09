import Collatz.OddThreeRootQuotient

namespace CollatzFinal

/-!
V128 — a *universal all-clock* counterexample to treating a chosen
3-root normalizer as a source-lowering function.

The deterministic root selector below is one exact constructive
section of the V126 6-rule mod-9 family. It selects a valid odd positive
3-divisible ancestor for every non-3-divisible positive endpoint.

For original source 21, EVERY future endpoint's selected root equals 21
(including the eventual 1↔2 terminal cycle). Yet 21 and the *smaller*
odd three-root 3 actually coalesce: T^3(21)=T^2(3)=8.

Therefore root selection is NOT a complete minimal-class
representative and is NOT a LowerMerge progress detector.
The warranted repair is RELATIONAL MULTI-ROOT future witnesses
with two clocks and exact protected source authority.
No Collatz QED is claimed.
-/

/-- A deterministic SOURCE-CLASS REPRESENTATIVE SELECTOR extracted
from the six universally valid V126 mod-9 affine cases.
The index is intentional and cannot be called a minimum. -/
def preferredThreeRoot (n : Nat) : Nat :=
  if n % 3 = 0 then n
  else if n % 9 = 1 then 21 + 192 * (n / 9)
  else if n % 9 = 2 then 21 + 96 * (n / 9)
  else if n % 9 = 4 then 21 + 48 * (n / 9)
  else if n % 9 = 5 then 3 + 6 * (n / 9)
  else if n % 9 = 7 then 9 + 12 * (n / 9)
  else 21 + 24 * (n / 9)

/-- Actual deterministic seven-state source-21 orbit envelope:
    21 → 32 → 16 → 8 → 4 → 2 → 1 → 2 → 1 ... -/
private def source21Envelope : List Nat :=
  [21,32,16,8,4,2,1]

private theorem source21_start_in_envelope :
    21 ∈ source21Envelope := by decide

private theorem source21_envelope_closed (n : Nat)
    (h : n ∈ source21Envelope) :
    shortcut n ∈ source21Envelope := by
  simp only [source21Envelope, List.mem_cons, List.not_mem_nil, or_false] at h ⊢
  rcases h with rfl | rfl | rfl | rfl | rfl | rfl | rfl
  all_goals decide

private theorem source21_all_forward_endpoints_in_envelope
    (k : Nat) :
    iter shortcut k 21 ∈ source21Envelope := by
  induction k with
  | zero =>
      exact source21_start_in_envelope
  | succ k ih =>
      have hlast :
          iter shortcut (k + 1) 21 =
            shortcut (iter shortcut k 21) := by
        simpa [iter] using (iter_add shortcut k 1 21)
      rw [hlast]
      exact source21_envelope_closed _ ih

private theorem selector_maps_source21_envelope_to_same_root
    (n : Nat) (h : n ∈ source21Envelope) :
    preferredThreeRoot n = 21 := by
  simp only [source21Envelope, List.mem_cons, List.not_mem_nil, or_false] at h
  rcases h with rfl | rfl | rfl | rfl | rfl | rfl | rfl
  all_goals decide

/-- The canonical source21 root selector *stutters at ALL natural clocks*,
    not merely for a bounded number of transitions. -/
theorem source21_preferred_root_stutters_everywhere
    (k : Nat) :
    preferredThreeRoot (iter shortcut k 21) = 21 := by
  exact selector_maps_source21_envelope_to_same_root _
    (source21_all_forward_endpoints_in_envelope k)

/-- Two independent protected actual clocks witness a LOWER odd 3-root.
    This is a genuine consequence missing from the selected representative. -/
theorem source21_has_earlier_odd_three_root_join :
    0 < 3 ∧ 3 < 21 ∧ 3 % 6 = 3 ∧
    iter shortcut 3 21 = iter shortcut 2 3 := by
  decide

/-- All-clock frozen-grammar impossibility + admitted class-merger witness.
    A ROOT SECTION is not the root-class MINIMUM. -/
theorem preferred_root_grammar_not_lower_merge_complete :
    (∀ k : Nat,
       preferredThreeRoot (iter shortcut k 21) = 21) ∧
    (∃ p a b : Nat,
       0 < p ∧ p < 21 ∧ p % 6 = 3 ∧
       iter shortcut a 21 = iter shortcut b p) := by
  constructor
  · exact source21_preferred_root_stutters_everywhere
  · refine ⟨3,3,2,?_⟩
    exact source21_has_earlier_odd_three_root_join

#print axioms source21_preferred_root_stutters_everywhere
#print axioms source21_has_earlier_odd_three_root_join
#print axioms preferred_root_grammar_not_lower_merge_complete

end CollatzFinal
