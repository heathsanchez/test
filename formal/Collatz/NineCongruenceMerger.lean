import Collatz.ThreeCongruenceMerger

namespace CollatzFinal
namespace SourceProduct

/-
V114: Nine exact reverse-word laws, each with a 12-step lawful
shortcut predecessor and a one-step forward source prefix.

For all q>=0, shortcut(r + 4374*q) =
  iter shortcut 12 (s + 4096*q), with 0<s+4096*q<r+4374*q.
These are source-relative mergers, not universal Collatz closure.
-/

/-- Law a: EEOEOEOOOOOO; exact reverse family (2768,6561)->(1727,4096). -/
theorem v114_a_reverse_word :
    AffineReverse 2768 6561 1727 4096 12 := by
  have h0 : AffineReverse 2768 6561 2768 6561 0 :=
    AffineReverse.seed 2768 6561
  have h1 : AffineReverse 2768 6561 5536 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 2768 6561 11072 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 2768 6561 7381 17496 3 :=
    AffineReverse.odd h2 7381 17496 (by decide) (by decide)
  have h4 : AffineReverse 2768 6561 14762 34992 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 2768 6561 9841 23328 5 :=
    AffineReverse.odd h4 9841 23328 (by decide) (by decide)
  have h6 : AffineReverse 2768 6561 19682 46656 6 :=
    AffineReverse.even h5
  have h7 : AffineReverse 2768 6561 13121 31104 7 :=
    AffineReverse.odd h6 13121 31104 (by decide) (by decide)
  have h8 : AffineReverse 2768 6561 8747 20736 8 :=
    AffineReverse.odd h7 8747 20736 (by decide) (by decide)
  have h9 : AffineReverse 2768 6561 5831 13824 9 :=
    AffineReverse.odd h8 5831 13824 (by decide) (by decide)
  have h10 : AffineReverse 2768 6561 3887 9216 10 :=
    AffineReverse.odd h9 3887 9216 (by decide) (by decide)
  have h11 : AffineReverse 2768 6561 2591 6144 11 :=
    AffineReverse.odd h10 2591 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 1727 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_a_source_merge (q : Nat) :
    LowerMerge shortcut (1845 + 4374 * q) (1727 + 4096 * q) := by
  have he : iter shortcut 1 1845 = 2768 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 1845 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 1845)
        ((2 ^ 0 * 3 ^ oddCount 1845 1) * 2187)
        1727 4096 12 := by
    simpa only [he, hs] using v114_a_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1845 1 0 2187 q 1727 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_a_reverse_word
#print axioms v114_a_source_merge

/-- Law b: EEOEOOEOOOOO; exact reverse family (3947,6561)->(2463,4096). -/
theorem v114_b_reverse_word :
    AffineReverse 3947 6561 2463 4096 12 := by
  have h0 : AffineReverse 3947 6561 3947 6561 0 :=
    AffineReverse.seed 3947 6561
  have h1 : AffineReverse 3947 6561 7894 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 3947 6561 15788 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 3947 6561 10525 17496 3 :=
    AffineReverse.odd h2 10525 17496 (by decide) (by decide)
  have h4 : AffineReverse 3947 6561 21050 34992 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 3947 6561 14033 23328 5 :=
    AffineReverse.odd h4 14033 23328 (by decide) (by decide)
  have h6 : AffineReverse 3947 6561 9355 15552 6 :=
    AffineReverse.odd h5 9355 15552 (by decide) (by decide)
  have h7 : AffineReverse 3947 6561 18710 31104 7 :=
    AffineReverse.even h6
  have h8 : AffineReverse 3947 6561 12473 20736 8 :=
    AffineReverse.odd h7 12473 20736 (by decide) (by decide)
  have h9 : AffineReverse 3947 6561 8315 13824 9 :=
    AffineReverse.odd h8 8315 13824 (by decide) (by decide)
  have h10 : AffineReverse 3947 6561 5543 9216 10 :=
    AffineReverse.odd h9 5543 9216 (by decide) (by decide)
  have h11 : AffineReverse 3947 6561 3695 6144 11 :=
    AffineReverse.odd h10 3695 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 2463 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_b_source_merge (q : Nat) :
    LowerMerge shortcut (2631 + 4374 * q) (2463 + 4096 * q) := by
  have he : iter shortcut 1 2631 = 3947 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 2631 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 2631)
        ((2 ^ 0 * 3 ^ oddCount 2631 1) * 2187)
        2463 4096 12 := by
    simpa only [he, hs] using v114_b_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    2631 1 0 2187 q 2463 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_b_reverse_word
