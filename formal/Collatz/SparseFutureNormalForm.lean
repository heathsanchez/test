import Collatz.CompactLeastBadCandidateSieve

namespace CollatzFinal
namespace SourceProduct

/-!
V179 — TOTAL, SOURCE-FAITHFUL FUTURE-CLASS NORMALIZATION.

For EVERY genuine positive source n, the 205 all-offset certified
V178 rules yield a terminating source-index descent procedure:
if n belongs to one of the source-cap-guarded arithmetic
progressions, construct the actual smaller source p with
T^i(n)=T^j(p), then repeat. Every reduction strictly lowers the
positive original source, so infinite reduction chains are impossible.

Lean proves:
  For ALL n>0, there is a positive irreducible p<=n,
  sharing a genuine two-clock future with n, with proof lineage
  assembled by transitivity of actual clocks.

This is UNIVERSAL ACCOUNTING and non-circular compression, NOT
UNIVERSAL TERMINATION: p may be bad. Its irreducibility is only
relative to this finite certified V178 grammar. The exact
independent periodic audit proves about 97.634% of sufficiently
large candidate-source positions are reducible by the 205-bank,
leaving 70,638 residual positions per period, infinitely many.

The conditional claim 'if every irreducible p converges, then
Collatz' is equivalent to the original conjecture; it is NOT a
missing theorem discharged in this module.

GLOBAL COLLATZ UNKNOWN. NO QED.
-/

/-- Genuine source-index reducibility by one of the kernel
    qualified finite, all-offset V178 meeting certificates. -/
def V179Reducible (n : Nat) : Prop :=
  ∃ r : V178CertifiedRule, r ∈ v178CompactBank ∧
    ∃ w : Nat,
      n = r.source + 2^r.sourceClock *
          (3^(oddCount r.earlier r.earlierClock)*w)

/-- Every permitted reduction meets a STRICTLY LOWER POSITIVE
    source at independently genuine clocks. -/
theorem v179_reducible_has_smaller_two_clock_witness
    {n : Nat} (h : V179Reducible n) :
    ∃ p : Nat,
      0 < p ∧ p < n ∧ V155FutureMeet n p := by
  obtain ⟨r,_hr,w,hSource⟩ := h
  subst n
  have hm := v178_rule_all_offsets_have_real_lower_merge r w
  obtain ⟨hlt,i,j,hMeet⟩ := hm
  let p := r.earlier + 2^r.earlierClock *
    (3^(oddCount r.source r.sourceClock)*w)
  have hp : 0<p := by
    dsimp [p]
    have hpositive := r.earlierPositive
    omega
  exact ⟨p,hp,hlt,⟨i,j,hMeet⟩⟩

/-- No source can traverse an infinite descending sequence of
    actual original-source indices. All positive sources have a
    certified irreducible normal form WITHOUT assuming Collatz. -/
theorem v179_every_positive_source_has_sparse_normal_form :
    ∀ n : Nat, 0<n →
      ∃ p : Nat, 0<p ∧ p≤n ∧ ¬ V179Reducible p ∧
        V155FutureMeet n p := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
      intro hn
      classical
      by_cases hred : V179Reducible n
      · obtain ⟨p,hp,hlt,hmeet⟩ :=
          v179_reducible_has_smaller_two_clock_witness hred
        obtain ⟨q,hq,hqle,hqnot,hpq⟩ := ih p hlt hp
        refine ⟨q,hq,?_,hqnot,?_⟩
        · omega
        · exact v155_future_meet_trans hmeet hpq
      · exact ⟨n,hn,Nat.le_refl n,hred,
          v155_future_meet_refl n⟩

/-- A genuine two-clock normal form PRESERVES convergence status
    in both directions, even when neither side has a certificate.
    This does not decide which status is true. -/
theorem v179_future_meet_preserves_good
    {n p : Nat} (hm : V155FutureMeet n p) :
    CollatzGood n ↔ CollatzGood p := by
  constructor
  · intro hn
    have hn1 :=
      (v155_future_meets_one_iff_good n).mpr hn
    have hp1 :=
      v155_future_meet_trans
        (v155_future_meet_symm hm) hn1
    exact (v155_future_meets_one_iff_good p).mp hp1
  · intro hp
    have hp1 :=
      (v155_future_meets_one_iff_good p).mpr hp
    have hn1 := v155_future_meet_trans hm hp1
    exact (v155_future_meets_one_iff_good n).mp hn1

/-- Complete all-source preservation of semantic outcome:
    each n has a smaller-or-equal irreducible true-future
    representative p, and GOOD(n) IFF GOOD(p). -/
theorem v179_total_positive_future_outcome_normalization
    (n : Nat) (hn : 0<n) :
    ∃ p : Nat,
      0<p ∧ p≤n ∧ ¬ V179Reducible p ∧
      (CollatzGood n ↔ CollatzGood p) := by
  obtain ⟨p,hp,hlt,hnot,hm⟩ :=
    v179_every_positive_source_has_sparse_normal_form n hn
  exact ⟨p,hp,hlt,hnot,
    v179_future_meet_preserves_good hm⟩

/-- Any putative bad source is forced to have a BAD irreducible
    representative: this is a sharp arithmetic *reduction* of
    the residual, not a contradiction or proof it is empty. -/
theorem v179_any_bad_source_funnels_to_bad_irreducible
    (n : Nat) (hbad : PositiveBad n) :
    ∃ p : Nat, 0<p ∧ p≤n ∧ PositiveBad p ∧
      ¬ V179Reducible p := by
  obtain ⟨p,hp,hlt,hnot,heq⟩ :=
    v179_total_positive_future_outcome_normalization n hbad.1
  have hbadp : ¬ CollatzGood p := by
    intro hpGood
    exact hbad.2 (heq.mpr hpGood)
  exact ⟨p,hp,hlt,⟨hp,hbadp⟩,hnot⟩

#print axioms v179_reducible_has_smaller_two_clock_witness
#print axioms v179_every_positive_source_has_sparse_normal_form
#print axioms v179_future_meet_preserves_good
#print axioms v179_total_positive_future_outcome_normalization
#print axioms v179_any_bad_source_funnels_to_bad_irreducible

end SourceProduct
end CollatzFinal
