import Collatz.AffineFTransportBank

namespace CollatzFinal
namespace SourceProduct

/-- True all-offset shortcut prefix for a dyadic cylinder:
    source 27+4096*q has actual parity word 1101, which is V115's
    initial odd-run/even/odd critical pair at k=2. -/
theorem source_27_parity_critical_pair (q : Nat) :
    InitialOddRun (27 + 4096 * q) 2 ∧
    (iter shortcut 2 (27 + 4096 * q)) % 2 = 0 ∧
    (shortcut (iter shortcut 2 (27 + 4096 * q))) % 2 = 1 := by
  have hnodd : (27 + 4096 * q) % 2 ≠ 0 := by omega
  have h1 : shortcut (27 + 4096 * q) = 41 + 6144 * q := by
    simp only [shortcut, if_neg hnodd]
    omega
  have hodd1 : (41 + 6144 * q) % 2 ≠ 0 := by omega
  have h2 : shortcut (41 + 6144 * q) = 62 + 9216 * q := by
    simp only [shortcut, if_neg hodd1]
    omega
  have heven2 : (62 + 9216 * q) % 2 = 0 := by omega
  have h3 : shortcut (62 + 9216 * q) = 31 + 4608 * q := by
    simp only [shortcut, if_pos heven2]
    omega
  have hprefix : InitialOddRun (27 + 4096 * q) 2 := by
    change (27 + 4096 * q) % 2 = 1 ∧
      (shortcut (27 + 4096 * q)) % 2 = 1 ∧ True
    refine ⟨by omega, ?_, trivial⟩
    rw [h1]
    omega
  have h2even : (iter shortcut 2 (27 + 4096 * q)) % 2 = 0 := by
    change (shortcut (shortcut (27 + 4096 * q))) % 2 = 0
    rw [h1, h2]
    omega
  have h3odd :
      (shortcut (iter shortcut 2 (27 + 4096 * q))) % 2 = 1 := by
    change (shortcut (shortcut (shortcut (27 + 4096 * q)))) % 2 = 1
    rw [h1, h2, h3]
    omega
  exact ⟨hprefix, h2even, h3odd⟩

/-- NEW source class excluded by neither V108/V109 nor V110/V112 bounded
    witness search at the old moduli. The CRT intersection uses
    n ≡ 27 (mod 4096), n ≡ 45 (mod 729).
    Combining the independently source-attached F predecessor
    and all-depth V115 critical pair, for every z>=0:
      T^4 (2727963+2985984*z) =
      T^13 (1915935+2097152*z).
    It has a strictly smaller ORIGINAL source for ALL offsets.
    This still proves only ONE uniform congruence family, NOT Collatz. -/
theorem new_source_27_45_crt_lower_merge (z : Nat) :
    0 < 1915935 + 2097152 * z ∧
    LowerMerge shortcut
      (2727963 + 2985984 * z)
      (1915935 + 2097152 * z) := by
  have heq :
      45 + 729 * (3742 + 4096 * z) =
      27 + 4096 * (666 + 729 * z) := by ring
  have hn :
      45 + 729 * (3742 + 4096 * z) =
      2727963 + 2985984 * z := by ring
  have hp :
      31 + 512 * (3742 + 4096 * z) =
      1915935 + 2097152 * z := by ring
  have hpar := source_27_parity_critical_pair (666 + 729 * z)
  rw [← heq] at hpar
  obtain ⟨hodd, heven, hnextodd⟩ := hpar
  have hmerge :=
    source_45_lower_merge_of_odd_run_even_odd
      (3742 + 4096 * z) 2 hodd heven hnextodd
  rw [hn, hp] at hmerge
  exact hmerge

#print axioms source_27_parity_critical_pair
#print axioms new_source_27_45_crt_lower_merge

end SourceProduct
end CollatzFinal
