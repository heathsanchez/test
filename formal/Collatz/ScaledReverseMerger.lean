import Collatz.Q7SourceMerger

namespace CollatzFinal
namespace SourceProduct

/-- Exact parity-prefix shift after scaling the dyadic cylinder by an
    arbitrary natural multiplier; V112 uses multiplier 3^7. -/
theorem parity_scaled_prefix_shift (r j h m q : Nat) :
    iter shortcut j (r + (2 ^ (j+h) * m) * q) =
      iter shortcut j r + ((2 ^ h * 3 ^ oddCount r j) * m) * q := by
  have hx := parity_prefix_shift r j h (m*q)
  simpa [Nat.mul_assoc] using hx

/-- Every genuine symbolic reverse path on a scaled source cylinder
    gives a future-coalescent strictly earlier source, for every q.
    Its premises are exact arithmetic, not sampled trajectory tests. -/
theorem scaled_reverse_lower_merge
    (r j h m q p c t : Nat)
    (hw : AffineReverse
       (iter shortcut j r)
       ((2 ^ h * 3 ^ oddCount r j) * m) p c t)
    (hbelow : p < r)
    (hslope : c ≤ 2 ^ (j+h) * m) :
    LowerMerge shortcut
      (r + (2 ^ (j+h) * m) * q) (p + c * q) := by
  have hmul := Nat.mul_le_mul_right q hslope
  have hlt : p + c*q < r + (2 ^ (j+h) * m)*q := by omega
  refine ⟨hlt,j,t,?_⟩
  calc
    iter shortcut j (r + (2 ^ (j+h)*m)*q) =
        iter shortcut j r + ((2 ^ h * 3 ^ oddCount r j)*m)*q :=
          parity_scaled_prefix_shift r j h m q
    _ = iter shortcut t (p + c*q) := (affine_reverse_sound hw q).symm

/-- An independently recorded V112 certificate.
    Actual prefix shortcut^4(6991899)=11798831, followed by the
    exact ten-step reverse word EEOOOEOOOO to 5524463. -/
theorem v112_example_reverse_word :
    AffineReverse 11798831 15116544 5524463 7077888 10 := by
  have h0 : AffineReverse 11798831 15116544 11798831 15116544 0 :=
    AffineReverse.seed 11798831 15116544
  have h1 : AffineReverse 11798831 15116544 23597662 30233088 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 11798831 15116544 47195324 60466176 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 11798831 15116544 31463549 40310784 3 :=
    AffineReverse.odd h2 31463549 40310784 (by decide) (by decide)
  have h4 : AffineReverse 11798831 15116544 20975699 26873856 4 :=
    AffineReverse.odd h3 20975699 26873856 (by decide) (by decide)
  have h5 : AffineReverse 11798831 15116544 13983799 17915904 5 :=
    AffineReverse.odd h4 13983799 17915904 (by decide) (by decide)
  have h6 : AffineReverse 11798831 15116544 27967598 35831808 6 :=
    AffineReverse.even h5
  have h7 : AffineReverse 11798831 15116544 18645065 23887872 7 :=
    AffineReverse.odd h6 18645065 23887872 (by decide) (by decide)
  have h8 : AffineReverse 11798831 15116544 12430043 15925248 8 :=
    AffineReverse.odd h7 12430043 15925248 (by decide) (by decide)
  have h9 : AffineReverse 11798831 15116544 8286695 10616832 9 :=
    AffineReverse.odd h8 8286695 10616832 (by decide) (by decide)
  exact AffineReverse.odd h9 5524463 7077888 (by decide) (by decide)

/-- All positive offsets in this entire CRT family coalesce with
    an explicitly smaller positive source. Not a global Collatz theorem. -/
theorem v112_example_all_offsets (q : Nat) :
    LowerMerge shortcut
      (6991899 + 8957952*q) (5524463 + 7077888*q) := by
  have he : iter shortcut 4 6991899 = 11798831 := by decide
  have hs : (2 ^ 8 * 3 ^ oddCount 6991899 4) * 2187 = 15116544 := by decide
  have hword :
      AffineReverse
        (iter shortcut 4 6991899)
        ((2 ^ 8 * 3 ^ oddCount 6991899 4) * 2187)
        5524463 7077888 10 := by
    simpa only [he, hs] using v112_example_reverse_word
  have h := scaled_reverse_lower_merge 6991899 4 8 2187 q
    5524463 7077888 10 hword (by decide) (by decide)
  have hm : (2 ^ (4+8) * 2187) = (8957952 : Nat) := by decide
  simpa only [hm] using h

#print axioms parity_scaled_prefix_shift
#print axioms scaled_reverse_lower_merge
#print axioms v112_example_reverse_word
#print axioms v112_example_all_offsets

end SourceProduct
end CollatzFinal
