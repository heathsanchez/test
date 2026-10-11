import Collatz.BinaryTernaryClassMassTransfer

namespace CollatzFinal
namespace SourceProduct

/-!
V177 — UNIVERSAL SOURCE-ATTACHED PARALLEL AFFINE MEETING COMPILER.

For ANY real two-clock equality T^i(n)=T^j(p), the already
kernel-qualified V160 all-source binary→ternary exact affine law
compiles an INFINITE family of actual two-clock equalities using
the two independently checked odd counts a=oddCount(n,i) and
b=oddCount(p,j):

 T^i(n+2^i*3^b*w) = T^j(p+2^j*3^a*w), ALL w.

If the source slope 2^i*3^b exceeds the companion slope 2^j*3^a,
the companion is strictly earlier for every w>=p+1, producing a
genuine source-capped LowerMerge witness WITHOUT recomputing any
individual trajectory.

THIS IS NOT A TERMINAL CERTIFICATE. Its smaller source might itself
belong to a bad future class. The same purely affine mechanism
works in generalized 3n+c maps with multiple basins. No
density contraction, no all-source finite generation and no QED
are claimed from it. Global Collatz UNKNOWN.
-/

/-- ALL source lifts of ANY authentic equality, not just the 17
cached families or one sampled source. Each clock and every starting
source is retained verbatim in the theorem statement. -/
theorem v177_parallel_source_affine_meeting
    (n p i j w : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p) :
    iter shortcut i
      (n + 2^i*(3^(oddCount p j)*w)) =
    iter shortcut j
      (p + 2^j*(3^(oddCount n i)*w)) := by
  calc
    iter shortcut i
        (n + 2^i*(3^(oddCount p j)*w)) =
      iter shortcut i n +
        3^(oddCount n i)*(3^(oddCount p j)*w) :=
      v160_exact_cylinder_affine i n (3^(oddCount p j)*w)
    _ = iter shortcut j p +
        3^(oddCount p j)*(3^(oddCount n i)*w) := by
      rw [hMeet]
      ac_rfl
    _ = iter shortcut j
        (p + 2^j*(3^(oddCount n i)*w)) := by
      symm
      exact v160_exact_cylinder_affine j p (3^(oddCount n i)*w)

/-- When the FIRST lifted source grows strictly faster in source
HEIGHT than the second, increasing the shared nonnegative lift
parameter yields a STRICTLY SMALLER genuine source-capped
future-coalescence certificate.

The base meeting equality must be supplied as independent evidence.
The theorem does not assert that the smaller source is good. -/
theorem v177_infinite_source_capped_meetings
    (n p i j w : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hSlope :
       2^j*3^(oddCount n i) <
         2^i*3^(oddCount p j)) :
    LowerMerge shortcut
      (n + 2^i*(3^(oddCount p j)*(p+1+w)))
      (p + 2^j*(3^(oddCount n i)*(p+1+w))) := by
  let Lsmall : Nat := 2^j*3^(oddCount n i)
  let Llarge : Nat := 2^i*3^(oddCount p j)
  let W : Nat := p+1+w
  have hs : Lsmall+1 ≤ Llarge := by
    dsimp [Lsmall,Llarge]
    omega
  have hm : (Lsmall+1)*W ≤ Llarge*W :=
    Nat.mul_le_mul_right W hs
  have he : Lsmall*W + W ≤ Llarge*W := by
    simpa [Nat.add_mul] using hm
  have hw : p+1 ≤ W := by dsimp [W]; omega
  have hCap' : p+Lsmall*W < n+Llarge*W := by omega
  have hCap :
      p + 2^j*(3^(oddCount n i)*W) <
      n + 2^i*(3^(oddCount p j)*W) := by
    simpa only [Lsmall,Llarge,Nat.mul_assoc] using hCap'
  refine ⟨hCap,i,j,?_⟩
  exact v177_parallel_source_affine_meeting n p i j W hMeet

/-- The qualified root23/3 all-offset source-capped family is
reconstructed from ONE checked meeting, no per-offset search.
A wider source-dependent theorem is not inferred from a finite run. -/
theorem v177_root23_recompiled_from_single_meeting
    (w : Nat) :
    LowerMerge shortcut (23+384*w) (3+54*w) := by
  have hMeet : iter shortcut 7 23 = iter shortcut 1 3 := by decide
  have hOne : oddCount 3 1 = 1 := by decide
  have hThree : oddCount 23 7 = 3 := by decide
  have hAffine :=
    v177_parallel_source_affine_meeting 23 3 7 1 w hMeet
  have hSame :
      iter shortcut 7 (23+384*w) =
      iter shortcut 1 (3+54*w) := by
    simpa [hOne, hThree, ← Nat.mul_assoc] using hAffine
  have hCap : 3+54*w < 23+384*w := by omega
  exact ⟨hCap,7,1,hSame⟩

/-- One qualified source meeting with a strict lifted source-slope gap
eliminates an INFINITE family of candidates for the LEAST genuine
positive Collatz counterexample. This is the precise elimination
interpretation of the affine compiler.

