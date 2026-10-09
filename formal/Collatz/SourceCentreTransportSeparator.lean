import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-!
V146 — ROS FIXED-SOURCE FINITE-CENTRE BOUNDARY.

Protected consequence: an ORIGINAL positive source meets a strictly
smaller positive source at two independent ACTUAL clocks.

The V95 source cocycle yields an exact congruence:
  2^k * (T^k(n)+1) = 3^oddCount(n,k)*n + (bias(n,k)+2^k).
High precision of endpoint+1 therefore transports to the AFFINE
source numerator with clock-dependent odd denominator and bias,
not automatically to n-c for a finite list of integer centres.

This file kernel-checks:
 A. the true V95 exact numerator pullback;
 B. the fixed-positive-source contradiction for ANY finite set of
    nonpositive integer centres, with NO hypothetical QED claim;
 C. a strengthened V115 adversarial family rooted at n=27:
       p(0)=27; p(t+1)=64*p(t)+91;
       B(t)=6*t+5; q(t)=2^B(t);
       9*p(t)+13 = 8*q(t);
       T^3(p(t)) = q(t)-1;
       p(t)%4=3 and no descent in the FIRST THREE steps;
    whose source-transport centre is the rational -13/9.
 D. for EVERY predeclared finite nonpositive INTEGER centre set,
    some real positive source in this family has arbitrarily high
    endpoint precision but NONE of the predeclared centres
    supports the matching original-source dyadic congruence.
 E. two true FUTURE-COALESCENT sources 21 and 3 require different
    integer source centres -3 and -1 at their lawful meeting clocks.
    Quotient equivalence does not authorize collapsing source-centre
    transport laws or two independent clocks.

Critically, ALL p(t) may have later lower-source mergers: this does
NOT falsify a hypothetical stronger finite-centre theorem restricted
to a genuine infinite no-exit least-bad trajectory. That all-depth
source-attached bridge is the missing theorem. GLOBAL COLLATZ UNKNOWN.
-/

/-- Mandatory exact affine source pullback. This transport preserves
    the source n and exact actual clock k; no replacement by a fixed
    integer centre is made. -/
theorem endpoint_precision_pulls_back_to_source_affine
    (n k B : Nat)
    (hprec : 2 ^ B ∣ (iter shortcut k n + 1)) :
    2 ^ (B + k) ∣
      (3 ^ oddCount n k * n + (bias n k + 2 ^ k)) := by
  obtain ⟨u, hu⟩ := hprec
  refine ⟨u, ?_⟩
  calc
    3 ^ oddCount n k * n + (bias n k + 2 ^ k) =
        2 ^ k * (iter shortcut k n + 1) := by
          have heq := exact_affine n k
          rw [Nat.mul_add]
          omega
    _ = 2 ^ k * (2 ^ B * u) := by rw [hu]
    _ = 2 ^ (B + k) * u := by
          simp [Nat.pow_add, Nat.mul_assoc, Nat.mul_comm,
            Nat.mul_left_comm]

/-- A finite list of nonpositive integer centres is represented
    faithfully by their nonnegative magnitudes d, with c=-d. -/
def maxNegativeCentreMagnitude : List Nat → Nat
  | [] => 0
  | d :: ds => max d (maxNegativeCentreMagnitude ds)

theorem listed_centre_magnitude_le_max :
    ∀ (ds : List Nat) (d : Nat), d ∈ ds →
      d ≤ maxNegativeCentreMagnitude ds := by
  intro ds
  induction ds with
  | nil =>
      intro d hd
      simp at hd
  | cons a rest ih =>
      intro d hd
      simp only [List.mem_cons] at hd
      rcases hd with h | h
      · subst d
        exact Nat.le_max_left a (maxNegativeCentreMagnitude rest)
      · exact Nat.le_trans (ih d h)
          (Nat.le_max_right a (maxNegativeCentreMagnitude rest))

/-- Elementary all-depth growth for a power of two, no source
    compactness hypothesis. -/
