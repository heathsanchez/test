import Collatz.ParityCollisionBridge
import Collatz.ReverseAffineMerger

namespace CollatzFinal
namespace SourceProduct

/-- General certificate compiler: a lawful affine reverse word reaches
    F(n)=3*n+2 from a STRICTLY SMALLER positive source, and V115's
    genuine odd-run/even/odd critical pair transports F(n) to n.

    Universal event production is NOT assumed or proved. -/
theorem affine_F_transport_lower_merge
    (a M p c t q k : Nat)
    (hword : AffineReverse (3 * a + 2) (3 * M) p c t)
    (hp : 0 < p)
    (hbase : p < a)
    (hslope : c ≤ M)
    (hodd : InitialOddRun (a + M * q) k)
    (heven : (iter shortcut k (a + M * q)) % 2 = 0)
    (hnextodd :
      (shortcut (iter shortcut k (a + M * q))) % 2 = 1) :
    0 < p + c * q ∧
      LowerMerge shortcut (a + M * q) (p + c * q) := by
  have hprod := Nat.mul_le_mul_right q hslope
  have hlt : p + c * q < a + M * q := by omega
  have hpPos : 0 < p + c * q := by omega
  have htransport :=
    three_plus_two_collision_after_odd_run
      (a + M * q) k hodd heven hnextodd
  have hscaled :
      3 * (a + M * q) + 2 = (3 * a + 2) + (3 * M) * q := by
    ring
  have hwitness := affine_reverse_sound hword q
  refine ⟨hpPos, hlt, k + 2, t + (k + 2), ?_⟩
  calc
    iter shortcut (k + 2) (a + M * q) =
        iter shortcut (k + 2) (3 * (a + M * q) + 2) := htransport.symm
    _ = iter shortcut (k + 2) ((3 * a + 2) + (3 * M) * q) := by
      rw [hscaled]
    _ = iter shortcut (k + 2) (iter shortcut t (p + c * q)) := by
      rw [hwitness]
    _ = iter shortcut (t + (k + 2)) (p + c * q) :=
      (iter_add shortcut t (k + 2) (p + c * q)).symm

/-- A NEW parametric F-predecessor family:
    T^9 (31 + 512*q) = 3*(45 + 729*q)+2 for every natural q.
    Word O E O E O O O O O is a chain of ACTUAL shortcut inverses.
    In contrast to the original V115 60 mod 81 family, this has
    base source 45 mod 729. -/
theorem source_45_reverse_word :
    AffineReverse 137 2187 31 512 9 := by
  have h0 : AffineReverse 137 2187 137 2187 0 :=
    AffineReverse.seed 137 2187
  have h1 : AffineReverse 137 2187 91 1458 1 :=
    AffineReverse.odd h0 91 1458 (by decide) (by decide)
  have h2 : AffineReverse 137 2187 182 2916 2 :=
    AffineReverse.even h1
  have h3 : AffineReverse 137 2187 121 1944 3 :=
    AffineReverse.odd h2 121 1944 (by decide) (by decide)
  have h4 : AffineReverse 137 2187 242 3888 4 :=
    AffineReverse.even h3
  have h5 : AffineReverse 137 2187 161 2592 5 :=
    AffineReverse.odd h4 161 2592 (by decide) (by decide)
  have h6 : AffineReverse 137 2187 107 1728 6 :=
    AffineReverse.odd h5 107 1728 (by decide) (by decide)
  have h7 : AffineReverse 137 2187 71 1152 7 :=
    AffineReverse.odd h6 71 1152 (by decide) (by decide)
  have h8 : AffineReverse 137 2187 47 768 8 :=
    AffineReverse.odd h7 47 768 (by decide) (by decide)
  exact AffineReverse.odd h8 31 512 (by decide) (by decide)

/-- All offsets of the new source family are lawful exact F-preimages. -/
theorem source_45_reverse_all_offsets (q : Nat) :
    iter shortcut 9 (31 + 512 * q) =
      3 * (45 + 729 * q) + 2 := by
  have hw := affine_reverse_sound source_45_reverse_word q
  simpa [Nat.mul_add, Nat.mul_assoc, Nat.add_assoc, Nat.add_comm,
         Nat.add_left_comm] using hw

/-- CONDITIONAL all-depth true lower-source coalescence for the
    45 mod 729 family, at ANY initial odd-run length. -/
theorem source_45_lower_merge_of_odd_run_even_odd
    (q k : Nat)
    (hodd : InitialOddRun (45 + 729 * q) k)
    (heven : (iter shortcut k (45 + 729 * q)) % 2 = 0)
    (hnextodd :
      (shortcut (iter shortcut k (45 + 729 * q))) % 2 = 1) :
    0 < 31 + 512 * q ∧
      LowerMerge shortcut (45 + 729 * q) (31 + 512 * q) := by
  exact affine_F_transport_lower_merge
    45 729 31 512 9 q k source_45_reverse_word
    (by decide) (by decide) (by decide)
    hodd heven hnextodd

#print axioms affine_F_transport_lower_merge
#print axioms source_45_reverse_word
#print axioms source_45_reverse_all_offsets
#print axioms source_45_lower_merge_of_odd_run_even_odd

end SourceProduct
end CollatzFinal
