import Collatz.SourceSpecificFutureGuard
import Collatz.GuardedInverseRuleClosure

namespace CollatzFinal
namespace SourceProduct

/-!
V186 — FLASH RECLOSURE OF QUALIFIED SOURCE-INDEX AND FUTURE-PREFIX
WARRANTS. This module imports and COMPOSES, without re-proving,
the independent V179 sparse-source normal-form capability, the V184
never-below-original-source all-prefix odd barrier, and V185's exact
+1 original-source coefficient event guard.

The CONSEQUENTIAL intersection is smaller than the information
provided by any single module:
  hypothetical LEAST bad n >=8 must be V178-IRREDUCIBLE AND
  V180 guarded-inverse-IRREDUCIBLE,
  have oddCount(n,5r)>=3r+1 for EVERY positive r, and
  satisfy 2^k*n^a <= (3*n+1)^a for EVERY k.

NONE of these individual or joint necessary conditions is shown
impossible for positive n; there is no global Collatz QED.

Separate elementary combinatorial accounting, using the V161
finite-parity word correspondence, shows the set of sources
satisfying ALL 5r odd-prefix constraints has NATURAL DENSITY ZERO.
An exceptional single integer may still be in a zero-density set.
The all-r combinatorial inequality is audited independently but
not claimed as a Lean theorem in this module.

This is exactly the protected-future global reclosure and warranted
minimum representation prescribed by the Metalogic research law:
preserve original Nat source, actual clocks, future class and
source-index witnesses. No further syntactic state is invented.
-/

/-- Small actual positive sources have independently replayable
terminal receipts; no unknown source enters by numerical threshold. -/
theorem v186_all_positive_sources_below_eight_are_good
    (n : Nat) (hpos : 0<n) (hsmall : n<8) :
    CollatzGood n := by
  have hCases : n=1 ∨ n=2 ∨ n=3 ∨ n=4 ∨
      n=5 ∨ n=6 ∨ n=7 := by omega
  rcases hCases with h|h|h|h|h|h|h
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩
  · subst n
    exact ⟨12, by decide⟩

/-- Every hypothetical least bad POSITIVE natural source must
therefore satisfy the source-height guard used by V184. -/
theorem v186_hypothetical_least_bad_at_least_eight
    (n : Nat) (hbad : MinimalBad PositiveBad n) :
    8<=n := by
  apply Classical.byContradiction
  intro hnot
  have hsmall : n<8 := by omega
  have hpositive : 0<n := hbad.1.1
  have hgood :=
    v186_all_positive_sources_below_eight_are_good
      n hpositive hsmall
  exact hbad.1.2 hgood

/-- A hypothetical least bad original natural source cannot be
reduced by ANY of the 205 already-qualified V178 all-offset source
rules: every such rule supplies a genuine STRICTLY earlier positive
source meeting, which protected minimality forbids. -/
theorem v186_hypothetical_least_bad_is_V178_irreducible
    (n : Nat) (hbad : MinimalBad PositiveBad n) :
    ¬ V179Reducible n := by
  intro hred
  obtain ⟨p,hp,hlt,hm⟩ :=
    v179_reducible_has_smaller_two_clock_witness hred
  obtain ⟨i,j,hEq⟩ := hm
  exact
    (minimal_positive_bad_no_earlier_source_meeting
      hbad p i j hp hlt) hEq

/-- Genuine V180 guarded-odd inverse reducibility, carrying the
29 separately kernel-checked original-source rules as a portable
capability bank. This is distinct from V178's forward affine bank. -/
def V186InverseReducible (n : Nat) : Prop :=
  ∃ r : V180CertifiedInverseSeed, r ∈ v180GuardedInverseBank ∧
    ∃ w : Nat,
      n = r.source + 2^(r.priorClock+1)*w

/-- The source-specific V180 inverse consequences are not recycled
uncritically: the verified constructor proves each such source has
a STRICTLY lower genuine positive two-clock companion, contradicting
LEAST bad status. No assumed convergence of companion. -/
theorem v186_hypothetical_least_bad_is_V180_irreducible
    (n : Nat) (hbad : MinimalBad PositiveBad n) :
    ¬ V186InverseReducible n := by
  intro hred
  obtain ⟨r,_hMember,w,hSource⟩ := hred
  subst n
  exact (v180_inverse_seed_excludes_least_bad r w) hbad

/-- THE independently checkable Metalogic joint-source residual:
all three protected source/future constraints hold simultaneously
for any hypothetical least positive BAD original Nat source.

This is an honest necessary condition, NOT a nonexistence proof.
It must be tested as a JOINT consequence rather than treating source
elimination, finite parity rarity or affine growth independently. -/
theorem v186_least_bad_joint_protected_future_residual
    (n : Nat) (hbad : MinimalBad PositiveBad n) :
    8<=n ∧ ¬ V179Reducible n ∧ ¬ V186InverseReducible n ∧
    (∀ r : Nat, 0<r →
       3*r+1 <= oddCount n (5*r)) ∧
    (∀ k : Nat,
       2^k*n^(oddCount n k) <=
         (3*n+1)^(oddCount n k)) := by
  have hEight :=
    v186_hypothetical_least_bad_at_least_eight n hbad
  refine ⟨hEight,
    v186_hypothetical_least_bad_is_V178_irreducible n hbad,
    v186_hypothetical_least_bad_is_V180_irreducible n hbad,
    ?_, ?_⟩
  · intro r hr
    exact
      v184_least_bad_perpetual_three_fifths_odd
        n r hbad hEight hr
  · intro k
    exact v185_least_bad_source_exact_all_clock_power n k hbad

/-- Protected status stays explicit, even though an arbitrary
irreducible representative may be terminal or nonterminal.
No algorithmically generated class label is assumed omniscient. -/
theorem v186_irreducible_future_equivalence_preserves_good
    {n p : Nat} (h : V155FutureMeet n p) :
    CollatzGood n ↔ CollatzGood p :=
  v179_future_meet_preserves_good h

#print axioms v186_all_positive_sources_below_eight_are_good
#print axioms v186_hypothetical_least_bad_at_least_eight
#print axioms v186_hypothetical_least_bad_is_V178_irreducible
#print axioms v186_hypothetical_least_bad_is_V180_irreducible
#print axioms v186_least_bad_joint_protected_future_residual
#print axioms v186_irreducible_future_equivalence_preserves_good

end SourceProduct
end CollatzFinal
