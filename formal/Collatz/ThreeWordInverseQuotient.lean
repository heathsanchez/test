import Collatz.ScaledReverseMerger

namespace CollatzFinal
namespace SourceProduct

/-- V113 reduces the new V112 merger bank to three exact ten-step inverse
laws, each with the same positive slope 1024/2187. All intermediate reverse
steps are real shortcut predecessors with integer arithmetic premises. -/

/-- EEOEOOOOOO: source endpoint residue 410 modulo 3^7. -/
theorem v113_r410_word :
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

theorem v113_r410_identity (q : Nat) :
    iter shortcut 10 (191 + 1024*q) = 410 + 2187*q :=
  affine_reverse_sound v113_r410_word q

/-- Source-relative use of the 410 endpoint class. -/
theorem v113_r410_source_merge (n j q : Nat)
    (hendpoint : iter shortcut j n = 410 + 2187*q)
    (hstrict : 191 + 1024*q < n) :
    LowerMerge shortcut n (191 + 1024*q) := by
  refine ⟨hstrict, j, 10, ?_⟩
  rw [hendpoint]
  exact (v113_r410_identity q).symm

#print axioms v113_r410_identity
#print axioms v113_r410_source_merge

/-- EEOOEOOOOO: source endpoint residue 1982 modulo 3^7. -/
theorem v113_r1982_word :
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

theorem v113_r1982_identity (q : Nat) :
    iter shortcut 10 (927 + 1024*q) = 1982 + 2187*q :=
  affine_reverse_sound v113_r1982_word q

/-- Source-relative use of the 1982 endpoint class. -/
theorem v113_r1982_source_merge (n j q : Nat)
    (hendpoint : iter shortcut j n = 1982 + 2187*q)
    (hstrict : 927 + 1024*q < n) :
    LowerMerge shortcut n (927 + 1024*q) := by
  refine ⟨hstrict, j, 10, ?_⟩
  rw [hendpoint]
  exact (v113_r1982_identity q).symm

#print axioms v113_r1982_identity
#print axioms v113_r1982_source_merge

/-- EEOOOEOOOO: source endpoint residue 2153 modulo 3^7. -/
theorem v113_r2153_word :
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

theorem v113_r2153_identity (q : Nat) :
    iter shortcut 10 (1007 + 1024*q) = 2153 + 2187*q :=
  affine_reverse_sound v113_r2153_word q

/-- Source-relative use of the 2153 endpoint class. -/
theorem v113_r2153_source_merge (n j q : Nat)
    (hendpoint : iter shortcut j n = 2153 + 2187*q)
    (hstrict : 1007 + 1024*q < n) :
    LowerMerge shortcut n (1007 + 1024*q) := by
  refine ⟨hstrict, j, 10, ?_⟩
  rw [hendpoint]
  exact (v113_r2153_identity q).symm

#print axioms v113_r2153_identity
#print axioms v113_r2153_source_merge

end SourceProduct
end CollatzFinal
