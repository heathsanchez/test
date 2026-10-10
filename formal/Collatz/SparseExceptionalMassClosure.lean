import Collatz.DensityAmplificationClosure

namespace CollatzFinal
namespace SourceProduct

/-!
V151 — SHARP SPARSE-SCALE EXCEPTIONAL-MASS CLOSURE.

V150 independently checked (on its declared external amplifier premise)
that positive lower density of a hypothetical bad class contradicts a
certain all-depth k*badCount(2^k) <= 2^k mass bound.

The V150 rate 1/k and "every large k" premise are STRONGER than
required. The exact weakest dyadic asymptotic criterion needed here
is upper density-one convergence along arbitrarily large dyadic
cutoffs, equivalently:

  For any q>0 and any lower cutoff X0, SOME dyadic 2^k >= X0
  satisfies q*badCount(2^k) < 2^k.

V151 proves that the explicit external V150 predecessor amplifier plus
this SPARSE condition rules out EVERY minimal positive bad source.

A stronger proof-carrying certifier interface uses a set E(k,n) of
not-yet-certified starts at dyadic cutoff 2^k. All positive n outside
E(k,n) must have a true V150Closed terminal/merge certificate. If the
exact EXCEPTIONAL population of E can be made smaller than any
positive rational fraction 1/q on arbitrarily large dyadic cutoffs,
then Collatz follows.

The two actual quantitative/universal premises are NOT discharged
here: Mazur's external Lean result is a reported pinned theorem but
not independently rebuilt in MathGraph, and no symbolic all-depth
sparse exceptional-mass estimate exists in V151.

V151 makes clear that a 1/k rate, uniform upper bound and monotone
density limit are unnecessary. NO Collatz QED is claimed.
-/

/-- The asymptotically MINIMAL source-mass criterion relevant to a
    positive lower-density exceptional population. It asks only for
    arbitrarily large DYADIC cutoffs with arbitrarily small
    exceptional population fractions, not all sufficiently large k. -/
def V151SparseDyadicBadMass : Prop :=
  ∀ q X0 : Nat, 0<q →
    ∃ k : Nat,
      X0 ≤ 2^k ∧
      q*v150BadCount (2^k) < 2^k

/-- Amplification + sparse dying exceptional mass is impossible
    under any hypothetical minimal bad original source.
    Both global inputs are explicit; this is conditional only. -/
theorem v151_sparse_density_eliminates_every_minimal_bad
    (hAmp : V150PredecessorAmplifier)
    (hSparse : V151SparseDyadicBadMass) :
    ∀ n : Nat, ¬ MinimalBad PositiveBad n := by
  intro n hmin
  obtain ⟨q,X0,hq,hLower⟩ :=
    v150_amplify_actual_minimal_bad hAmp hmin
  obtain ⟨k,hcut,hSmall⟩ := hSparse q X0 hq
  have hlarge : 2^k ≤ q*v150BadCount (2^k) :=
    hLower (2^k) hcut
  omega

/-- Conditional universal closeout at SPARSE DYADIC scales.
    It does not require the stronger V150 all-k 1/k bound. -/
theorem v151_collatz_of_sparse_density_one_and_amplification
    (hAmp : V150PredecessorAmplifier)
    (hSparse : V151SparseDyadicBadMass) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n :=
    no_bad_of_no_minimal PositiveBad
      (v151_sparse_density_eliminates_every_minimal_bad hAmp hSparse)
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn,hbad⟩

/-- A genuinely usable certifier goal. A verified predicate E(k,n)
    may depend on scale. For every prescribed denominator q and
    cutoff X0, one may choose a DIFFERENT large dyadic cutoff k.
    No fixed stopping-time horizon, uniform source-bound or global
    density limit is smuggled into the type. -/
def V151SparseCertifiedEnvelope
    (E : Nat → Nat → Prop) : Prop :=
  ∀ q X0 : Nat, 0<q →
    ∃ k : Nat,
      X0 ≤ 2^k ∧
      q*v150EnvelopeCount E k < 2^k

/-- Source-attached exact terminal certificate coverage plus
    sparse envelope mass yields the weaker genuine bad-mass property.
    The bridge uses the formal finite COUNT inequality from V150. -/
theorem v151_certified_envelope_implies_sparse_bad_mass
    (E : Nat → Nat → Prop)
    (hCover : ∀ k n : Nat,
      0<n → n<2^k → ¬ E k n → V150Closed n)
    (hSparseE : V151SparseCertifiedEnvelope E) :
    V151SparseDyadicBadMass := by
  intro q X0 hq
  obtain ⟨k,hcut,hbound⟩ := hSparseE q X0 hq
  refine ⟨k,hcut,?_⟩
  have htrue :=
    v150_proof_carrying_envelope_bounds_true_bad_count E hCover k
  have hweighted := Nat.mul_le_mul_left q htrue
  exact Nat.lt_of_le_of_lt hweighted hbound

/-- Full composable, all-source conditional Collatz closeout.
    Unlike V150's stronger interface, it asks ONLY for sparse-scale
    vanishing population of unproved starts, proved by the guarded
    terminal/merge proof language, rather than merely low-size
    local-descent residues. -/
theorem v151_collatz_of_sparse_proof_carrying_exceptional_mass
    (hAmp : V150PredecessorAmplifier)
    (E : Nat → Nat → Prop)
    (hCover : ∀ k n : Nat,
      0<n → n<2^k → ¬ E k n → V150Closed n)
    (hSparseE : V151SparseCertifiedEnvelope E) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  have hs : V151SparseDyadicBadMass :=
    v151_certified_envelope_implies_sparse_bad_mass E hCover hSparseE
  exact v151_collatz_of_sparse_density_one_and_amplification hAmp hs

/-- The external predecessor claim cannot be invoked on a target
    divisible by 3. The new interface preserves exactly that
    restriction, already discharged for minimal bad sources in V150. -/
theorem v151_target_guard_inherited
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    PositiveBad (shortcut n) ∧ shortcut n % 3 ≠ 0 := by
  obtain ⟨hb,hr⟩ := v150_minimal_bad_has_nonthree_bad_successor hmin
  exact ⟨hb,by omega⟩

#print axioms v151_sparse_density_eliminates_every_minimal_bad
#print axioms v151_collatz_of_sparse_density_one_and_amplification
#print axioms v151_certified_envelope_implies_sparse_bad_mass
#print axioms v151_collatz_of_sparse_proof_carrying_exceptional_mass
#print axioms v151_target_guard_inherited

end SourceProduct
end CollatzFinal