The proof uses the independently warranted universal fact that a
minimal bad source cannot join ANY strictly earlier positive source
at two genuine clocks; NO assumption that all numbers converge. -/
theorem v177_slope_lift_excludes_least_positive_bad
    (n p i j w : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hSlope :
       2^j*3^(oddCount n i) <
         2^i*3^(oddCount p j)) :
    ¬ MinimalBad PositiveBad
      (n + 2^i*(3^(oddCount p j)*(p+1+w))) := by
  intro hBad
  obtain ⟨hLess, u, v, hEq⟩ :=
    v177_infinite_source_capped_meetings n p i j w hMeet hSlope
  have hTwo : 0 < 2^j := Nat.pow_pos (by decide)
  have hThree : 0 < 3^(oddCount n i) := Nat.pow_pos (by decide)
  have hW : 0 < p+1+w := by omega
  have hSmallPos :
      0 < p + 2^j*(3^(oddCount n i)*(p+1+w)) := by
    have hpPart :
        0 < 2^j*(3^(oddCount n i)*(p+1+w)) :=
      Nat.mul_pos hTwo (Nat.mul_pos hThree hW)
    omega
  exact (minimal_positive_bad_no_earlier_source_meeting
      hBad
      (p + 2^j*(3^(oddCount n i)*(p+1+w)))
      u v hSmallPos hLess) hEq

/-- A concrete certified infinite excluded least-bad progression,
already contained in V134's earlier rooted family. Its significance
is that the *generic* V177 compiler now derives the same conclusion
from an independently checkable two-clock source meeting. -/
theorem v177_root23_progression_excludes_minimal_bad
    (w : Nat) :
    ¬ MinimalBad PositiveBad (23+384*w) := by
  intro hBad
  obtain ⟨hLess, i, j, hEq⟩ :=
    v177_root23_recompiled_from_single_meeting w
  have hSmallPos : 0 < 3+54*w := by omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (3+54*w) i j hSmallPos hLess) hEq

/-- If the verified BASE source is already greater than its
verified companion, a nonnegative source-slope ordering suffices to
retain a strict positive-source reduction at EVERY w>=0, with no
artificial shift by p+1. This is the exact reusable constructor for
ordinary rooted arithmetic progressions. -/
theorem v177_unshifted_ordered_affine_lower_merge
    (n p i j w : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hBase : p < n)
    (hSlope :
       2^j*3^(oddCount n i) ≤
         2^i*3^(oddCount p j)) :
    LowerMerge shortcut
      (n + 2^i*(3^(oddCount p j)*w))
      (p + 2^j*(3^(oddCount n i)*w)) := by
  have hScaled :
      (2^j*3^(oddCount n i))*w ≤
        (2^i*3^(oddCount p j))*w :=
    Nat.mul_le_mul_right w hSlope
  have hStrict :
      p + (2^j*3^(oddCount n i))*w <
        n + (2^i*3^(oddCount p j))*w := by omega
  have hCap :
      p + 2^j*(3^(oddCount n i)*w) <
        n + 2^i*(3^(oddCount p j)*w) := by
    simpa only [Nat.mul_assoc] using hStrict
  exact ⟨hCap,i,j,
    v177_parallel_source_affine_meeting n p i j w hMeet⟩

/-- A genuine n=21, p=3 meeting eliminates every 21+72*w from
being a least bad source. This says nothing about arbitrary other
source classes. -/
theorem v177_root21_progression_excludes_minimal_bad
    (w : Nat) :
    ¬ MinimalBad PositiveBad (21+72*w) := by
  have hMeet : iter shortcut 3 21 = iter shortcut 2 3 := by decide
  have hCount21 : oddCount 21 3 = 1 := by decide
  have hCount3 : oddCount 3 2 = 2 := by decide
  have hSlope :
      2^2*3^(oddCount 21 3) ≤ 2^3*3^(oddCount 3 2) := by
    rw [hCount21,hCount3]
    decide
  have hRaw :=
    v177_unshifted_ordered_affine_lower_merge
      21 3 3 2 w hMeet (by decide) hSlope
  have hLM : LowerMerge shortcut (21+72*w) (3+12*w) := by
    simpa [hCount21,hCount3,← Nat.mul_assoc] using hRaw
  intro hBad
  obtain ⟨hLess, i, j, hEq⟩ := hLM
  have hPos : 0<3+12*w := by omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (3+12*w) i j hPos hLess) hEq

/-- Same unbounded least-bad-source exclusion from the previously
qualified real source9/7 two-clock meeting. -/
theorem v177_root9_progression_excludes_minimal_bad
    (w : Nat) :
    ¬ MinimalBad PositiveBad (9+1728*w) := by
  have hMeet : iter shortcut 6 9 = iter shortcut 4 7 := by decide
  have hCount9 : oddCount 9 6 = 4 := by decide
  have hCount7 : oddCount 7 4 = 3 := by decide
  have hSlope :
      2^4*3^(oddCount 9 6) ≤ 2^6*3^(oddCount 7 4) := by
    rw [hCount9,hCount7]
    decide
  have hRaw :=
    v177_unshifted_ordered_affine_lower_merge
      9 7 6 4 w hMeet (by decide) hSlope
  have hLM : LowerMerge shortcut (9+1728*w) (7+1296*w) := by
    simpa [hCount9,hCount7,← Nat.mul_assoc] using hRaw
  intro hBad
  obtain ⟨hLess, i, j, hEq⟩ := hLM
  have hPos : 0<7+1296*w := by omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (7+1296*w) i j hPos hLess) hEq

#print axioms v177_unshifted_ordered_affine_lower_merge
#print axioms v177_root21_progression_excludes_minimal_bad
#print axioms v177_root9_progression_excludes_minimal_bad

#print axioms v177_slope_lift_excludes_least_positive_bad
#print axioms v177_root23_progression_excludes_minimal_bad

#print axioms v177_parallel_source_affine_meeting
#print axioms v177_infinite_source_capped_meetings
#print axioms v177_root23_recompiled_from_single_meeting

end SourceProduct
end CollatzFinal
