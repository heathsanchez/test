import Collatz.BinaryTernaryClassMassTransfer
import Collatz.InverseHorizonMassCeiling

namespace CollatzFinal
namespace SourceProduct

/-!
V166 — COMPUTABLE FINITE-CLOCK SOURCE/CERTIFICATE MASS TRANSFER.

V165 transfers *eventual* future-class membership and therefore
preserves class mass by definition. It CANNOT yield contraction.

V166 protects a stronger, independent observation:
for every source prefix r, depth k, source lift q, and additional
clock budget h, an ACTUAL certificate reaching {1,2} at clock k+h
is exactly a certificate at clock h on the actual ternary endpoint.

The Boolean predicate below is decidable by computation. The
finite population count is also executable. No undecidable
"CollatzGood" membership test or CLASSICAL.choice is needed.

The same actual affine identity also compiles any VERIFIED
earlier-source endpoint equality into a source-capped genuine
two-clock merger; that is a separate proof mechanism from a
direct terminal hit.

This is an exact, noncircular compiler. It does NOT assert a
positive fraction of timeouts disappear. The V163 reverse entropy
bound says bitlength-or-shorter direct terminal hits are sparse.
The G7 synthetic model shows mass transport alone permits
disjoint positive future classes. GLOBAL COLLATZ UNKNOWN.
-/

/-- An executable terminal certificate at EXACT real shortcut clock t.
    Since 1<->2 is closed, hitting at or before t is equivalent. -/
def v166HitBool (t n : Nat) : Bool :=
  (iter shortcut t n == 1) || (iter shortcut t n == 2)

theorem v166_hit_bool_semantics (t n : Nat) :
    v166HitBool t n = true ↔ Terminal (iter shortcut t n) := by
  simp [v166HitBool,Terminal]

/-- Fully source-attached, exact clock budget conversion,
    with no future-class oracle or unproved long-time horizon. -/
theorem v166_actual_clock_shift (r k h q : Nat) :
    iter shortcut (k+h) (r+2^k*q) =
      iter shortcut h (iter shortcut k r+3^oddCount r k*q) := by
  calc
    iter shortcut (k+h) (r+2^k*q) =
        iter shortcut h (iter shortcut k (r+2^k*q)) :=
      iter_add shortcut k h (r+2^k*q)
    _ = _ := by rw [v160_exact_cylinder_affine]

theorem v166_actual_hit_bool_transport (r k h q : Nat) :
    v166HitBool (k+h) (r+2^k*q) =
      v166HitBool h (iter shortcut k r+3^oddCount r k*q) := by
  exact congrArg (fun x : Nat => (x == 1) || (x == 2))
    (v166_actual_clock_shift r k h q)

/-- The two different horizon windows describe exactly the SAME
    genuine original sources, because terminal {1,2} remains
    invariant under all additional actual shortcut steps. -/
theorem v166_hit_by_horizon_source_to_endpoint (r k h q : Nat) :
    (∃ j : Nat, j<=k+h ∧
      Terminal (iter shortcut j (r+2^k*q))) ↔
    (∃ j : Nat, j<=h ∧
      Terminal (iter shortcut j
        (iter shortcut k r+3^oddCount r k*q))) := by
  have hs :=
    v163_terminal_by_horizon_iff_exact_clock
      (r+2^k*q) (k+h)
  have ht :=
    v163_terminal_by_horizon_iff_exact_clock
      (iter shortcut k r+3^oddCount r k*q) h
  change (∃ j : Nat, j<=k+h ∧
     Terminal (iter shortcut j (r+2^k*q))) ↔ _
  exact hs.trans
    ((show Terminal (iter shortcut (k+h) (r+2^k*q)) ↔
      Terminal (iter shortcut h
        (iter shortcut k r+3^oddCount r k*q)) by
      rw [v166_actual_clock_shift]).trans ht.symm)

/-- An executable finite population count for decidable Bool
    evidence, not an opaque count over an unknown future class. -/
