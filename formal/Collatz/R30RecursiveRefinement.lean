import Collatz.SourceCylinderExit
import Collatz.EarlierSourceCollision
import Collatz.R30FirstSplit

set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace CollatzFinal.SourceProduct

/-- After the first V68 split, the lexicographically first surviving sibling is
still r=30, now at parameter depth 22.  Refinement depths 23..25 expose no
currently compiled protected consequence.  At depth 26, the child with new
four-bit value 14 has a uniform direct descent after 85 shortcut steps. -/
theorem r30_depth26_second_split_merger (u : Nat) :
    EarlierSourceCollision
      (222089457973445273090248409115 +
        253816393679730624487911063552 * u)
      (iter shortcut 85
        (222089457973445273090248409115 +
          253816393679730624487911063552 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_direct
      (n := 222089457973445273090248409115)
      (k := 85)
      (y := 111276847342912191586928426644)
      (q := 53)
      (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 85 * 6561 = 253816393679730624487911063552 := by decide
  have heq :
      222089457973445273090248409115 + 2 ^ 85 * (6561 * u) =
        222089457973445273090248409115 +
          253816393679730624487911063552 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (222089457973445273090248409115 +
          253816393679730624487911063552 * u)
        (iter shortcut 85
          (222089457973445273090248409115 +
            253816393679730624487911063552 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 222089457973445273090248409115 +
        253816393679730624487911063552 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

/-- Prospective falsifier to the tempting repeated-four-bit pattern.  After the
depth-26 zero sibling is retained, depths 27 and 28 expose no compiled merger;
at depth 29 the first protected separator instead occurs after three bits, at
new suffix value 3. -/
theorem r30_depth29_third_split_merger (u : Nat) :
    EarlierSourceCollision
      (761449294542872850127059419163 +
        2030531149437844995903288508416 * u)
      (iter shortcut 88
        (761449294542872850127059419163 +
          2030531149437844995903288508416 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_direct
      (n := 761449294542872850127059419163)
      (k := 88)
      (y := 429210541515842425114374868088)
      (q := 55)
      (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 88 * 6561 = 2030531149437844995903288508416 := by decide
  have heq :
      761449294542872850127059419163 + 2 ^ 88 * (6561 * u) =
        761449294542872850127059419163 +
          2030531149437844995903288508416 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (761449294542872850127059419163 +
          2030531149437844995903288508416 * u)
        (iter shortcut 88
          (761449294542872850127059419163 +
            2030531149437844995903288508416 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 761449294542872850127059419163 +
        2030531149437844995903288508416 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

#print axioms r30_depth26_second_split_merger
#print axioms r30_depth29_third_split_merger

end CollatzFinal.SourceProduct
