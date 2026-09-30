import Collatz.AffineBudget

namespace CollatzFinal.SourceProduct

/-- The block of `width` binary digits of `m` beginning at bit `lo`. -/
def sourceBitBlock (m lo width : Nat) : Nat :=
  (m / 2 ^ lo) % 2 ^ width

/-- Once the precision lies above the whole natural number, every newly
exposed bit block is zero. -/
theorem sourceBitBlock_zero_of_lt_pow
    {m lo width : Nat} (h : m < 2 ^ lo) :
    sourceBitBlock m lo width = 0 := by
  simp [sourceBitBlock, Nat.div_eq_of_lt h]

/-- Crude but universal natural ceiling: all bits at positions m+1 and above
are zero.  No logarithm machinery is needed. -/
theorem sourceBitBlock_zero_above_self
    (m width : Nat) :
    sourceBitBlock m (m + 1) width = 0 := by
  apply sourceBitBlock_zero_of_lt_pow
  have h := (m + 1).lt_two_pow_self
  omega

/-- Any strictly increasing natural precision sequence has reached precision
at least i by its i-th switch. -/
theorem strict_precision_ge_index
    (p : Nat → Nat)
    (hstrict : ∀ i, p i < p (i + 1)) :
    ∀ i, i ≤ p i := by
  intro i
  induction i with
  | zero => omega
  | succ i ih =>
      have hs := hstrict i
      omega

/-- Natural-bit bar.

For one fixed ordinary natural source/owner m, if every genuine switch strictly
increases source-pulled 2-adic precision p_i, then after finitely many switches
all subsequently exposed source-bit blocks are forced to be zero.

This is the abstract naturalness reduction needed by the Collatz switch
programme.  It does not assert that the zero-exposure switch grammar itself
terminates. -/
theorem natural_switch_tail_zero
    (m : Nat) (p : Nat → Nat)
    (hstrict : ∀ i, p i < p (i + 1)) :
    ∀ i, m + 1 ≤ i →
      sourceBitBlock m (p i) (p (i + 1) - p i) = 0 := by
  intro i hi
  have hindex : i ≤ p i :=
    strict_precision_ge_index p hstrict i
  have hexp : m + 1 ≤ p i :=
    Nat.le_trans hi hindex
  have hsmall : m < 2 ^ (m + 1) := by
    have h := (m + 1).lt_two_pow_self
    omega
  have hpows : 2 ^ (m + 1) ≤ 2 ^ (p i) := by
    exact Nat.pow_le_pow_right (by decide : 1 ≤ (2 : Nat)) hexp
  have hm : m < 2 ^ (p i) :=
    Nat.lt_of_lt_of_le hsmall hpows
  exact sourceBitBlock_zero_of_lt_pow hm

/-- Hence an infinite switch sequence cannot expose a nonzero fresh bit block
at every switch around one fixed natural owner. -/
theorem no_infinite_all_nonzero_exposure
    (m : Nat) (p : Nat → Nat)
    (hstrict : ∀ i, p i < p (i + 1))
    (hnonzero :
      ∀ i, sourceBitBlock m (p i) (p (i + 1) - p i) ≠ 0) :
    False := by
  have hz :=
    natural_switch_tail_zero m p hstrict (m + 1) (by omega)
  exact hnonzero (m + 1) hz

#print axioms sourceBitBlock_zero_of_lt_pow
#print axioms strict_precision_ge_index
#print axioms natural_switch_tail_zero
#print axioms no_infinite_all_nonzero_exposure

end CollatzFinal.SourceProduct
