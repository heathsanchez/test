import Collatz.ReverseAffineMerger

namespace CollatzFinal
namespace SourceProduct

/-- Consequence-directed schema for *any* exact symbolic reverse word:
    source a+M*s shares an actual future with the smaller p+c*s.
    No local trajectory-rank assumption is required. -/
theorem reverse_family_lower_merge
    (a M p c t s : Nat)
    (hw : AffineReverse a M p c t)
    (hbase : p < a)
    (hcoef : c ≤ M) :
    LowerMerge shortcut (a + M * s) (p + c * s) := by
  have hs := Nat.mul_le_mul_right s hcoef
  have hlt : p + c * s < a + M * s := by omega
  refine ⟨hlt, 0, t, ?_⟩
  simpa [iter] using (affine_reverse_sound hw s).symm

/-- The one-step ternary inverse-odd cone gives genuine lower-source merger. -/
theorem ternary_inverse_odd_lower_merge (s : Nat) :
    LowerMerge shortcut (3 * s + 2) (2 * s + 1) := by
  have hstep : shortcut (2 * s + 1) = 3 * s + 2 :=
    exact_inverse_odd_step (3 * s + 2) (2 * s + 1) (by omega)
  refine ⟨by omega, 0, 1, ?_⟩
  simpa [iter] using hstep.symm

/-- A six-step executed reverse word from 10+81*s to 7+64*s.
    Reverse sequence E O E O O O is arithmetically exact. -/
theorem q7_source_reverse_word :
    AffineReverse 10 81 7 64 6 := by
  have h0 : AffineReverse 10 81 10 81 0 :=
    AffineReverse.seed 10 81
  have h1 : AffineReverse 10 81 20 162 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 10 81 13 108 2 :=
    AffineReverse.odd h1 13 108 (by decide) (by decide)
  have h3 : AffineReverse 10 81 26 216 3 :=
    AffineReverse.even h2
  have h4 : AffineReverse 10 81 17 144 4 :=
    AffineReverse.odd h3 17 144 (by decide) (by decide)
  have h5 : AffineReverse 10 81 11 96 5 :=
    AffineReverse.odd h4 11 96 (by decide) (by decide)
  exact AffineReverse.odd h5 7 64 (by decide) (by decide)

/-- This is not inferred from a bounded sample: the abstract reverse-word
    theorem forces a smaller-source future coalescence for every s. -/
theorem q7_source_lower_merge (s : Nat) :
    LowerMerge shortcut (81 * s + 10) (64 * s + 7) := by
  simpa [Nat.add_comm] using
    (reverse_family_lower_merge 10 81 7 64 6 s
      q7_source_reverse_word (by decide) (by decide))

/-- A hypothetical least positive counterexample cannot lie in the
    immediate inverse-odd ternary class. This is an exclusion of a
    *minimal bad source*, not a standalone termination proof for every
    n in the class without a smaller-source induction premise. -/
theorem minimal_bad_not_ternary_two {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n % 3 ≠ 2 := by
  intro hmod
  let s := n / 3
  have heq : n = 3 * s + 2 := by
    dsimp [s]
    omega
  have hm : LowerMerge shortcut n (2 * s + 1) := by
    rw [heq]
    exact ternary_inverse_odd_lower_merge s
  exact positive_minimal_no_lower_merge hmin (2 * s + 1) (by omega) hm

/-- The q7 reverse-word certificate also forbids its whole source
    congruence class as the least possible bad positive source. -/
theorem minimal_bad_not_q7_class {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n % 81 ≠ 10 := by
  intro hmod
  let s := n / 81
  have heq : n = 81 * s + 10 := by
    dsimp [s]
    omega
  have hm : LowerMerge shortcut n (64 * s + 7) := by
    rw [heq]
    exact q7_source_lower_merge s
  exact positive_minimal_no_lower_merge hmin (64 * s + 7) (by omega) hm

#print axioms minimal_bad_not_ternary_two
#print axioms minimal_bad_not_q7_class

#print axioms reverse_family_lower_merge
#print axioms ternary_inverse_odd_lower_merge
#print axioms q7_source_reverse_word
#print axioms q7_source_lower_merge

end SourceProduct
end CollatzFinal