theorem pow_two_exceeds_its_index (B : Nat) :
    B < (2 : Nat) ^ B := by
  induction B with
  | zero => decide
  | succ B ih =>
      have hp : 0 < (2 : Nat) ^ B :=
        Nat.pow_pos (by decide)
      rw [Nat.pow_succ]
      omega

/-- For ONE fixed positive integer n, finite nonpositive centres
    are already contradicted by all-depth dyadic precision. This is
    the valid last inference IF the all-depth source bar is given. -/
theorem fixed_positive_source_cannot_match_finite_negative_centres
    (n : Nat) (hn : 0 < n) (ds : List Nat)
    (hbar : ∀ B : Nat,
      ∃ d : Nat, d ∈ ds ∧ 2 ^ B ∣ (n + d)) : False := by
  let M := maxNegativeCentreMagnitude ds
  let B := n + M + 1
  have hpow := pow_two_exceeds_its_index B
  obtain ⟨d, hd, hdiv⟩ := hbar B
  have hdmax := listed_centre_magnitude_le_max ds d hd
  have hpos : 0 < n + d := by omega
  have hlt : n + d < 2 ^ B := by
    dsimp [B] at hpow ⊢
    omega
  have hle : 2 ^ B ≤ n + d := Nat.le_of_dvd hpos hdiv
  omega

/-- Formally isolated MISSING seam. This theorem proves only that
    the *additional universal finite-centre bar*, IF independently
    established for every genuinely minimal bad source, would imply
    Collatz. No such bar is supplied or claimed here. -/
theorem collatz_of_universal_minimal_bad_finite_centre_bar
    (hbridge : ∀ n : Nat, MinimalBad PositiveBad n →
      ∃ ds : List Nat, ∀ B : Nat,
        ∃ d : Nat, d ∈ ds ∧ 2 ^ B ∣ (n + d)) :
    ∀ n : Nat, 0 < n → CollatzGood n := by
  have hno : ∀ n : Nat, ¬ MinimalBad PositiveBad n := by
    intro n hmin
    obtain ⟨ds, hbar⟩ := hbridge n hmin
    exact fixed_positive_source_cannot_match_finite_negative_centres
      n hmin.1.1 ds hbar
  have hnone : ∀ n : Nat, ¬ PositiveBad n :=
    no_bad_of_no_minimal PositiveBad hno
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn, hbad⟩

/-- Adversarial ORIGINAL source. B grows by six, and the actual
    starting value changes with B. All arithmetic is exact Nat. -/
def shadowSource : Nat → Nat
  | 0 => 27
  | t + 1 => 64 * shadowSource t + 91

def shadowPrecision (t : Nat) : Nat := 6 * t + 5
def shadowModulus (t : Nat) : Nat := 2 ^ shadowPrecision t

private theorem shadow_source_ge_27 (t : Nat) :
    27 ≤ shadowSource t := by
  cases t with
  | zero => decide
  | succ t =>
      change 27 ≤ 64 * shadowSource t + 91
      omega

private theorem shadow_source_mod_eight (t : Nat) :
    shadowSource t % 8 = 3 := by
  cases t with
  | zero => decide
  | succ t =>
      change (64 * shadowSource t + 91) % 8 = 3
      omega

private theorem shadow_modulus_pos (t : Nat) :
    0 < shadowModulus t := by
  unfold shadowModulus
  exact Nat.pow_pos (by decide)

/-- Infinite exact integer identity encoding fixed RATIONAL
    source centre -13/9. This is never silently integerized. -/
theorem shadow_source_affine_identity (t : Nat) :
    9 * shadowSource t + 13 = 8 * shadowModulus t := by
  induction t with
  | zero => decide
  | succ t ih =>
      have hmod : shadowModulus (t + 1) =
          64 * shadowModulus t := by
        unfold shadowModulus shadowPrecision
        have he : 6 * (t + 1) + 5 = (6 * t + 5) + 6 := by
          omega
        rw [he, Nat.pow_add]
        simp [Nat.mul_comm]
      calc
        9 * shadowSource (t + 1) + 13 =
            64 * (9 * shadowSource t + 13) := by
              change 9 * (64 * shadowSource t + 91) + 13 =
                64 * (9 * shadowSource t + 13)
              omega
        _ = 64 * (8 * shadowModulus t) := by rw [ih]
        _ = 8 * shadowModulus (t + 1) := by
              rw [hmod]
              omega

