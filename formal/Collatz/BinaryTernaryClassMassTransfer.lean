import Collatz.SourceLockedDyadicFutureLift
import Collatz.UniversalFutureClassFrontier

namespace CollatzFinal
namespace SourceProduct

noncomputable section

/-- Finite exact population counting is classical for a hypothetical
    nondecidable future-class predicate; this instance carries ONLY
    logical decidability, not a convergent-or-divergent oracle. -/
local instance (p : Prop) : Decidable p :=
  Classical.propDecidable p

/-!
V165 — EXACT BINARY-SOURCE / TERNARY-ENDPOINT FUTURE-CLASS MASS TRANSFER.

The real V160 source-affine identity is pointwise:
  T^k(r + 2^k*q) = g + 3^a*q
with g=T^k(r), a=oddCount(r,k).

For ANY property P invariant under one ACTUAL shortcut step,
  P(r + 2^k*q) IFF P(g + 3^a*q)
for EVERY q. Thus for ANY finite q budget Q, the number of
P-labelled genuine sources in a binary arithmetic progression
equals the number of P-labelled reached endpoints in the
corresponding ternary arithmetic progression.

This is a POPULATION accounting identity, unlike V160's
isolated certificate existence. It applies to the TRUE
terminal class, hypothetical bad class, and EVERY two-clock
future-equivalence class, without assuming their uniqueness.

The equality supplies NO contraction and imposes NO source
height cutoff beyond the chosen q-range. To infer universal
Collatz one still needs a genuinely independent quantitative
bound on the class indicator solutions (V151), not just the
identity above. The synthetic G7 dual-basin countermodel
also satisfies its analog, so this structure by itself
cannot rule out multiple future classes.

GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- Any shortcut-invariant property is invariant under every
    actual finite number of shortcut steps. -/
theorem v165_invariant_all_real_clocks
    (P : Nat → Prop)
    (hStep : ∀ n : Nat, P n ↔ P (shortcut n))
    (k n : Nat) :
    P n ↔ P (iter shortcut k n) := by
  induction k generalizing n with
  | zero =>
      simp [iter]
  | succ k ih =>
      simpa only [iter] using
        ((hStep n).trans (ih (shortcut n)))

/-- Every original binary source cylinder is paired, q by q,
    to a ternary affine endpoint cylinder preserving ANY
    property of the genuine shortcut future. -/
theorem v165_binary_ternary_class_indicator_transport
    (P : Nat → Prop)
    (hStep : ∀ n : Nat, P n ↔ P (shortcut n))
    (r k q : Nat) :
    P (r+2^k*q) ↔
      P (iter shortcut k r+3^oddCount r k*q) := by
  have hf := v165_invariant_all_real_clocks P hStep
    k (r+2^k*q)
  rw [v160_exact_cylinder_affine] at hf
  exact hf

/-- The exact finite q-population transfer does not
    require any independence of source parities or
    convergence assumptions. All counts are integer-exact. -/
theorem v165_binary_ternary_finite_population_transport
    (P : Nat → Prop)
    (hStep : ∀ n : Nat, P n ↔ P (shortcut n))
    (r k Q : Nat) :
    v150Count (fun q => P (r+2^k*q)) Q =
      v150Count
        (fun q => P (iter shortcut k r+3^oddCount r k*q)) Q := by
  classical
  induction Q with
  | zero =>
      rfl
  | succ Q ih =>
      have heq :=
        v165_binary_ternary_class_indicator_transport
          P hStep r k Q
      by_cases hs : P (r+2^k*Q)
      · have ht := heq.mp hs
        simpa [v150Count,hs,ht] using ih
      · have ht :
          ¬ P (iter shortcut k r+3^oddCount r k*Q) :=
          fun h => hs (heq.mpr h)
        simpa [v150Count,hs,ht] using ih

/-- Terminal convergence is invariant under the exact next
    shortcut step in BOTH directions. Neither direction
    assumes universal termination. -/
