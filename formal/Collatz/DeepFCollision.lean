import Collatz.AffineFTransportBank

namespace CollatzFinal
namespace SourceProduct

/-- A deeper exact critical pair OUTSIDE V115's initial odd-run/even/odd
    shape: the source has parity word 111111001101100, the F-source has
    word 111111011000001, and both REAL 15-step endpoints coincide.
    The base slope is 59049=3^10; the transformed source has nine odds. -/
theorem deep_F_collision_3391 (q : Nat) :
    iter shortcut 15 (3391 + 32768 * q) =
      iter shortcut 15 (3 * (3391 + 32768 * q) + 2) := by
  have hb : iter shortcut 15 3391 = 6113 := by decide
  have hc : oddCount 3391 15 = 10 := by decide
  have hfb : iter shortcut 15 10175 = 6113 := by decide
  have hfc : oddCount 10175 15 = 9 := by decide
  have hleft :
      iter shortcut 15 (3391 + 32768 * q) = 6113 + 59049 * q := by
    simpa [hb, hc] using (parity_cylinder_shift 3391 15 q)
  have hright :
      iter shortcut 15 (10175 + 32768 * (3 * q)) =
        6113 + 59049 * q := by
    simpa [hfb, hfc, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      using (parity_cylinder_shift 10175 15 (3 * q))
  calc
    iter shortcut 15 (3391 + 32768 * q) =
        6113 + 59049 * q := hleft
    _ = iter shortcut 15 (10175 + 32768 * (3 * q)) := hright.symm
    _ = iter shortcut 15 (3 * (3391 + 32768 * q) + 2) := by
      congr 1
      ring

/-- Reuse the V118 source-45 lawful OEOEOOOOO word and the NEW deeper
    exact F collision to obtain genuine smaller ORIGINAL-source merger.
    Source n(z)=19107135+23887872*z has an all-offset 15-step
    non-descending prefix (separate finite-symbolic check). -/
theorem deep_F_new_lower_merge (z : Nat) :
    0 < 13419551 + 16777216 * z ∧
    LowerMerge shortcut
      (19107135 + 23887872 * z)
      (13419551 + 16777216 * z) := by
  let n := 19107135 + 23887872 * z
  let p := 13419551 + 16777216 * z
  have hp : 0 < p := by dsimp [p]; omega
  have hlt : p < n := by dsimp [p,n]; omega
  have hsource :
      n = 3391 + 32768 * (583 + 729 * z) := by
    dsimp [n]
    ring
  have hcollision :
      iter shortcut 15 n = iter shortcut 15 (3 * n + 2) := by
    calc
      iter shortcut 15 n =
          iter shortcut 15 (3391 + 32768 * (583 + 729 * z)) := by
        rw [hsource]
      _ = iter shortcut 15
          (3 * (3391 + 32768 * (583 + 729 * z)) + 2) :=
        deep_F_collision_3391 (583 + 729 * z)
      _ = iter shortcut 15 (3 * n + 2) := by
        rw [← hsource]
  have hreverse :
      iter shortcut 9 p = 3 * n + 2 := by
    calc
      iter shortcut 9 p =
          iter shortcut 9 (31 + 512 * (26210 + 32768 * z)) := by
        congr 1
        dsimp [p]
        ring
      _ = 3 * (45 + 729 * (26210 + 32768 * z)) + 2 :=
        source_45_reverse_all_offsets (26210 + 32768 * z)
      _ = 3 * n + 2 := by
        dsimp [n]
        ring
  refine ⟨hp, hlt, 15, 24, ?_⟩
  calc
    iter shortcut 15 n =
        iter shortcut 15 (3 * n + 2) := hcollision
    _ = iter shortcut 15 (iter shortcut 9 p) := by
      rw [hreverse]
    _ = iter shortcut 24 p := by
      simpa using (iter_add shortcut 9 15 p).symm

#print axioms deep_F_collision_3391
#print axioms deep_F_new_lower_merge

end SourceProduct
end CollatzFinal
