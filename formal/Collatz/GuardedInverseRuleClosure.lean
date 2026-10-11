import Collatz.SparseFutureNormalForm

namespace CollatzFinal
namespace SourceProduct

set_option maxRecDepth 8192
set_option maxHeartbeats 40000000

/-!
V180 — GUARDED INVERSE RULE COMPILER THAT COMPOUNDS REAL CAPABILITIES.

V179's deterministic first-applicable normalizer sends an irreducible
odd source's immediate successor back to that same source, an
INFORMATION-FREE self-return. The missing distinction is to search
*all* independently qualified source meeting rules at the successor.

V180 derives a NEW source-lower family from a genuine predecessor
u of an independently certified prior source s:

  T(u)=s; T^i(s)=p; 0<p<u;
  => T^(i+1)(u)=p.

The independently kernel-verified V160 all-source +1 law then
promotes that base witness to an infinite source-locked family:

  T^(i+1)(u+2^(i+1)*w)
      = p + 3^oddCount(u,i+1)*w

for ALL natural w; if the smaller-source slope is <= 2^(i+1),
every lifted source has a genuinely strictly earlier positive
companion, excluding that ENTIRE progression as a candidate for the
LEAST bad original source.

29 numeric certified records are independently reconstructed by
guarded original-source reverse preimages from the V178 bank. Each
base predecessor, prior genuine meeting, strict source guard and
lifted slope are rechecked in Lean using exact 'by decide' proofs.

This does NOT classify any of these sources as globally terminal
without an independent good seed. Every conclusion is source-relative,
not Collatz QED.  Global Collatz UNKNOWN.
-/

structure V180CertifiedInverseSeed where
  source : Nat
  priorSource : Nat
  earlier : Nat
  priorClock : Nat
  earlierPositive : 0 < earlier
  earlierSmaller : earlier < source
  genuineOddPredecessor : shortcut source = priorSource
  previousGenuineMeeting :
    iter shortcut priorClock priorSource = earlier
  liftedSourceSlopeDominates :
    3^(oddCount source (priorClock+1)) <= 2^(priorClock+1)

/-- Independently checked REAL two-clock certificate, not a
semantic label from an assumed bad/terminal basin. -/
theorem v180_seed_base_meeting (r : V180CertifiedInverseSeed) :
    iter shortcut (r.priorClock+1) r.source = r.earlier := by
  calc
    iter shortcut (r.priorClock+1) r.source =
        iter shortcut r.priorClock (shortcut r.source) := by rfl
    _ = iter shortcut r.priorClock r.priorSource := by
        rw [r.genuineOddPredecessor]
    _ = r.earlier := r.previousGenuineMeeting

/-- The exact new all-offset source-lower capability: a formal
construction for ALL w, not a bounded replay or guessed congruence. -/
theorem v180_inverse_seed_all_offsets_lower
    (r : V180CertifiedInverseSeed) (w : Nat) :
    LowerMerge shortcut
      (r.source + 2^(r.priorClock+1)*w)
      (r.earlier + 3^(oddCount r.source (r.priorClock+1))*w) := by
  have hScaled :
      3^(oddCount r.source (r.priorClock+1))*w <=
        2^(r.priorClock+1)*w :=
    Nat.mul_le_mul_right w r.liftedSourceSlopeDominates
  have hCap :
      r.earlier + 3^(oddCount r.source (r.priorClock+1))*w <
      r.source + 2^(r.priorClock+1)*w := by
    have hBase : r.earlier < r.source := r.earlierSmaller
    omega
  have hAll :
      iter shortcut (r.priorClock+1)
        (r.source+2^(r.priorClock+1)*w) =
      r.earlier+3^(oddCount r.source (r.priorClock+1))*w := by
    calc
      iter shortcut (r.priorClock+1)
          (r.source+2^(r.priorClock+1)*w) =
        iter shortcut (r.priorClock+1) r.source +
          3^(oddCount r.source (r.priorClock+1))*w :=
        v160_exact_cylinder_affine (r.priorClock+1) r.source w
      _ = r.earlier+3^(oddCount r.source (r.priorClock+1))*w := by
        rw [v180_seed_base_meeting r]
  exact ⟨hCap,r.priorClock+1,0,by
    simpa only [iter] using hAll⟩