def v166CountBool (P : Nat → Bool) : Nat → Nat
  | 0 => 0
  | Q+1 => v166CountBool P Q + (if P Q then 1 else 0)

theorem v166_count_bool_ext
    (P Q : Nat → Bool) (h : ∀ q, P q=Q q) :
    ∀ X : Nat, v166CountBool P X=v166CountBool Q X := by
  intro X
  induction X with
  | zero => rfl
  | succ X ih =>
      simp only [v166CountBool,ih,h X]

/-- FINITE CLOCK CERTIFICATE MASS, exactly transported across
    the dyadic original-source and ternary future-endpoint charts.
    Equal integer counts, not a statistical or spectral claim. -/
theorem v166_terminal_certificate_count_transport
    (r k h Q : Nat) :
    v166CountBool
      (fun q => v166HitBool (k+h) (r+2^k*q)) Q =
    v166CountBool
      (fun q => v166HitBool h
        (iter shortcut k r+3^oddCount r k*q)) Q := by
  apply v166_count_bool_ext
  intro q
  exact v166_actual_hit_bool_transport r k h q

/-- The currently unresolved finite CLOCK survivors also transport
    without losing a single original source identity. -/
theorem v166_timeout_count_transport
    (r k h Q : Nat) :
    Q-v166CountBool
      (fun q => v166HitBool (k+h) (r+2^k*q)) Q =
    Q-v166CountBool
      (fun q => v166HitBool h
        (iter shortcut k r+3^oddCount r k*q)) Q := by
  rw [v166_terminal_certificate_count_transport]

/-- A proof-carrying, strictly smaller positive source p remains
    a true two-clock merger after the source-prefix normalization.
    No earlier-source witness is invented by the conversion. -/
theorem v166_compiled_earlier_source_join
    (r k q h j p : Nat)
    (hCap : p<r+2^k*q)
    (hEndpoint :
      iter shortcut h
        (iter shortcut k r+3^oddCount r k*q) =
      iter shortcut j p) :
    LowerMerge shortcut (r+2^k*q) p := by
  refine ⟨hCap,k+h,j,?_⟩
  exact (v166_actual_clock_shift r k h q).trans hEndpoint

/-- STATEFUL PROOF REUSE CONTROL (V133): the clocked affine
    chart compiler reconstructs the existing true all-offset
    23 -> (3+54t) source-capped two-clock relation, without
    assuming either family already converges or appealing to
    the generic V131 chart theorem. -/
theorem v166_root23_family_reconstructed (t : Nat) :
    LowerMerge shortcut (23+384*t) (3+54*t) := by
  have hCap : 3+54*t < 23+2^7*(3*t) := by
    norm_num
    omega
  have hBase : iter shortcut 7 23=5 := by decide
  have hOddCount : oddCount 23 7=3 := by decide
  have hEarlier : iter shortcut 1 (3+54*t)=5+81*t := by
    change shortcut (3+54*t)=5+81*t
    have hOdd : (3+54*t)%2≠0 := by omega
    simp only [shortcut,hOdd,ite_false]
    omega
  have hEndpoint :
      iter shortcut 0
        (iter shortcut 7 23+3^oddCount 23 7*(3*t)) =
        iter shortcut 1 (3+54*t) := by
    simp only [iter,hBase,hOddCount,hEarlier]
    omega
  have hMerge :=
    v166_compiled_earlier_source_join
      23 7 (3*t) 0 1 (3+54*t) hCap hEndpoint
  have hSource : 23+2^7*(3*t)=23+384*t := by
    norm_num
    omega
  simpa only [hSource] using hMerge

#print axioms v166_hit_bool_semantics
#print axioms v166_actual_clock_shift
#print axioms v166_actual_hit_bool_transport
#print axioms v166_hit_by_horizon_source_to_endpoint
#print axioms v166_count_bool_ext
#print axioms v166_terminal_certificate_count_transport
#print axioms v166_timeout_count_transport
#print axioms v166_compiled_earlier_source_join
#print axioms v166_root23_family_reconstructed

end SourceProduct
end CollatzFinal
