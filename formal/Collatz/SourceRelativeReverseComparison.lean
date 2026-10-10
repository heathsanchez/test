import Collatz.ActualRationalCentreDrift

namespace CollatzFinal
namespace SourceProduct

/-!
V149 — SOUND PROTECTED-FUTURE REVERSE COMPARISON.

Goal: compare source-attached proof candidates in a way that
CONSTRUCTS a verified strictly smaller positive source p, with
T^sourceClock(n)=T^reverseClock(p).

The semantic mistake to avoid: ordering two residual states or
equating their rational source centres does not automatically
produce a new earlier-source coalescence witness.

The constructive comparison uses exact reverse shortcut steps:
  EVEN inverse: p <- 2*p;
  ODD inverse:  p <- q whenever 3*q+1=2*p.
Those are arithmetic/Lean-certified, not free source classes or
assumed base endpoint meetings.

Every reverse chain is inductively checked, gives TRUE forward
semantics T^b(q)=y, and is safe under every common future suffix.
A source-relative strict cap q<n converts it into LowerMerge.

A safe dominance relation can prune reverse candidates only when
they share the SAME actual target endpoint y: source p<=q dominates
candidate q for existence of a smaller positive source, while
each actual reverse clock remains independent.

Negative controls preserve:
 - V128 source21->root3 (independent clocks 3,2),
 - V106 ascending actual source9->root7 (clocks 6,4),
 - source1 terminal: no smaller positive source even though its
   pure-even reverse cone is infinite and totally comparable,
 - V147/V148 static same-rational-centre observations do NOT
   commute with naive future even-step transitions.

What is NOT shown: that any hypothetical least positive bad source
ever produces an admissible reverse candidate, or that comparability
of all reverse nodes entails such an admissible source. A generic
well-quasi-order does NOT supply that numerical source cap.

GLOBAL COLLATZ UNKNOWN — NO QED. V134 controller unchanged.
-/

/-- A checkable, source-independent TRUE reverse step. -/
theorem v149_even_inverse_shortcut (p : Nat) :
    shortcut (2*p) = p := by
  have hpar : (2*p)%2=0 := by omega
  simp [shortcut,hpar]
  omega

/-- Exact odd reverse step: 3*q+1=2*p forces q to be odd and
    then computes the genuine shortcut endpoint p. -/
theorem v149_odd_inverse_shortcut (p q : Nat)
    (heq : 3*q+1=2*p) :
    shortcut q = p := by
  have hodd : q%2=1 := by omega
  simp [shortcut,hodd]
  omega

/-- The reverse certificate grammar contains no asserted meeting
    with the original source. Only true local inverse arithmetic. -/
inductive V149ReverseTrace (y : Nat) : Nat → Nat → Prop where
  | here : V149ReverseTrace y y 0
  | even {p b : Nat} :
      V149ReverseTrace y p b →
      V149ReverseTrace y (2*p) (b+1)
  | odd {p q b : Nat} :
      V149ReverseTrace y p b →
      3*q+1=2*p →
      V149ReverseTrace y q (b+1)

/-- Every certificate really executes under the original Nat
    shortcut map. The proof never assumes Collatz convergence. -/
theorem v149_reverse_trace_sound
    {y p b : Nat} (h : V149ReverseTrace y p b) :
    iter shortcut b p = y := by
  induction h with
  | here =>
      rfl
  | even h ih =>
      simpa only [iter, v149_even_inverse_shortcut] using ih
  | odd h heq ih =>
      have hs := v149_odd_inverse_shortcut _ _ heq
      simpa only [iter, hs] using ih

/-- Under ANY real future continuation of the shared endpoint,
    the reverse chain preserves its independently qualified clock. -/
theorem v149_reverse_trace_preserves_every_future_suffix
    {y p b : Nat} (h : V149ReverseTrace y p b)
    (k : Nat) :
    iter shortcut (b+k) p = iter shortcut k y := by
  rw [iter_add, v149_reverse_trace_sound h]

/-- A proof-bearing inverse candidate. Positivity is deliberately
    not inferred from mere quotient or future-class identity. -/
structure V149InverseCandidate (y : Nat) where
  source : Nat
  backClock : Nat
  reverse : V149ReverseTrace y source backClock
  positive : 0 < source

def v149SourceAdmissible
    (n y : Nat) (w : V149InverseCandidate y) : Prop :=
  w.source < n

/-- This is the actual witness-producing comparison theorem:
    exact source endpoint + exact inverse grammar + strict ORIGINAL
    source guard -> true LowerMerge with both independent clocks.
    No meeting on the p-side was postulated. -/