private theorem shadow_first_odd (t : Nat) :
    shadowSource t % 2 = 1 := by
  have h := shadow_source_mod_eight t
  omega

private theorem shadow_first_step (t : Nat) :
    2 * shortcut (shadowSource t) =
      3 * shadowSource t + 1 := by
  simpa [shadow_first_odd t] using
    (double_shortcut (shadowSource t))

private theorem shadow_second_input_odd (t : Nat) :
    shortcut (shadowSource t) % 2 = 1 := by
  have hmod := shadow_source_mod_eight t
  have hs := shadow_first_step t
  omega

private theorem shadow_derived_intermediate (t : Nat) :
    3 * shortcut (shadowSource t) + 5 =
      4 * shadowModulus t := by
  have hp := shadow_source_affine_identity t
  have hs := shadow_first_step t
  omega

private theorem shadow_second_step (t : Nat) :
    shortcut (shortcut (shadowSource t)) =
      2 * (shadowModulus t - 1) := by
  have he := shadow_second_input_odd t
  have hdouble : 2 * shortcut (shortcut (shadowSource t)) =
      3 * shortcut (shadowSource t) + 1 := by
    simpa [he] using (double_shortcut (shortcut (shadowSource t)))
  have hi := shadow_derived_intermediate t
  have hq := shadow_modulus_pos t
  omega

/-- The exact true third shortcut endpoint is 2^B-1,
    independently of any convergence inference. -/
theorem shadow_actual_endpoint (t : Nat) :
    iter shortcut 3 (shadowSource t) =
      shadowModulus t - 1 := by
  have hs := shadow_second_step t
  have he : (2 * (shadowModulus t - 1)) % 2 = 0 := by
    omega
  calc
    iter shortcut 3 (shadowSource t) =
        shortcut (shortcut (shortcut (shadowSource t))) := rfl
    _ = shortcut (2 * (shadowModulus t - 1)) := by rw [hs]
    _ = shadowModulus t - 1 := by simp [shortcut, he]

/-- This family *passes* V141's necessary least-bad-source
    3-mod-4 guard, and has a true rising three-step prefix.
    That is NOT a certificate of indefinite NoExit. -/
theorem shadow_actual_prefix_nondescending (t : Nat) :
    shadowSource t % 4 = 3 ∧
    (∀ k : Nat, k ≤ 3 →
      shadowSource t ≤ iter shortcut k (shadowSource t)) := by
  have hmod := shadow_source_mod_eight t
  have hp := shadow_source_affine_identity t
  have hs := shadow_first_step t
  have hsecond := shadow_second_step t
  have hthird := shadow_actual_endpoint t
  have hge := shadow_source_ge_27 t
  have hq := shadow_modulus_pos t
  have hqgt : shadowSource t < shadowModulus t - 1 := by
    omega
  constructor
  · omega
  · intro k hk
    have hkCases : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 := by
      omega
    rcases hkCases with h0 | h1 | h2 | h3
    · subst k
      simp [iter]
    · subst k
      change shadowSource t ≤ shortcut (shadowSource t)
      omega
    · subst k
      change shadowSource t ≤
        shortcut (shortcut (shadowSource t))
      rw [hsecond]
      omega
    · subst k
      rw [hthird]
      omega

/-- Arbitrarily precise reached endpoints and exact pulled source
    affine numerator for this explicit 3-mod-4 rising family. -/
theorem shadow_high_endpoint_precision (t : Nat) :
    shadowModulus t ∣
      (iter shortcut 3 (shadowSource t) + 1) ∧
    9 * shadowSource t + 13 = 8 * shadowModulus t := by
  constructor
  · have hq := shadow_modulus_pos t
    have hend := shadow_actual_endpoint t
    have hsum : iter shortcut 3 (shadowSource t) + 1 =
        shadowModulus t := by
      rw [hend]
      omega
    rw [hsum]
    exact dvd_refl _
  · exact shadow_source_affine_identity t

