import Collatz.MersenneJointResidualBarrier
import Collatz.ParallelMeetingAffineCompiler

set_option maxRecDepth 16384

namespace CollatzFinal
namespace SourceProduct

/-!
V183 — REPAIR THE FIRST V178/V181 JOINT MERSENNE RESIDUAL
AND COMPILE AN INFINITE LEAST-BAD SOURCE REDUCTION FAMILY.

The source n0=2^21-1=2097151 is irreducible under the FIRST
205-rule V178 bank by a separately exact modular audit, but it
actually reaches terminal2 at real clock193 with 109 genuine
odd transitions. From this independently checkable single
terminal-seeded meeting, the universally verified V177 affine
source law compiles ALL nonnegative offset meetings:

 T^193(2097151 + 2^193*w) = 2+3^109*w.

Since 2^193>3^109 and 2097151>2, the companion source is
STRICTLY SMALLER for ALL w>=0. Hence none of these original
source positions can be a hypothetical LEAST positive bad source.

IMPORTANT: The companion 2+3^109*w for w>0 is not known terminal
by this construction. The new family excludes LEAST-bad positions,
not arbitrary actual bad sources. It does NOT cover the entire
V182 infinite Mersenne residual exponent subfamily.

Global Collatz UNKNOWN — NO QED.
-/

/-- Exact genuine original-source/clock seed meeting. -/
theorem v183_real_mersenne_seed_meets_two :
    iter shortcut 193 2097151 = iter shortcut 0 2 := by
  decide

/-- Exact odd-count of the REAL original 193-clock Mersenne
trajectory, not a probabilistic word or heuristic estimate. -/
theorem v183_real_mersenne_seed_odd_count :
    oddCount 2097151 193 = 109 := by
  decide

/-- The new original-source increment is strictly larger
than the resulting companion increment, so strict source
ordering cannot be lost by arbitrarily many offsets. -/
theorem v183_mersenne_source_slope_strict :
    3^109 < 2^193 := by decide

/-- A single independently checked genuine terminal-seeded
meeting compiles a symbolic TRUE shortcut source family for
ALL natural offsets with no per-offset search. -/
theorem v183_mersenne_seed_affine_meeting
    (w : Nat) :
    iter shortcut 193 (2097151+2^193*w) =
      2+3^109*w := by
  have hMeet := v183_real_mersenne_seed_meets_two
  have hOdd := v183_real_mersenne_seed_odd_count
  have hLift :=
    v177_parallel_source_affine_meeting
      2097151 2 193 0 w hMeet
  simpa [hOdd, Nat.mul_assoc] using hLift

/-- The source-rank guard is independent of offset. -/
theorem v183_all_offsets_strict_earlier_source
    (w : Nat) :
    0 < 2+3^109*w ∧
    2+3^109*w < 2097151+2^193*w := by
  have hs : 3^109<=2^193 :=
    Nat.le_of_lt v183_mersenne_source_slope_strict
  have hm : 3^109*w <= 2^193*w :=
    Nat.mul_le_mul_right w hs
  constructor <;> omega

/-- A qualified family of genuine two-clock
strict-original-source LowerMerge proof terms. -/
theorem v183_repaired_residual_source_lower_merge
    (w : Nat) :
    LowerMerge shortcut
      (2097151+2^193*w)
      (2+3^109*w) := by
  have hh := v183_all_offsets_strict_earlier_source w
  refine ⟨hh.2,193,0,?_⟩
  simpa only [iter] using v183_mersenne_seed_affine_meeting w

/-- Infinite family EXCLUDED only as the position of the
hypothetical least positive bad source. This is not terminal
certification of every lifted source. -/
theorem v183_repaired_residual_excludes_least_positive_bad
    (w : Nat) :
    ¬ MinimalBad PositiveBad (2097151+2^193*w) := by
  intro hBad
  obtain ⟨hLess,i,j,hEq⟩ :=
    v183_repaired_residual_source_lower_merge w
  have hPos := (v183_all_offsets_strict_earlier_source w).1
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (2+3^109*w) i j hPos hLess) hEq

/-- The unlifted original seed is ACTUALLY terminal-certified,
while lifted companions for w>0 have no terminal assumption. -/
theorem v183_original_source_good :
    CollatzGood 2097151 := by
  simpa only [] using v182_smallest_joint_residual_is_actually_good

#print axioms v183_real_mersenne_seed_meets_two
#print axioms v183_real_mersenne_seed_odd_count
#print axioms v183_mersenne_source_slope_strict
#print axioms v183_mersenne_seed_affine_meeting
#print axioms v183_all_offsets_strict_earlier_source
#print axioms v183_repaired_residual_source_lower_merge
#print axioms v183_repaired_residual_excludes_least_positive_bad
#print axioms v183_original_source_good

end SourceProduct
end CollatzFinal