theorem v165_good_step_iff (n : Nat) :
    CollatzGood n ↔ CollatzGood (shortcut n) := by
  constructor
  · intro hg
    exact eventually_step_forward shortcut Terminal
      terminal_forward_invariant hg
  · intro hg
    exact v150_good_before_shortcut n hg

/-- Any hypothetical bad-source indicator is itself exactly
    shortcut-invariant, including the excluded source zero. -/
theorem v165_bad_step_iff (n : Nat) :
    PositiveBad n ↔ PositiveBad (shortcut n) := by
  by_cases hz : n=0
  · subst n
    simp [PositiveBad,shortcut]
  · have hn : 0<n := Nat.pos_of_ne_zero hz
    have hNext : 0<shortcut n := shortcut_positive n hn
    have hiff := v165_good_step_iff n
    constructor
    · intro h
      refine ⟨hNext,?_⟩
      intro hh
      exact h.2 (hiff.mpr hh)
    · intro h
      refine ⟨hn,?_⟩
      intro hh
      exact h.2 (hiff.mp hh)

/-- The FINITE bad-source population (a set that may be empty)
    obeys exactly the same q-parameter mass equation in EVERY
    binary original-source cylinder. -/
theorem v165_bad_mass_binary_ternary_fiber
    (r k Q : Nat) :
    v150Count (fun q => PositiveBad (r+2^k*q)) Q =
      v150Count (fun q =>
        PositiveBad (iter shortcut k r+3^oddCount r k*q)) Q := by
  exact v165_binary_ternary_finite_population_transport
    PositiveBad v165_bad_step_iff r k Q

/-- Membership in ANY single genuine future class is invariant
    under one real shortcut step, not just in the 1/2 class. -/
theorem v165_future_meet_step_iff
    (b n : Nat) :
    V155FutureMeet n b ↔
      V155FutureMeet (shortcut n) b := by
  have hNear : V155FutureMeet n (shortcut n) := by
    refine ⟨1,0,?_⟩
    rfl
  constructor
  · intro hh
    exact v155_future_meet_trans
      (v155_future_meet_symm hNear) hh
  · intro hh
    exact v155_future_meet_trans hNear hh

/-- UNIVERSAL CLASS-MASS TRANSPORT: each arbitrary genuine
    future-coalescence class b has exact equal finite numbers
    of source members and endpoint members in these paired
    arithmetic progressions, regardless of eventual Collatz. -/
theorem v165_every_future_class_mass_fiber
    (b r k Q : Nat) :
    v150Count
      (fun q => V155FutureMeet (r+2^k*q) b) Q =
    v150Count
      (fun q =>
        V155FutureMeet
          (iter shortcut k r+3^oddCount r k*q) b) Q := by
  exact v165_binary_ternary_finite_population_transport
    (fun n => V155FutureMeet n b)
    (v165_future_meet_step_iff b) r k Q

/-- The terminal 1<->2 future class is a specialization,
    though this theorem DOES NOT count almost all sources. -/
theorem v165_good_mass_binary_ternary_fiber
    (r k Q : Nat) :
    v150Count
      (fun q => CollatzGood (r+2^k*q)) Q =
    v150Count
      (fun q =>
        CollatzGood
          (iter shortcut k r+3^oddCount r k*q)) Q := by
  exact v165_binary_ternary_finite_population_transport
    CollatzGood v165_good_step_iff r k Q

#print axioms v165_invariant_all_real_clocks
#print axioms v165_binary_ternary_class_indicator_transport
#print axioms v165_binary_ternary_finite_population_transport
#print axioms v165_good_step_iff
#print axioms v165_bad_step_iff
#print axioms v165_bad_mass_binary_ternary_fiber
#print axioms v165_future_meet_step_iff
#print axioms v165_every_future_class_mass_fiber
#print axioms v165_good_mass_binary_ternary_fiber

end

end SourceProduct
end CollatzFinal
