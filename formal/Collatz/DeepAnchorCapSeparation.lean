import Collatz.MinimalBadTernaryBarrier

namespace CollatzFinal
namespace SourceProduct

/-- At fixed original source n, any endpoint whose (y+1) is divisible
by a sufficiently large power of two lies ABOVE the odd-inverse cap.
This needs no Collatz hypothesis. It prevents converting V103's
unbounded endpoint anchors directly into capped ternary hits. -/
theorem deep_anchor_not_capped
    (n y B : Nat)
    (hdiv : 2 ^ B ∣ y + 1)
    (hlarge : 3 * n + 3 ≤ 2 ^ (B + 1)) :
    ¬ (2 * y - 1 < 3 * n) := by
  have hle : 2 ^ B ≤ y + 1 :=
    Nat.le_of_dvd (by omega) hdiv
  have hbig : 3 * n + 3 ≤ 2 * 2 ^ B := by
    simpa [pow_succ, Nat.mul_comm] using hlarge
  intro hcap
  omega

/-- Every actual capped hit must have endpoint-anchor precision
bounded in terms of the ORIGINAL source, even if other later
endpoints have arbitrarily high precision. -/
theorem capped_endpoint_has_bounded_anchor
    (n y B : Nat)
    (hdiv : 2 ^ B ∣ y + 1)
    (hcap : 2 * y - 1 < 3 * n) :
    2 ^ (B + 1) < 3 * n + 3 := by
  apply Classical.byContradiction
  intro hbad
  have hlarge : 3 * n + 3 ≤ 2 ^ (B + 1) := by omega
  exact deep_anchor_not_capped n y B hdiv hlarge hcap

#print axioms deep_anchor_not_capped
#print axioms capped_endpoint_has_bounded_anchor

end SourceProduct
end CollatzFinal