/-- Only the LEAST hypothetical positive bad source is excluded.
An excluded source might, in principle, be nonterminal while its
smaller companion belongs to the same hypothetical bad class. -/
theorem v180_inverse_seed_excludes_least_bad
    (r : V180CertifiedInverseSeed) (w : Nat) :
    ¬ MinimalBad PositiveBad
      (r.source + 2^(r.priorClock+1)*w) := by
  intro hBad
  obtain ⟨hCap,i,j,hMeet⟩ :=
    v180_inverse_seed_all_offsets_lower r w
  have hPos :
      0 < r.earlier + 3^(oddCount r.source (r.priorClock+1))*w := by
    have hp := r.earlierPositive
    omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad
    (r.earlier + 3^(oddCount r.source (r.priorClock+1))*w)
    i j hPos hCap) hMeet

/-- The TRUE source qualification is encoded in each kernel-checkable
record below. The finite certificate bank is a candidate-position
sieve, not an oracle deciding all trajectories. -/
def v180GuardedInverseBank : List V180CertifiedInverseSeed := [
  ⟨5, 8, 4, 1, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨23, 35, 20, 4, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨175, 263, 167, 7, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨95, 143, 91, 7, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨39, 59, 38, 7, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨5615, 8423, 4498, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨255, 383, 205, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨5871, 8807, 4703, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨623, 935, 500, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨679, 1019, 545, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨3455, 5183, 2768, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨6559, 9839, 5254, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨1135, 1703, 910, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨1191, 1787, 955, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨3967, 5951, 3178, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨6815, 10223, 5459, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨4199, 6299, 3364, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨4223, 6335, 3383, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨1567, 2351, 1256, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨4455, 6683, 3569, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨1727, 2591, 1384, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨7399, 11099, 5927, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨1983, 2975, 1589, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨2079, 3119, 1666, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨2095, 3143, 1679, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨4927, 7391, 3947, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨7911, 11867, 6337, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨2607, 3911, 2089, 12, by decide, by decide, by decide, by decide, by decide⟩,
  ⟨5439, 8159, 4357, 12, by decide, by decide, by decide, by decide, by decide⟩
]

/-- Every member of the finite, independently checkable bank has a
genuine all-offset lower-source witness by one generic theorem. -/
theorem v180_bank_each_member_excludes_least_bad
    (r : V180CertifiedInverseSeed) (w : Nat)
    (_hMember : r ∈ v180GuardedInverseBank) :
    ¬ MinimalBad PositiveBad
      (r.source + 2^(r.priorClock+1)*w) :=
  v180_inverse_seed_excludes_least_bad r w

/-- A completely explicit NEW family involving residual source255,
missed by the original V178 source-clock cutoff i<=12. -/
theorem v180_mersenne255_guarded_inverse_family
    (w : Nat) :
    iter shortcut 13 (255+8192*w) = 205+6561*w := by
  have hBase : iter shortcut 13 255 = 205 := by decide
  have hOdd : oddCount 255 13 = 8 := by decide
  have hAffine := v160_exact_cylinder_affine 13 255 w
  simpa [hBase,hOdd,← Nat.mul_assoc] using hAffine

theorem v180_mersenne255_excludes_least_bad
    (w : Nat) :
    ¬ MinimalBad PositiveBad (255+8192*w) := by
  have hCap : 205+6561*w < 255+8192*w := by omega
  have hMeet := v180_mersenne255_guarded_inverse_family w
  intro hBad
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (205+6561*w) 13 0 (by omega) hCap)
    (by simpa only [iter] using hMeet)

#print axioms v180_seed_base_meeting
#print axioms v180_inverse_seed_all_offsets_lower
#print axioms v180_inverse_seed_excludes_least_bad
#print axioms v180_bank_each_member_excludes_least_bad
#print axioms v180_mersenne255_guarded_inverse_family
#print axioms v180_mersenne255_excludes_least_bad

end SourceProduct
end CollatzFinal