theorem v149_admissible_inverse_constructs_lower_merge
    (n i y : Nat)
    (hendpoint : iter shortcut i n = y)
    (w : V149InverseCandidate y)
    (hcap : v149SourceAdmissible n y w) :
    LowerMerge shortcut n w.source := by
  refine ⟨hcap, i, w.backClock, ?_⟩
  rw [hendpoint]
  exact (v149_reverse_trace_sound w.reverse).symm

/-- Real continuation simulation: every suffix preserves the
    original source, the independent clocks and the common endpoint. -/
theorem v149_admissible_inverse_preserves_all_future_meetings
    (n i y : Nat)
    (hendpoint : iter shortcut i n = y)
    (w : V149InverseCandidate y)
    (_hcap : v149SourceAdmissible n y w)
    (k : Nat) :
    iter shortcut (i+k) n =
      iter shortcut (w.backClock+k) w.source := by
  rw [iter_add, hendpoint]
  exact (v149_reverse_trace_preserves_every_future_suffix
    w.reverse k).symm

/-- A future-safe candidate comparison: when two true inverse
    certificates lead to the SAME y, the smaller positive source
    dominates for all ORIGINAL caps n. No clock equivalence claimed. -/
def v149ReverseDominates
    {y : Nat} (lower upper : V149InverseCandidate y) : Prop :=
  lower.source ≤ upper.source

theorem v149_dominance_preserves_every_source_cap
    {y : Nat} (lower upper : V149InverseCandidate y)
    (hdom : v149ReverseDominates lower upper) :
    ∀ n : Nat,
      v149SourceAdmissible n y upper →
      v149SourceAdmissible n y lower := by
  intro n hcap
  exact Nat.lt_of_le_of_lt hdom hcap

/-- Comparison of two proof-bearing candidates can thus create a
    true lower-class merge for a smaller retained source without
    replaying the longer dominated candidate. -/
theorem v149_dominated_reverse_candidate_creates_lower_merge
    (n i y : Nat)
    (hendpoint : iter shortcut i n = y)
    (lower upper : V149InverseCandidate y)
    (hdom : v149ReverseDominates lower upper)
    (hupper : v149SourceAdmissible n y upper) :
    LowerMerge shortcut n lower.source :=
  v149_admissible_inverse_constructs_lower_merge
    n i y hendpoint lower
    (v149_dominance_preserves_every_source_cap lower upper hdom
      n hupper)

/-- This is the source-indexed contradiction with a hypothetical
    LEAST positive counterexample. All arithmetic premises
    genuinely produce a full LowerMerge certificate. -/
theorem v149_qualified_comparison_refutes_minimal_positive_bad
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (i y : Nat) (hendpoint : iter shortcut i n = y)
    (w : V149InverseCandidate y)
    (hcap : v149SourceAdmissible n y w) : False := by
  have hm := v149_admissible_inverse_constructs_lower_merge
    n i y hendpoint w hcap
  exact (positive_minimal_no_lower_merge hmin w.source
    w.positive) hm

/-- The V128 root-selection stutter is repaired CONSTRUCTIVELY:
    T^3(21)=8 and the true reverse chain 3->5->8 provides
    root 3 at independent back-clock 2, without a base meeting axiom. -/
theorem v149_source21_to_root3_constructive :
    LowerMerge shortcut 21 3 := by
  have hend : iter shortcut 3 21 = 8 := by decide
  have h8 : V149ReverseTrace 8 8 0 := .here
  have h5 : V149ReverseTrace 8 5 1 :=
    .odd h8 (by decide)
  have h3 : V149ReverseTrace 8 3 2 :=
    .odd h5 (by decide)
  let w : V149InverseCandidate 8 :=
    ⟨3,2,h3,(by decide)⟩
  exact v149_admissible_inverse_constructs_lower_merge
    21 3 8 hend w (by decide)

/-- The ascending-sign V106 real source9 episode is not discarded:
    T^6(9)=13, and an independently certified four-step inverse
    chain 7->11->17->26->13 constructs a smaller p=7. -/
