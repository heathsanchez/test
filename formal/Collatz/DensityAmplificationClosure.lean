import Collatz.SourceRelativeReverseComparison

namespace CollatzFinal
namespace SourceProduct

/-!
V150 — DENSITY-AMPLIFICATION TO CERTIFIED EXCEPTIONAL-MASS INTERFACE.

EXTERNAL MATHEMATICAL INPUT (not claimed locally kernel re-proved):
Lech Mazur (2026-09-06), "Positive Lower Density of Collatz
Predecessors", ProofAtlas, states that for every positive a with
3 ∤ a, ORDINARY Collatz predecessors of a have positive lower
natural density. The actual external theorem uses Real c>0; our
discrete V150PredecessorAmplifier contract below demands a
corresponding positive natural denominator q. The translation from
the external theorem and a genuine independent source build is
NOT supplied in V150. There is NO new axiom or sorry for it.

V150 kernel-proves:
  (1) ordinary predecessor n->a preserves BADNESS in the shortcut
      map when a is shortcut-bad (unlike false equality of arbitrary
      ordinary and shortcut predecessor sets);
  (2) a hypothetical minimal positive bad n is ODD, and its genuine
      next shortcut state a=T(n) is itself bad and ALWAYS 2 mod3;
      this discharges the external theorem's 3-nondivisibility guard;
  (3) exact finite-count monotonicity from predecessor population
      to bad population;
  (4) positive-density bad mass is incompatible with a universally
      certified *dyadic* exceptional-mass envelope bounded by
      k*|E_k| <= 2^k for every sufficiently large k;
  (5) a typed terminal/lower-merge certificate grammar carries
      evidence all the way to the true terminal class, rather than
      miscounting a mere lower-source meeting as convergence.

The STILL MISSING INPUT is precisely an all-depth certifier E_k:
outside E_k every n<2^k has a proof-carrying terminal/merge chain,
and k*|E_k| <= 2^k for all sufficiently large k.

Finite experimental coverage, Tao's almost-bounded theorem and
the V149 witness soundness do not discharge that quantified premise.

GLOBAL COLLATZ UNKNOWN. NO QED. V134 STATE UNCHANGED.
-/

/-- The unaccelerated ORDINARY map used in the density theorem.
    It is not pointwise equal to the MathGraph shortcut map. -/