/-- If the dyadic precision q exceeds 13+9d, the correct affine
    identity already places 0 < source+d < q. Hence it is IMPOSSIBLE
    to interpret the pulled centre -13/9 as the fixed integer -d.
    This is strict exact source transport, not bounded enumeration. -/
theorem shadow_excludes_one_integer_centre
    (t d : Nat)
    (hsize : 13 + 9 * d < shadowModulus t) :
    ¬ shadowModulus t ∣ (shadowSource t + d) := by
  intro hdvd
  have hs := shadow_source_affine_identity t
  have hp := shadow_source_ge_27 t
  have hpos : 0 < shadowSource t + d := by omega
  have hlt : shadowSource t + d < shadowModulus t := by
    omega
  have hle : shadowModulus t ≤ shadowSource t + d :=
    Nat.le_of_dvd hpos hdvd
  omega

/-- Stronger source-specific V115 separator: for EVERY finite set
    of nonpositive integer centres, an ACTUAL positive source
    congruent 3 mod4, with no direct descent during the first THREE
    steps, reaches arbitrarily high endpoint precision but satisfies
    NONE of the claimed original-source integer-centre congruences.

    The source varies with t; the theorem does NOT refute the much
    stronger remaining all-depth NoExit-specific hypothetical bar.
-/
theorem no_finite_integer_centres_for_rising_shadow_family
    (ds : List Nat) :
    ∃ t : Nat,
      shadowSource t % 4 = 3 ∧
      (∀ k : Nat, k ≤ 3 →
         shadowSource t ≤ iter shortcut k (shadowSource t)) ∧
      shadowModulus t ∣
         (iter shortcut 3 (shadowSource t) + 1) ∧
      (∀ d : Nat, d ∈ ds →
         ¬ shadowModulus t ∣ (shadowSource t + d)) := by
  let M := maxNegativeCentreMagnitude ds
  let t := 13 + 9 * M
  have hb : shadowPrecision t < shadowModulus t := by
    exact pow_two_exceeds_its_index (shadowPrecision t)
  have hsize : 13 + 9 * M < shadowModulus t := by
    have hindex : 13 + 9 * M ≤ shadowPrecision t := by
      dsimp [shadowPrecision, t]
      omega
    exact Nat.lt_of_le_of_lt hindex hb
  obtain ⟨hmod, hprefix⟩ := shadow_actual_prefix_nondescending t
  obtain ⟨hdyadic, _⟩ := shadow_high_endpoint_precision t
  refine ⟨t, hmod, hprefix, hdyadic, ?_⟩
  intro d hd
  have hle := listed_centre_magnitude_le_max ds d hd
  apply shadow_excludes_one_integer_centre t d
  omega

/-- V128 actual coalescence at endpoint 8 gives two DIFFERENT
    original-source integer centres -3 and -1 with independent
    clocks 3 and 2. A future-coalescence quotient is not by itself
    an authorized quotient of affine source-centre witnesses. -/
theorem coalescent_sources_require_distinct_source_centres :
    iter shortcut 3 21 = iter shortcut 2 3 ∧
    3 ^ oddCount 21 3 * 3 = bias 21 3 + 2 ^ 3 ∧
    3 ^ oddCount 3 2 * 1 = bias 3 2 + 2 ^ 2 ∧
    (3 : Nat) ≠ 1 := by
  decide

#print axioms endpoint_precision_pulls_back_to_source_affine
#print axioms listed_centre_magnitude_le_max
#print axioms pow_two_exceeds_its_index
#print axioms fixed_positive_source_cannot_match_finite_negative_centres
#print axioms collatz_of_universal_minimal_bad_finite_centre_bar
#print axioms shadow_source_affine_identity
#print axioms shadow_actual_endpoint
#print axioms shadow_actual_prefix_nondescending
#print axioms shadow_high_endpoint_precision
#print axioms shadow_excludes_one_integer_centre
#print axioms no_finite_integer_centres_for_rising_shadow_family
#print axioms coalescent_sources_require_distinct_source_centres

end SourceProduct
end CollatzFinal
