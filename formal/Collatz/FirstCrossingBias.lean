import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- Before the first coefficient crossing, each odd-step contribution to
B / 3^q is at most 1/3. This elementary bound requires no logarithm theorem. -/
theorem elementary_bias_bound_of_no_earlier_crossing (n k : Nat)
    (hpre : ∀ i, i < k → 2 ^ i ≤ 3 ^ oddCount n i) :
    3 * bias n k ≤ oddCount n k * 3 ^ oddCount n k := by
  induction k with
  | zero => simp [bias, oddCount]
  | succ k ih =>
      have hi := ih (fun i h => hpre i (Nat.lt_trans h (Nat.lt_succ_self k)))
      have hp := hpre k (Nat.lt_succ_self k)
      by_cases h : iter shortcut k n % 2 = 0
      · simpa only [bias, oddCount, h, ite_true] using hi
      · simp only [bias, oddCount, h, ite_false]
        calc
          3 * (3 * bias n k + 2 ^ k) =
              3 * (3 * bias n k) + 3 * 2 ^ k := Nat.mul_add _ _ _
          _ ≤ 3 * (oddCount n k * 3 ^ oddCount n k) +
              3 * 3 ^ oddCount n k :=
            Nat.add_le_add (Nat.mul_le_mul_left 3 hi) (Nat.mul_le_mul_left 3 hp)
          _ = (oddCount n k + 1) * 3 ^ (oddCount n k + 1) := by
            simp [Nat.pow_succ, Nat.add_mul, Nat.mul_add, Nat.mul_assoc,
              Nat.mul_comm, Nat.mul_left_comm]

/-- Every nonempty first-crossing word has its terminal coefficient in
[2^(k-1), 2^k). The upper bound is supplied separately by the crossing. -/
theorem first_crossing_type_lower (n k : Nat)
    (hpre : ∀ i, i < k + 1 → 2 ^ i ≤ 3 ^ oddCount n i) :
    2 ^ (k + 1) ≤ 2 * 3 ^ oddCount n (k + 1) := by
  have hp := hpre k (Nat.lt_succ_self k)
  have hq : 3 ^ oddCount n k ≤ 3 ^ oddCount n (k + 1) := by
    by_cases h : iter shortcut k n % 2 = 0
    · simp [oddCount, h]
    · simp only [oddCount, h, ite_false, Nat.pow_succ]
      omega
  have hh := Nat.mul_le_mul_left 2 (Nat.le_trans hp hq)
  simpa only [Nat.pow_succ, Nat.mul_comm] using hh

/-- Exact finite source-cap interface: a first-crossing non-descent lies below
any floor satisfying the declared integer coefficient inequality.
This does not assert that a crossing exists or that any external floor holds. -/
theorem source_lt_floor_of_first_crossing_cap
    (n k bound : Nat)
    (hpre : ∀ i, i < k → 2 ^ i ≤ 3 ^ oddCount n i)
    (hnd : n ≤ iter shortcut k n)
    (hcap : oddCount n k * 3 ^ oddCount n k <
      3 * (2 ^ k - 3 ^ oddCount n k) * bound) :
    n < bound := by
  have ha := exact_affine n k
  have hs := Nat.mul_le_mul_left (2 ^ k) hnd
  rw [ha] at hs
  have hd : (2 ^ k - 3 ^ oddCount n k) * n ≤ bias n k := by
    rw [Nat.sub_mul]
    omega
  have hb := elementary_bias_bound_of_no_earlier_crossing n k hpre
  have hdn := Nat.mul_le_mul_left 3 hd
  have hscaled : 3 * (2 ^ k - 3 ^ oddCount n k) * n <
      3 * (2 ^ k - 3 ^ oddCount n k) * bound := by
    have hh := Nat.lt_of_le_of_lt (Nat.le_trans hdn hb) hcap
    simpa only [Nat.mul_assoc] using hh
  by_cases h : n < bound
  · exact h
  · have hbn : bound ≤ n := by omega
    have hh := Nat.mul_le_mul_left (3 * (2 ^ k - 3 ^ oddCount n k)) hbn
    omega

#print axioms elementary_bias_bound_of_no_earlier_crossing
#print axioms first_crossing_type_lower
#print axioms source_lt_floor_of_first_crossing_cap

end SourceProduct
end CollatzFinal