def v150Ordinary (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else 3*n+1

def v150OrdReaches (n a : Nat) : Prop :=
  ∃ k : Nat, iter v150Ordinary k n = a

/-- If the shortcut successor is certified to reach the terminal
    class, then the original source is certified one step earlier. -/
theorem v150_good_before_shortcut (n : Nat)
    (h : CollatzGood (shortcut n)) : CollatzGood n := by
  obtain ⟨k,hk⟩ := h
  exact ⟨k+1, by simpa only [iter] using hk⟩

/-- A shortcut-convergent source remains convergent after a single
    ordinary step. For odd input, the intermediate 3n+1 endpoint is
    NOT an accelerated shortcut endpoint; it executes one extra
    even ordinary/shortcut step to rejoin the real future. -/
theorem v150_good_after_one_ordinary_step (n : Nat)
    (hg : CollatzGood n) :
    CollatzGood (v150Ordinary n) := by
  have hs : CollatzGood (shortcut n) :=
    eventually_step_forward shortcut Terminal terminal_forward_invariant hg
  by_cases he : n % 2 = 0
  · simpa [v150Ordinary,shortcut,he] using hs
  · have h3even : (3*n+1)%2=0 := by omega
    have hmeet : shortcut (v150Ordinary n) = shortcut n := by
      simp [v150Ordinary, shortcut, he, h3even]
    apply v150_good_before_shortcut
    rw [hmeet]
    exact hs

/-- Every genuine ordinary future of a shortcut-good source remains
    shortcut-good, even across the intermediate odd-step doubling. -/
theorem v150_good_after_ordinary_iter
    (k : Nat) :
    ∀ n : Nat, CollatzGood n →
      CollatzGood (iter v150Ordinary k n) := by
  induction k with
  | zero =>
      intro n hn
      simpa [iter] using hn
  | succ k ih =>
      intro n hn
      have hnext : CollatzGood (v150Ordinary n) :=
        v150_good_after_one_ordinary_step n hn
      simpa only [iter] using ih (v150Ordinary n) hnext

/-- Correct direction for Mazur's predecessor theorem: any ordinary
    predecessor of a shortcut BAD target is also shortcut BAD.
    We do NOT assert equality of ordinary and shortcut predecessor
    sets, which is false for target4/source1. -/
theorem v150_ordinary_predecessor_of_bad_is_bad
    (a n : Nat)
    (ha : PositiveBad a) (hn : 0 < n)
    (hreach : v150OrdReaches n a) :
    PositiveBad n := by
  refine ⟨hn, ?_⟩
  intro hgood
  obtain ⟨k,hk⟩ := hreach
  have hfuture := v150_good_after_ordinary_iter k n hgood
  rw [hk] at hfuture
  exact ha.2 hfuture

/-- Semantic separator: ordinary 1 reaches 4 in one step,
    whereas the shortcut 1↔2 cycle never touches 4. -/
theorem v150_not_equal_predecessor_sets :
    v150OrdReaches 1 4 ∧
    ¬ (∃ k : Nat, iter shortcut k 1 = 4) := by
  constructor
  · refine ⟨1, ?_⟩
    decide
  · intro ⟨k,hk⟩
    have hT : ∀ j : Nat, Terminal (iter shortcut j 1) := by
      intro j
      induction j with
      | zero => exact Or.inl rfl
      | succ j ih =>
          rw [iter_succ_last]
          exact terminal_forward_invariant _ ih
    rcases hT k with h1 | h2 <;> omega

/-- For EVERY hypothetical least positive bad source n,
    the true successor a=T(n) is itself bad and a ≡ 2 (mod 3),
    so it belongs to the 3-nondivisible target class. -/
theorem v150_minimal_bad_has_nonthree_bad_successor
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    PositiveBad (shortcut n) ∧ shortcut n % 3 = 2 := by
  have hnodd : n%2=1 := positive_minimal_bad_odd hmin
  have hdouble : 2*shortcut n=3*n+1 := by
    simpa [hnodd] using double_shortcut n
  have hp : 0<shortcut n := shortcut_positive n hmin.1.1
  have hbad : ¬ CollatzGood (shortcut n) := by
    intro hg
    exact hmin.1.2 (v150_good_before_shortcut n hg)
  exact ⟨⟨hp,hbad⟩,by omega⟩

/-- Count DISTINCT positive starting integers below X; the
    noncomputable decision procedure is used only to state exact
    finite cardinality bounds, not to decide Collatz. -/
noncomputable def v150BadCount (X : Nat) : Nat := by
  classical
  exact ((Finset.range X).filter (fun n => PositiveBad n)).card

noncomputable def v150OrdPredecessorCount (a X : Nat) : Nat := by
  classical
  exact ((Finset.range X).filter
    (fun n => 0<n ∧ v150OrdReaches n a)).card

theorem v150_bad_target_predecessors_counted_as_bad
    (a X : Nat) (hbad : PositiveBad a) :
    v150OrdPredecessorCount a X ≤ v150BadCount X := by
  classical
  unfold v150OrdPredecessorCount v150BadCount
  apply Finset.card_le_card
  intro n hn
  have hmem := Finset.mem_filter.mp hn
  apply Finset.mem_filter.mpr
  exact ⟨hmem.1,
    v150_ordinary_predecessor_of_bad_is_bad
      a n hbad hmem.2.1 hmem.2.2⟩

/-- Explicit, *external* predecessor-amplification contract. This is
    a quantified premise, NOT an imported axiom or theorem proved
    by the local MathGraph Lean kernel. The pinned 2026 source uses
    an equivalent positive REAL density constant; a real-to-Nat
    reciprocal choice is needed before direct formal composition. -/
def V150PredecessorAmplifier : Prop :=
  ∀ a : Nat, 0<a → a%3≠0 →
    ∃ q X0 : Nat, 0<q ∧
      ∀ X : Nat, X0≤X →
        X ≤ q*v150OrdPredecessorCount a X

/-- Import boundary fully visible: IF the external amplifier
    contract holds, a least positive bad source forces positive
    lower counting density of bad starts. The new 3-mod restriction
    is discharged via its true odd shortcut successor. -/
theorem v150_amplify_actual_minimal_bad
    (hAmp : V150PredecessorAmplifier)
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ∃ q X0 : Nat, 0<q ∧
      ∀ X : Nat, X0≤X → X≤q*v150BadCount X := by
  obtain ⟨ha,hmod⟩ :=
    v150_minimal_bad_has_nonthree_bad_successor hmin
  have hthree : shortcut n%3≠0 := by omega
  obtain ⟨q,X0,hq,hcounts⟩ := hAmp (shortcut n) ha.1 hthree
  refine ⟨q,X0,hq,?_⟩
  intro X hx
  have hpred := hcounts X hx
  have hsubset :=
    v150_bad_target_predecessors_counted_as_bad
      (shortcut n) X ha
  exact Nat.le_trans hpred (Nat.mul_le_mul_left q hsubset)

/-- A mathematically decisive but STILL-UNPROVED quantified mass
    condition: k times the number of genuinely bad positive integers
    below 2^k is at most 2^k for every sufficiently large k. -/
def V150DyadicBadMassVanishes : Prop :=
  ∃ K : Nat, ∀ k : Nat, K≤k →
    k*v150BadCount (2^k) ≤ 2^k

/-- THE CONDITIONAL DENSITY CLOSURE:
    external amplification plus an ALL-DEPTH shrinking bad-count
    estimate contradicts a hypothetical minimal bad source. Neither
    input is silently discharged here. -/
theorem v150_collatz_of_amplification_and_dyadic_mass
    (hAmp : V150PredecessorAmplifier)
    (hDyad : V150DyadicBadMassVanishes) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  obtain ⟨K,hMass⟩ := hDyad
  have hNoMin : ∀ n : Nat, ¬ MinimalBad PositiveBad n := by
    intro n hmin
    obtain ⟨q,X0,hq,hLower⟩ :=
      v150_amplify_actual_minimal_bad hAmp hmin
    let k := K+q+X0+2
    have hK : K≤k := by dsimp [k]; omega
    have hqk : q+1≤k := by dsimp [k]; omega
    have hX0 : X0≤2^k := by
      have hp := pow_two_exceeds_its_index k
      dsimp [k] at hp ⊢
      omega
    let d := v150BadCount (2^k)
    have hlow : 2^k ≤ q*d := by
      simpa only [d] using hLower (2^k) hX0
    have hhigh : k*d ≤ 2^k := by
      simpa only [d] using hMass k hK
    have hd : 0<d := by
      by_contra hn
      have hzero : d=0 := by omega
      rw [hzero, Nat.mul_zero] at hlow
      have hpow : 0<(2 : Nat)^k := Nat.pow_pos (by decide)
      omega
    have hs := Nat.mul_le_mul_right d hqk
    have hmul : q*d+d ≤ k*d := by
      simpa [Nat.add_mul] using hs
    omega
  have hNoBad : ∀ n, ¬ PositiveBad n :=
    no_bad_of_no_minimal PositiveBad hNoMin
  intro n hn
  apply Classical.byContradiction
  intro h
  exact hNoBad n ⟨hn,h⟩

/-- Proof-carrying terminal/merge grammar. A mere strict descent or
    future-class identity never enters the certified-good count
    unless its earlier source also has a terminating certificate. -/
inductive V150Closed : Nat → Prop where
  | terminal {n : Nat} :
      Terminal n → V150Closed n
  | merger {n p : Nat} :
      LowerMerge shortcut n p → V150Closed p → V150Closed n

theorem v150_closed_certificate_sound
    {n : Nat} (h : V150Closed n) : CollatzGood n := by
  induction h with
  | terminal ht =>
      exact ⟨0,ht⟩
  | merger hm _hp ih =>
      exact lower_merge_preserves_eventual shortcut Terminal
        terminal_forward_invariant hm ih

/-- A certifier may output a finite exceptional Finset for each
    dyadic cutoff. Soundness means EVERY positive source outside it
    has a real terminal/merge chain, with proof, not a mere heuristic
    prediction, apparent descent or root-class equality. -/
theorem v150_proof_carrying_envelope_bounds_true_bad_count
    (E : Nat → Finset Nat)
    (hCover : ∀ k n : Nat,
      0<n → n < 2^k → n ∉ E k → V150Closed n)
    (k : Nat) :
    v150BadCount (2^k) ≤ (E k).card := by
  classical
  unfold v150BadCount
  apply Finset.card_le_card
  intro n hn
  have hmem := Finset.mem_filter.mp hn
  by_cases ht : n ∈ E k
  · exact ht
  · have hclosed := hCover k n hmem.2.1 (Finset.mem_range.mp hmem.1) ht
    exact False.elim (hmem.2.2 (v150_closed_certificate_sound hclosed))

/-- The exact final source-verified path:
    external density amplifier + certified terminal-closure coverage
    + a UNIVERSAL dyadic mass estimate ⇒ Collatz.
    Both quantified research inputs stay visibly explicit. -/
theorem v150_collatz_of_proof_carrying_exceptional_cover
    (hAmp : V150PredecessorAmplifier)
    (E : Nat → Finset Nat)
    (hCover : ∀ k n : Nat,
      0<n → n < 2^k → n ∉ E k → V150Closed n)
    (hSmall : ∃ K : Nat, ∀ k : Nat, K≤k →
      k*(E k).card ≤ 2^k) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  have hDyad : V150DyadicBadMassVanishes := by
    obtain ⟨K,hK⟩ := hSmall
    refine ⟨K,?_⟩
    intro k hk
    have hbound :=
      v150_proof_carrying_envelope_bounds_true_bad_count E hCover k
    have hScaled := Nat.mul_le_mul_left k hbound
    exact Nat.le_trans hScaled (hK k hk)
  exact v150_collatz_of_amplification_and_dyadic_mass hAmp hDyad

#print axioms v150_good_after_one_ordinary_step
#print axioms v150_ordinary_predecessor_of_bad_is_bad
#print axioms v150_not_equal_predecessor_sets
#print axioms v150_minimal_bad_has_nonthree_bad_successor
#print axioms v150_bad_target_predecessors_counted_as_bad
#print axioms v150_amplify_actual_minimal_bad
#print axioms v150_collatz_of_amplification_and_dyadic_mass
#print axioms v150_closed_certificate_sound
#print axioms v150_proof_carrying_envelope_bounds_true_bad_count
#print axioms v150_collatz_of_proof_carrying_exceptional_cover

end SourceProduct
end CollatzFinal
