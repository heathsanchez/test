import Collatz.LawfulFutureJoin
import Collatz.CylinderCoalescence

namespace CollatzFinal

/-!
V129: one new semantic constructor forced by V128's all-clock
preferred-root selector separator (source 21 is always mapped back to 21,
while source 3 is a genuinely smaller odd 3-divisible future coalescent).

Rather than increasing a root-selector search depth, derive the smallest
UNIFORM, ALL-OFFSET relational root law. Every t>=0 has two positive ODD
3-divisible sources:
  n(t)=21+72*t,   p(t)=3+12*t<n(t)
and their REAL shortcut orbits meet at two INDEPENDENT clocks:
  T^3(n(t))=8+27*t=T^2(p(t)).

This is one infinite parametric proof constructor, not a theorem
about all odd roots, not a universal proof of Collatz termination.
The semantics are exactly the existing LawfulFutureJoin type from V123/124.
-/

theorem root21_family_forward (t : Nat) :
    iter shortcut 3 (21 + 72 * t) = 8 + 27 * t := by
  have h := SourceProduct.parity_cylinder_shift 21 3 (9 * t)
  have hb : iter shortcut 3 21 = 8 := by decide
  have hc : SourceProduct.oddCount 21 3 = 1 := by decide
  rw [hb, hc] at h
  have hpow2 : (2 : Nat) ^ 3 = 8 := by decide
  have hpow3 : (3 : Nat) ^ 1 = 3 := by decide
  rw [hpow2, hpow3] at h
  have harg : 21 + 8 * (9 * t) = 21 + 72 * t := by omega
  calc
    iter shortcut 3 (21 + 72 * t) =
        iter shortcut 3 (21 + 8 * (9 * t)) := by rw [harg]
    _ = 8 + 3 * (9 * t) := h
    _ = 8 + 27 * t := by omega

theorem root3_family_forward (t : Nat) :
    iter shortcut 2 (3 + 12 * t) = 8 + 27 * t := by
  have h := SourceProduct.parity_cylinder_shift 3 2 (3 * t)
  have hb : iter shortcut 2 3 = 8 := by decide
  have hc : SourceProduct.oddCount 3 2 = 2 := by decide
  rw [hb, hc] at h
  have hpow2 : (2 : Nat) ^ 2 = 4 := by decide
  have hpow3 : (3 : Nat) ^ 2 = 9 := by decide
  rw [hpow2, hpow3] at h
  have harg : 3 + 4 * (3 * t) = 3 + 12 * t := by omega
  calc
    iter shortcut 2 (3 + 12 * t) =
        iter shortcut 2 (3 + 4 * (3 * t)) := by rw [harg]
    _ = 8 + 9 * (3 * t) := h
    _ = 8 + 27 * t := by omega

/-- Full all-offset typed future witness, preserving ORIGINAL source
    and both independent clocks: a semantic law rather than a cached trace. -/
def root21_family_join (t : Nat) : LawfulFutureJoin :=
  { source := 21 + 72 * t
    earlier := 3 + 12 * t
    sourceClock := 3
    earlierClock := 2
    positive := by omega
    smaller := by omega
    common := (root21_family_forward t).trans (root3_family_forward t).symm }

/-- Both sources are odd positive multiples of three; the source guard is
    strict for EVERY natural t. Thus this constructor lives in the
    V127 odd-root representative domain and does not rely on 21 alone. -/
theorem root21_family_odd_three_root_certificate (t : Nat) :
    (21 + 72 * t) % 6 = 3 ∧
    (3 + 12 * t) % 6 = 3 ∧
    0 < 3 + 12 * t ∧
    3 + 12 * t < 21 + 72 * t ∧
    iter shortcut 3 (21 + 72 * t) =
      iter shortcut 2 (3 + 12 * t) := by
  refine ⟨by omega, by omega, by omega, by omega, ?_⟩
  exact (root21_family_join t).common

/-- Compiles through the unchanged V124 normalized LowerMerge interface. -/
theorem root21_family_lower_source_join (t : Nat) :
    LowerMerge shortcut (21 + 72 * t) (3 + 12 * t) :=
  (root21_family_join t).toLowerMerge

/-- Positive source in this family CANNOT be a least positive
    nonconvergent source. This is a conditional contradiction, NOT
    an assertion that all odd three-roots have such a witness. -/
theorem root21_family_not_minimal_bad (t : Nat)
    (hbad : MinimalBad (fun n => ¬ CollatzGood n) (21 + 72 * t)) :
    False :=
  (root21_family_join t).refutes_minimal_bad hbad

#print axioms root21_family_forward
#print axioms root3_family_forward
#print axioms root21_family_join
#print axioms root21_family_odd_three_root_certificate
#print axioms root21_family_lower_source_join
#print axioms root21_family_not_minimal_bad

end CollatzFinal