#print axioms v114_b_source_merge

/-- Law c: EEOEOOOEOOOO; exact reverse family (2435,6561)->(1519,4096). -/
theorem v114_c_reverse_word :
    AffineReverse 2435 6561 1519 4096 12 := by
  have h0 : AffineReverse 2435 6561 2435 6561 0 :=
    AffineReverse.seed 2435 6561
  have h1 : AffineReverse 2435 6561 4870 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 2435 6561 9740 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 2435 6561 6493 17496 3 :=
    AffineReverse.odd h2 6493 17496 (by decide) (by decide)
  have h4 : AffineReverse 2435 6561 12986 34992 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 2435 6561 8657 23328 5 :=
    AffineReverse.odd h4 8657 23328 (by decide) (by decide)
  have h6 : AffineReverse 2435 6561 5771 15552 6 :=
    AffineReverse.odd h5 5771 15552 (by decide) (by decide)
  have h7 : AffineReverse 2435 6561 3847 10368 7 :=
    AffineReverse.odd h6 3847 10368 (by decide) (by decide)
  have h8 : AffineReverse 2435 6561 7694 20736 8 :=
    AffineReverse.even h7
  have h9 : AffineReverse 2435 6561 5129 13824 9 :=
    AffineReverse.odd h8 5129 13824 (by decide) (by decide)
  have h10 : AffineReverse 2435 6561 3419 9216 10 :=
    AffineReverse.odd h9 3419 9216 (by decide) (by decide)
  have h11 : AffineReverse 2435 6561 2279 6144 11 :=
    AffineReverse.odd h10 2279 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 1519 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_c_source_merge (q : Nat) :
    LowerMerge shortcut (1623 + 4374 * q) (1519 + 4096 * q) := by
  have he : iter shortcut 1 1623 = 2435 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 1623 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 1623)
        ((2 ^ 0 * 3 ^ oddCount 1623 1) * 2187)
        1519 4096 12 := by
    simpa only [he, hs] using v114_c_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1623 1 0 2187 q 1519 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_c_reverse_word
#print axioms v114_c_source_merge

/-- Law d: EEOEOOOOEOOO; exact reverse family (167,6561)->(103,4096). -/
theorem v114_d_reverse_word :
    AffineReverse 167 6561 103 4096 12 := by
  have h0 : AffineReverse 167 6561 167 6561 0 :=
    AffineReverse.seed 167 6561
  have h1 : AffineReverse 167 6561 334 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 167 6561 668 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 167 6561 445 17496 3 :=
    AffineReverse.odd h2 445 17496 (by decide) (by decide)
  have h4 : AffineReverse 167 6561 890 34992 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 167 6561 593 23328 5 :=
    AffineReverse.odd h4 593 23328 (by decide) (by decide)
  have h6 : AffineReverse 167 6561 395 15552 6 :=
    AffineReverse.odd h5 395 15552 (by decide) (by decide)
  have h7 : AffineReverse 167 6561 263 10368 7 :=
    AffineReverse.odd h6 263 10368 (by decide) (by decide)
  have h8 : AffineReverse 167 6561 175 6912 8 :=
    AffineReverse.odd h7 175 6912 (by decide) (by decide)
  have h9 : AffineReverse 167 6561 350 13824 9 :=
    AffineReverse.even h8
  have h10 : AffineReverse 167 6561 233 9216 10 :=
    AffineReverse.odd h9 233 9216 (by decide) (by decide)
  have h11 : AffineReverse 167 6561 155 6144 11 :=
    AffineReverse.odd h10 155 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 103 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_d_source_merge (q : Nat) :
    LowerMerge shortcut (111 + 4374 * q) (103 + 4096 * q) := by
  have he : iter shortcut 1 111 = 167 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 111 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 111)
        ((2 ^ 0 * 3 ^ oddCount 111 1) * 2187)
        103 4096 12 := by
    simpa only [he, hs] using v114_d_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    111 1 0 2187 q 103 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_d_reverse_word