theorem v149_source9_to_root7_constructive :
    LowerMerge shortcut 9 7 := by
  have hend : iter shortcut 6 9 = 13 := by decide
  have h13 : V149ReverseTrace 13 13 0 := .here
  have h26 : V149ReverseTrace 13 26 1 := .even h13
  have h17 : V149ReverseTrace 13 17 2 :=
    .odd h26 (by decide)
  have h11 : V149ReverseTrace 13 11 3 :=
    .odd h17 (by decide)
  have h7 : V149ReverseTrace 13 7 4 :=
    .odd h11 (by decide)
  let w : V149InverseCandidate 13 :=
    ⟨7,4,h7,(by decide)⟩
  exact v149_admissible_inverse_constructs_lower_merge
    9 6 13 hend w (by decide)

/-- A comparable pure-doubling reverse chain exists for EVERY
    endpoint y at all depths. This by itself has no source cap. -/
theorem v149_pure_even_reverse_chain
    (y : Nat) :
    ∀ j : Nat, V149ReverseTrace y (2^j * y) j := by
  intro j
  induction j with
  | zero =>
      simpa using (V149ReverseTrace.here : V149ReverseTrace y y 0)
  | succ j ih =>
      have hd : (2 : Nat)^(j+1)*y = 2*(2^j*y) := by
        simp [Nat.pow_succ, Nat.mul_assoc,
          Nat.mul_comm, Nat.mul_left_comm]
      rw [hd]
      exact .even ih

/-- Exact rank-only falsifier: even reverse witnesses form an
    infinite monotonically comparable chain, but if n≤y, not a
    single member is a strictly smaller source than n. This cannot
    be repaired by an abstract Nat WQO on candidate values. -/
theorem v149_comparable_even_chain_need_not_produce_lower_source
    (n y : Nat) (hcap : n ≤ y) :
    ∀ j : Nat,
      V149ReverseTrace y (2^j*y) j ∧
      n ≤ 2^j*y ∧
      2^j*y ≤ 2^(j+1)*y := by
  intro j
  have hpositive : 0 < (2 : Nat)^j :=
    Nat.pow_pos (by decide)
  have hfirst : y ≤ 2^j*y := by
    have hh : 1 ≤ (2 : Nat)^j := by omega
    have h := Nat.mul_le_mul_right y hh
    simpa only [Nat.one_mul] using h
  have hsecond : 2^j*y ≤ 2^(j+1)*y := by
    have hh : (2 : Nat)^j ≤ 2^j*2 := by omega
    have h := Nat.mul_le_mul_right y hh
    simpa only [Nat.pow_succ] using h
  exact ⟨v149_pure_even_reverse_chain y j,
    Nat.le_trans hcap hfirst, hsecond⟩

/-- A protected terminal boundary: source1 really has endpoint2,
    but no positive predecessor of endpoint2 can have p<1.
    Comparable reverse states alone cannot prove Collatz or
    a smaller-source witness here. -/
theorem v149_terminal_one_refuses_nonpositive_rank_shortcut
    (w : V149InverseCandidate 2) :
    ¬ v149SourceAdmissible 1 2 w := by
  intro hcap
  have hp := w.positive
  omega

/-- V147 equality of static rational source observations does NOT
    create a future-safe simulation under naive even offset updates.
    The two source certificates have equal -13/9 centres, but the
    unscaled updates immediately separate them. V148 warns why
    hidden scaling/clock information must be retained. -/
theorem v149_rational_static_class_not_untyped_future_simulation :
    v147CentreEquivalent v147CentreNineThirteen
      v147CentreTwentySevenThirtyNine ∧
    ¬ v147CentreEquivalent
      (⟨9,14,by decide⟩ : RationalSourceCentreV147)
      (⟨27,40,by decide⟩ : RationalSourceCentreV147) := by
  constructor
  · exact v147_positive_rational_equivalence
  · intro h
    change 27*14=9*40 at h
    omega

#print axioms v149_even_inverse_shortcut
#print axioms v149_odd_inverse_shortcut
#print axioms v149_reverse_trace_sound
#print axioms v149_reverse_trace_preserves_every_future_suffix
#print axioms v149_admissible_inverse_constructs_lower_merge
#print axioms v149_admissible_inverse_preserves_all_future_meetings
#print axioms v149_dominance_preserves_every_source_cap
#print axioms v149_dominated_reverse_candidate_creates_lower_merge
#print axioms v149_qualified_comparison_refutes_minimal_positive_bad
#print axioms v149_source21_to_root3_constructive
#print axioms v149_source9_to_root7_constructive
#print axioms v149_pure_even_reverse_chain
#print axioms v149_comparable_even_chain_need_not_produce_lower_source
#print axioms v149_terminal_one_refuses_nonpositive_rank_shortcut
#print axioms v149_rational_static_class_not_untyped_future_simulation

end SourceProduct
end CollatzFinal
