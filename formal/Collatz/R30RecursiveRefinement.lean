import Collatz.SourceCylinderExit
import Collatz.EarlierSourceCollision
import Collatz.R30FirstSplit

set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace CollatzFinal.SourceProduct

/-- V69 first recursive separator.  Starting from the surviving r=30
parameter cylinder at depth 22, no currently compiled protected consequence
distinguishes either child through depths 23 and 24.  At depth 25 the child
with new suffix value 6 has an exact odd lower-source merge after 84 source
steps. -/
theorem r30_depth25_recursive_split_merger (u : Nat) :
    EarlierSourceCollision
      (95181261133579960846292877339 +
        126908196839865312243955531776 * u)
      (iter shortcut 84
        (95181261133579960846292877339 +
          126908196839865312243955531776 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_odd_merge
      (n := 95181261133579960846292877339)
      (k := 84)
      (y := 95380219860175772630973553685)
      (q := 52)
      (p := 63586813240117181753982369123)
      (by decide) (by decide) (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 84 * 6561 = 126908196839865312243955531776 := by decide
  have heq :
      95181261133579960846292877339 + 2 ^ 84 * (6561 * u) =
        95181261133579960846292877339 +
          126908196839865312243955531776 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (95181261133579960846292877339 +
          126908196839865312243955531776 * u)
        (iter shortcut 84
          (95181261133579960846292877339 +
            126908196839865312243955531776 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 95181261133579960846292877339 +
        126908196839865312243955531776 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

/-- After retaining the zero sibling at depth 25, the licensed consequence
grammar remains silent through depths 26..28.  At depth 29 the child with new
suffix value 6 has a uniform direct descent after 88 shortcut steps. -/
theorem r30_depth29_recursive_split_merger (u : Nat) :
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

/-- Prospective rejection of the tempting repeated-suffix-6 rule.  From the
depth-29 zero sibling, the first currently compiled protected separator occurs
at depth 33 with new suffix value 1, not 6. -/
theorem r30_depth33_pattern_falsifier_merger (u : Nat) :
    EarlierSourceCollision
      (2030531262941525972566614736923 +
        32488498391005519934452616134656 * u)
      (iter shortcut 92
        (2030531262941525972566614736923 +
          32488498391005519934452616134656 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_direct
      (n := 2030531262941525972566614736923)
      (k := 92)
      (y := 1931447256879570512768032660349)
      (q := 58)
      (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 92 * 6561 = 32488498391005519934452616134656 := by decide
  have heq :
      2030531262941525972566614736923 + 2 ^ 92 * (6561 * u) =
        2030531262941525972566614736923 +
          32488498391005519934452616134656 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (2030531262941525972566614736923 +
          32488498391005519934452616134656 * u)
        (iter shortcut 92
          (2030531262941525972566614736923 +
            32488498391005519934452616134656 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 2030531262941525972566614736923 +
        32488498391005519934452616134656 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

/-- Fourth consequence-forced split on the same zero-tail lineage.  The
depth-33 unsplit reverse grammar still reconstructs ancestry only; the first
current protected consequence appears at depth 38, suffix value 21. -/
theorem r30_depth38_recursive_split_merger (u : Nat) :
    EarlierSourceCollision
      (682258466324619599600168265056283 +
        1039631948512176637902483716308992 * u)
      (iter shortcut 97
        (682258466324619599600168265056283 +
          1039631948512176637902483716308992 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_direct
      (n := 682258466324619599600168265056283)
      (k := 97)
      (y := 547565266808367096240406240668341)
      (q := 61)
      (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 97 * 6561 = 1039631948512176637902483716308992 := by decide
  have heq :
      682258466324619599600168265056283 + 2 ^ 97 * (6561 * u) =
        682258466324619599600168265056283 +
          1039631948512176637902483716308992 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (682258466324619599600168265056283 +
          1039631948512176637902483716308992 * u)
        (iter shortcut 97
          (682258466324619599600168265056283 +
            1039631948512176637902483716308992 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 682258466324619599600168265056283 +
        1039631948512176637902483716308992 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

#print axioms r30_depth25_recursive_split_merger
#print axioms r30_depth29_recursive_split_merger
#print axioms r30_depth33_pattern_falsifier_merger
#print axioms r30_depth38_recursive_split_merger

end CollatzFinal.SourceProduct
