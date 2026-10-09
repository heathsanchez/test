import Collatz.ScaledReverseMerger

namespace CollatzFinal
namespace SourceProduct

/-
V113: compress 1701 bounded CRT candidate witnesses to three exact
unbounded congruence-cylinder lower-source merger laws.

These are uniform for every natural offset q. They are NOT a
universal natural-source cover or a global Collatz proof.
Each reverse step carries its exact arithmetic equations.
-/

/-- Reverse word EEOEOOOOOO, from endpoint 410+2187*q to 191+1024*q. -/
theorem v113_a_reverse_word :
    AffineReverse 410 2187 191 1024 10 := by
  have h0 : AffineReverse 410 2187 410 2187 0 :=
    AffineReverse.seed 410 2187
  have h1 : AffineReverse 410 2187 820 4374 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 410 2187 1640 8748 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 410 2187 1093 5832 3 :=
    AffineReverse.odd h2 1093 5832 (by decide) (by decide)
  have h4 : AffineReverse 410 2187 2186 11664 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 410 2187 1457 7776 5 :=
    AffineReverse.odd h4 1457 7776 (by decide) (by decide)
  have h6 : AffineReverse 410 2187 971 5184 6 :=
    AffineReverse.odd h5 971 5184 (by decide) (by decide)
  have h7 : AffineReverse 410 2187 647 3456 7 :=
    AffineReverse.odd h6 647 3456 (by decide) (by decide)
  have h8 : AffineReverse 410 2187 431 2304 8 :=
    AffineReverse.odd h7 431 2304 (by decide) (by decide)
  have h9 : AffineReverse 410 2187 287 1536 9 :=
    AffineReverse.odd h8 287 1536 (by decide) (by decide)
  exact AffineReverse.odd h9 191 1024 (by decide) (by decide)

/-- For EVERY q≥0 the source 273+1458*q has a strictly smaller
    positive coalescent 191+1024*q, with exact clocks (1,10). -/
theorem v113_a_source_merge (q : Nat) :
    LowerMerge shortcut (273 + 1458 * q) (191 + 1024 * q) := by
  have he : iter shortcut 1 273 = 410 := by decide
  have hs :
      (2 ^ 0 * 3 ^ oddCount 273 1) * 729 = 2187 := by decide
  have hw :
      AffineReverse
        (iter shortcut 1 273)
        ((2 ^ 0 * 3 ^ oddCount 273 1) * 729)
        191 1024 10 := by
    simpa only [he, hs] using v113_a_reverse_word
  have hm : (2 ^ (1 + 0) * 729) = (1458 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    273 1 0 729 q 191 1024 10 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v113_a_reverse_word
#print axioms v113_a_source_merge

/-- Reverse word EEOOEOOOOO, from endpoint 1982+2187*q to 927+1024*q. -/
theorem v113_b_reverse_word :
    AffineReverse 1982 2187 927 1024 10 := by
  have h0 : AffineReverse 1982 2187 1982 2187 0 :=
    AffineReverse.seed 1982 2187
  have h1 : AffineReverse 1982 2187 3964 4374 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 1982 2187 7928 8748 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 1982 2187 5285 5832 3 :=
    AffineReverse.odd h2 5285 5832 (by decide) (by decide)
  have h4 : AffineReverse 1982 2187 3523 3888 4 :=
    AffineReverse.odd h3 3523 3888 (by decide) (by decide)
  have h5 : AffineReverse 1982 2187 7046 7776 5 :=
    AffineReverse.even h4
  have h6 : AffineReverse 1982 2187 4697 5184 6 :=
    AffineReverse.odd h5 4697 5184 (by decide) (by decide)
  have h7 : AffineReverse 1982 2187 3131 3456 7 :=
    AffineReverse.odd h6 3131 3456 (by decide) (by decide)
  have h8 : AffineReverse 1982 2187 2087 2304 8 :=
    AffineReverse.odd h7 2087 2304 (by decide) (by decide)
  have h9 : AffineReverse 1982 2187 1391 1536 9 :=
    AffineReverse.odd h8 1391 1536 (by decide) (by decide)
  exact AffineReverse.odd h9 927 1024 (by decide) (by decide)

/-- For EVERY q≥0 the source 1321+1458*q has a strictly smaller
    positive coalescent 927+1024*q, with exact clocks (1,10). -/
theorem v113_b_source_merge (q : Nat) :
    LowerMerge shortcut (1321 + 1458 * q) (927 + 1024 * q) := by
  have he : iter shortcut 1 1321 = 1982 := by decide
  have hs :
      (2 ^ 0 * 3 ^ oddCount 1321 1) * 729 = 2187 := by decide
  have hw :
      AffineReverse
        (iter shortcut 1 1321)
        ((2 ^ 0 * 3 ^ oddCount 1321 1) * 729)
        927 1024 10 := by
    simpa only [he, hs] using v113_b_reverse_word
  have hm : (2 ^ (1 + 0) * 729) = (1458 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1321 1 0 729 q 927 1024 10 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v113_b_reverse_word
#print axioms v113_b_source_merge

/-- Reverse word EEOOOEOOOO, from endpoint 2153+2187*q to 1007+1024*q. -/
theorem v113_c_reverse_word :
    AffineReverse 2153 2187 1007 1024 10 := by
  have h0 : AffineReverse 2153 2187 2153 2187 0 :=
    AffineReverse.seed 2153 2187
  have h1 : AffineReverse 2153 2187 4306 4374 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 2153 2187 8612 8748 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 2153 2187 5741 5832 3 :=
    AffineReverse.odd h2 5741 5832 (by decide) (by decide)
  have h4 : AffineReverse 2153 2187 3827 3888 4 :=
    AffineReverse.odd h3 3827 3888 (by decide) (by decide)
  have h5 : AffineReverse 2153 2187 2551 2592 5 :=
    AffineReverse.odd h4 2551 2592 (by decide) (by decide)
  have h6 : AffineReverse 2153 2187 5102 5184 6 :=
    AffineReverse.even h5
  have h7 : AffineReverse 2153 2187 3401 3456 7 :=
    AffineReverse.odd h6 3401 3456 (by decide) (by decide)
  have h8 : AffineReverse 2153 2187 2267 2304 8 :=
    AffineReverse.odd h7 2267 2304 (by decide) (by decide)
  have h9 : AffineReverse 2153 2187 1511 1536 9 :=
    AffineReverse.odd h8 1511 1536 (by decide) (by decide)
  exact AffineReverse.odd h9 1007 1024 (by decide) (by decide)

/-- For EVERY q≥0 the source 1275+1296*q has a strictly smaller
    positive coalescent 1007+1024*q, with exact clocks (4,10). -/
theorem v113_c_source_merge (q : Nat) :
    LowerMerge shortcut (1275 + 1296 * q) (1007 + 1024 * q) := by
  have he : iter shortcut 4 1275 = 2153 := by decide
  have hs :
      (2 ^ 0 * 3 ^ oddCount 1275 4) * 81 = 2187 := by decide
  have hw :
      AffineReverse
        (iter shortcut 4 1275)
        ((2 ^ 0 * 3 ^ oddCount 1275 4) * 81)
        1007 1024 10 := by
    simpa only [he, hs] using v113_c_reverse_word
  have hm : (2 ^ (4 + 0) * 81) = (1296 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1275 4 0 81 q 1007 1024 10 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v113_c_reverse_word
#print axioms v113_c_source_merge

end SourceProduct
end CollatzFinal
