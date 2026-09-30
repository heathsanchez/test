import Collatz.GuardedDyadicSwitch

namespace CollatzFinal.SourceProduct

/-- One past the highest possible nonzero binary digit of a natural. -/
def naturalSupportBound (n : Nat) : Nat := n.log2 + 1

/-- No source bits change between precisions p and q.  Once both moduli exceed
the finite binary support of n, this holds automatically. -/
def ZeroBitBlock (n p q : Nat) : Prop :=
  n % (2 ^ q) = n % (2 ^ p)

theorem natural_lt_two_pow_support (n : Nat) :
    n < 2 ^ naturalSupportBound n := by
  simpa [naturalSupportBound] using Nat.lt_log2_self (n := n)

theorem natural_lt_two_pow_of_support_le
    {n p : Nat} (hp : naturalSupportBound n ≤ p) :
    n < 2 ^ p := by
  exact Nat.lt_of_lt_of_le (natural_lt_two_pow_support n)
    (Nat.pow_le_pow_right (by decide : 0 < (2 : Nat)) hp)

theorem zero_bit_block_above_support
    {n p q : Nat}
    (hp : naturalSupportBound n ≤ p) (hpq : p ≤ q) :
    ZeroBitBlock n p q := by
  have hnP : n < 2 ^ p := natural_lt_two_pow_of_support_le hp
  have hsupQ : naturalSupportBound n ≤ q := Nat.le_trans hp hpq
  have hnQ : n < 2 ^ q := natural_lt_two_pow_of_support_le hsupQ
  simp [ZeroBitBlock, Nat.mod_eq_of_lt hnP, Nat.mod_eq_of_lt hnQ]

theorem strict_precision_linear_lower
    (p : Nat → Nat) (hstep : ∀ i, p i < p (i + 1)) :
    ∀ i, p 0 + i ≤ p i := by
  intro i
  induction i with
  | zero => simp
  | succ i ih =>
      have hs : p i + 1 ≤ p (i + 1) := by
        exact Nat.succ_le_of_lt (hstep i)
      omega

/-- A strictly improving precision sequence around one fixed natural source
eventually exposes only zero source-bit blocks. -/
theorem strict_precision_eventual_zero_blocks
    (n : Nat) (p : Nat → Nat)
    (hstep : ∀ i, p i < p (i + 1)) :
    ∀ i, naturalSupportBound n ≤ i →
      ZeroBitBlock n (p i) (p (i + 1)) := by
  intro i hi
  have hlin := strict_precision_linear_lower p hstep i
  have hp : naturalSupportBound n ≤ p i := by
    omega
  have hpq : p i ≤ p (i + 1) := Nat.le_of_lt (hstep i)
  exact zero_bit_block_above_support hp hpq

#print axioms natural_lt_two_pow_support
#print axioms zero_bit_block_above_support
#print axioms strict_precision_linear_lower
#print axioms strict_precision_eventual_zero_blocks

end CollatzFinal.SourceProduct