#print axioms v114_d_source_merge

/-- Law e: EEOEOOOOOEOO; exact reverse family (3326,6561)->(2075,4096). -/
theorem v114_e_reverse_word :
    AffineReverse 3326 6561 2075 4096 12 := by
  have h0 : AffineReverse 3326 6561 3326 6561 0 :=
    AffineReverse.seed 3326 6561
  have h1 : AffineReverse 3326 6561 6652 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 3326 6561 13304 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 3326 6561 8869 17496 3 :=
    AffineReverse.odd h2 8869 17496 (by decide) (by decide)
  have h4 : AffineReverse 3326 6561 17738 34992 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 3326 6561 11825 23328 5 :=
    AffineReverse.odd h4 11825 23328 (by decide) (by decide)
  have h6 : AffineReverse 3326 6561 7883 15552 6 :=
    AffineReverse.odd h5 7883 15552 (by decide) (by decide)
  have h7 : AffineReverse 3326 6561 5255 10368 7 :=
    AffineReverse.odd h6 5255 10368 (by decide) (by decide)
  have h8 : AffineReverse 3326 6561 3503 6912 8 :=
    AffineReverse.odd h7 3503 6912 (by decide) (by decide)
  have h9 : AffineReverse 3326 6561 2335 4608 9 :=
    AffineReverse.odd h8 2335 4608 (by decide) (by decide)
  have h10 : AffineReverse 3326 6561 4670 9216 10 :=
    AffineReverse.even h9
  have h11 : AffineReverse 3326 6561 3113 6144 11 :=
    AffineReverse.odd h10 3113 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 2075 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_e_source_merge (q : Nat) :
    LowerMerge shortcut (2217 + 4374 * q) (2075 + 4096 * q) := by
  have he : iter shortcut 1 2217 = 3326 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 2217 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 2217)
        ((2 ^ 0 * 3 ^ oddCount 2217 1) * 2187)
        2075 4096 12 := by
    simpa only [he, hs] using v114_e_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    2217 1 0 2187 q 2075 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_e_reverse_word
#print axioms v114_e_source_merge

/-- Law f: EEOOEOEOOOOO; exact reverse family (3332,6561)->(2079,4096). -/
theorem v114_f_reverse_word :
    AffineReverse 3332 6561 2079 4096 12 := by
  have h0 : AffineReverse 3332 6561 3332 6561 0 :=
    AffineReverse.seed 3332 6561
  have h1 : AffineReverse 3332 6561 6664 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 3332 6561 13328 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 3332 6561 8885 17496 3 :=
    AffineReverse.odd h2 8885 17496 (by decide) (by decide)
  have h4 : AffineReverse 3332 6561 5923 11664 4 :=
    AffineReverse.odd h3 5923 11664 (by decide) (by decide)
  have h5 : AffineReverse 3332 6561 11846 23328 5 :=
    AffineReverse.even h4
  have h6 : AffineReverse 3332 6561 7897 15552 6 :=
    AffineReverse.odd h5 7897 15552 (by decide) (by decide)
  have h7 : AffineReverse 3332 6561 15794 31104 7 :=
    AffineReverse.even h6
  have h8 : AffineReverse 3332 6561 10529 20736 8 :=
    AffineReverse.odd h7 10529 20736 (by decide) (by decide)
  have h9 : AffineReverse 3332 6561 7019 13824 9 :=
    AffineReverse.odd h8 7019 13824 (by decide) (by decide)
  have h10 : AffineReverse 3332 6561 4679 9216 10 :=
    AffineReverse.odd h9 4679 9216 (by decide) (by decide)
  have h11 : AffineReverse 3332 6561 3119 6144 11 :=
    AffineReverse.odd h10 3119 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 2079 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_f_source_merge (q : Nat) :
    LowerMerge shortcut (2221 + 4374 * q) (2079 + 4096 * q) := by
  have he : iter shortcut 1 2221 = 3332 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 2221 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 2221)
        ((2 ^ 0 * 3 ^ oddCount 2221 1) * 2187)
        2079 4096 12 := by
    simpa only [he, hs] using v114_f_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    2221 1 0 2187 q 2079 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_f_reverse_word
