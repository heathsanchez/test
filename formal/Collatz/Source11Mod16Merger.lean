import Collatz.AffineFTransportBank

namespace CollatzFinal
namespace SourceProduct

/-- The entire cylinder n=11+16*q has the REAL source parity prefix
    odd,odd,even,odd. These are exact affine identities for ALL offsets. -/
theorem source_11_mod16_parity_collision (q : Nat) :
    InitialOddRun (11 + 16 * q) 2 ∧
    (iter shortcut 2 (11 + 16 * q)) % 2 = 0 ∧
    (shortcut (iter shortcut 2 (11 + 16 * q))) % 2 = 1 := by
  have hnodd : (11 + 16 * q) % 2 ≠ 0 := by omega
  have h1 : shortcut (11 + 16 * q) = 17 + 24 * q := by
    simp only [shortcut, if_neg hnodd]
    omega
  have hodd1 : (17 + 24 * q) % 2 ≠ 0 := by omega
  have h2 : shortcut (17 + 24 * q) = 26 + 36 * q := by
    simp only [shortcut, if_neg hodd1]
    omega
  have heven2 : (26 + 36 * q) % 2 = 0 := by omega
  have h3 : shortcut (26 + 36 * q) = 13 + 18 * q := by
    simp only [shortcut, if_pos heven2]
    omega
  have hodd : InitialOddRun (11 + 16 * q) 2 := by
    change (11 + 16 * q) % 2 = 1 ∧
      (shortcut (11 + 16 * q)) % 2 = 1 ∧ True
    refine ⟨by omega, ?_, trivial⟩
    rw [h1]
    omega
  have heven : (iter shortcut 2 (11 + 16 * q)) % 2 = 0 := by
    change (shortcut (shortcut (11 + 16 * q))) % 2 = 0
    rw [h1, h2]
    omega
  have hnextodd :
      (shortcut (iter shortcut 2 (11 + 16 * q))) % 2 = 1 := by
    change (shortcut (shortcut (shortcut (11 + 16 * q)))) % 2 = 1
    rw [h1, h2, h3]
    omega
  exact ⟨hodd, heven, hnextodd⟩

/-- Compact source-relative CRT consequence:
    source n(z)=10251+11664*z (11 mod16, 45 mod729)
    shares an actual future with strictly smaller
    p(z)=7199+8192*z. Clocks: T^4(n)=T^13(p).
    The symbolic all-offset merger does not imply global Collatz;
    its previous V112 UNKNOWN residue-count contribution is 93 classes. -/
theorem source_11_mod16_45_mod729_lower_merge (z : Nat) :
    0 < 7199 + 8192 * z ∧
    LowerMerge shortcut
      (10251 + 11664 * z)
      (7199 + 8192 * z) := by
  have heq :
      45 + 729 * (14 + 16 * z) =
      11 + 16 * (640 + 729 * z) := by omega
  have hn :
      45 + 729 * (14 + 16 * z) =
      10251 + 11664 * z := by omega
  have hp :
      31 + 512 * (14 + 16 * z) =
      7199 + 8192 * z := by omega
  have hpar := source_11_mod16_parity_collision (640 + 729 * z)
  rw [← heq] at hpar
  obtain ⟨hodd, heven, hnextodd⟩ := hpar
  have hm :=
    source_45_lower_merge_of_odd_run_even_odd
      (14 + 16 * z) 2 hodd heven hnextodd
  rw [hn, hp] at hm
  exact hm

#print axioms source_11_mod16_parity_collision
#print axioms source_11_mod16_45_mod729_lower_merge

end SourceProduct
end CollatzFinal