#print axioms v114_f_source_merge

/-- Law g: EEOOEOOEOOOO; exact reverse family (1820,6561)->(1135,4096). -/
theorem v114_g_reverse_word :
    AffineReverse 1820 6561 1135 4096 12 := by
  have h0 : AffineReverse 1820 6561 1820 6561 0 :=
    AffineReverse.seed 1820 6561
  have h1 : AffineReverse 1820 6561 3640 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 1820 6561 7280 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 1820 6561 4853 17496 3 :=
    AffineReverse.odd h2 4853 17496 (by decide) (by decide)
  have h4 : AffineReverse 1820 6561 3235 11664 4 :=
    AffineReverse.odd h3 3235 11664 (by decide) (by decide)
  have h5 : AffineReverse 1820 6561 6470 23328 5 :=
    AffineReverse.even h4
  have h6 : AffineReverse 1820 6561 4313 15552 6 :=
    AffineReverse.odd h5 4313 15552 (by decide) (by decide)
  have h7 : AffineReverse 1820 6561 2875 10368 7 :=
    AffineReverse.odd h6 2875 10368 (by decide) (by decide)
  have h8 : AffineReverse 1820 6561 5750 20736 8 :=
    AffineReverse.even h7
  have h9 : AffineReverse 1820 6561 3833 13824 9 :=
    AffineReverse.odd h8 3833 13824 (by decide) (by decide)
  have h10 : AffineReverse 1820 6561 2555 9216 10 :=
    AffineReverse.odd h9 2555 9216 (by decide) (by decide)
  have h11 : AffineReverse 1820 6561 1703 6144 11 :=
    AffineReverse.odd h10 1703 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 1135 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_g_source_merge (q : Nat) :
    LowerMerge shortcut (1213 + 4374 * q) (1135 + 4096 * q) := by
  have he : iter shortcut 1 1213 = 1820 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 1213 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 1213)
        ((2 ^ 0 * 3 ^ oddCount 1213 1) * 2187)
        1135 4096 12 := by
    simpa only [he, hs] using v114_g_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1213 1 0 2187 q 1135 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_g_reverse_word
#print axioms v114_g_source_merge

/-- Law h: EEOOEOOOEOOO; exact reverse family (6113,6561)->(3815,4096). -/
theorem v114_h_reverse_word :
    AffineReverse 6113 6561 3815 4096 12 := by
  have h0 : AffineReverse 6113 6561 6113 6561 0 :=
    AffineReverse.seed 6113 6561
  have h1 : AffineReverse 6113 6561 12226 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 6113 6561 24452 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 6113 6561 16301 17496 3 :=
    AffineReverse.odd h2 16301 17496 (by decide) (by decide)
  have h4 : AffineReverse 6113 6561 10867 11664 4 :=
    AffineReverse.odd h3 10867 11664 (by decide) (by decide)
  have h5 : AffineReverse 6113 6561 21734 23328 5 :=
    AffineReverse.even h4
  have h6 : AffineReverse 6113 6561 14489 15552 6 :=
    AffineReverse.odd h5 14489 15552 (by decide) (by decide)
  have h7 : AffineReverse 6113 6561 9659 10368 7 :=
    AffineReverse.odd h6 9659 10368 (by decide) (by decide)
  have h8 : AffineReverse 6113 6561 6439 6912 8 :=
    AffineReverse.odd h7 6439 6912 (by decide) (by decide)
  have h9 : AffineReverse 6113 6561 12878 13824 9 :=
    AffineReverse.even h8
  have h10 : AffineReverse 6113 6561 8585 9216 10 :=
    AffineReverse.odd h9 8585 9216 (by decide) (by decide)
  have h11 : AffineReverse 6113 6561 5723 6144 11 :=
    AffineReverse.odd h10 5723 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 3815 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_h_source_merge (q : Nat) :
    LowerMerge shortcut (4075 + 4374 * q) (3815 + 4096 * q) := by
  have he : iter shortcut 1 4075 = 6113 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 4075 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 4075)
        ((2 ^ 0 * 3 ^ oddCount 4075 1) * 2187)
        3815 4096 12 := by
    simpa only [he, hs] using v114_h_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    4075 1 0 2187 q 3815 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_h_reverse_word
#print axioms v114_h_source_merge

/-- Law i: EEOOEOOOOEOO; exact reverse family (2711,6561)->(1691,4096). -/
theorem v114_i_reverse_word :
    AffineReverse 2711 6561 1691 4096 12 := by
  have h0 : AffineReverse 2711 6561 2711 6561 0 :=
    AffineReverse.seed 2711 6561
  have h1 : AffineReverse 2711 6561 5422 13122 1 :=
    AffineReverse.even h0
  have h2 : AffineReverse 2711 6561 10844 26244 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 2711 6561 7229 17496 3 :=
    AffineReverse.odd h2 7229 17496 (by decide) (by decide)
  have h4 : AffineReverse 2711 6561 4819 11664 4 :=
    AffineReverse.odd h3 4819 11664 (by decide) (by decide)
  have h5 : AffineReverse 2711 6561 9638 23328 5 :=
    AffineReverse.even h4
  have h6 : AffineReverse 2711 6561 6425 15552 6 :=
    AffineReverse.odd h5 6425 15552 (by decide) (by decide)
  have h7 : AffineReverse 2711 6561 4283 10368 7 :=
    AffineReverse.odd h6 4283 10368 (by decide) (by decide)
  have h8 : AffineReverse 2711 6561 2855 6912 8 :=
    AffineReverse.odd h7 2855 6912 (by decide) (by decide)
  have h9 : AffineReverse 2711 6561 1903 4608 9 :=
    AffineReverse.odd h8 1903 4608 (by decide) (by decide)
  have h10 : AffineReverse 2711 6561 3806 9216 10 :=
    AffineReverse.even h9
  have h11 : AffineReverse 2711 6561 2537 6144 11 :=
    AffineReverse.odd h10 2537 6144 (by decide) (by decide)
  exact AffineReverse.odd h11 1691 4096 (by decide) (by decide)

/-- Entire positive source congruence cylinder, never just test offsets. -/
theorem v114_i_source_merge (q : Nat) :
    LowerMerge shortcut (1807 + 4374 * q) (1691 + 4096 * q) := by
  have he : iter shortcut 1 1807 = 2711 := by decide
  have hs : (2 ^ 0 * 3 ^ oddCount 1807 1) * 2187 = 6561 := by decide
  have hw :
      AffineReverse (iter shortcut 1 1807)
        ((2 ^ 0 * 3 ^ oddCount 1807 1) * 2187)
        1691 4096 12 := by
    simpa only [he, hs] using v114_i_reverse_word
  have hm : (2 ^ (1 + 0) * 2187) = (4374 : Nat) := by decide
  have h := scaled_reverse_lower_merge
    1807 1 0 2187 q 1691 4096 12 hw (by decide) (by decide)
  simpa only [hm] using h

#print axioms v114_i_reverse_word
#print axioms v114_i_source_merge

end SourceProduct
end CollatzFinal
