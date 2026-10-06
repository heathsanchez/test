import Mathlib

namespace CollatzFinal.SourceProduct

def NatBitIntervalNonzero (m lo hi : Nat) : Prop :=
  2 ^ lo ≤ m % (2 ^ hi)

theorem nat_lt_two_pow (n : Nat) : n < 2 ^ n := by
  induction n with
  | zero => decide
  | succ n ih =>
      have hp : 0 < 2 ^ n := Nat.pow_pos (by decide)
      simp only [Nat.pow_succ]
      omega

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

theorem bit_interval_zero_above_source
    {m lo hi : Nat}
    (hm : m < 2 ^ lo) :
    ¬ NatBitIntervalNonzero m lo hi := by
  intro h
  unfold NatBitIntervalNonzero at h
  have hmod : m % (2 ^ hi) ≤ m := Nat.mod_le _ _
  omega

theorem no_infinite_strict_refinement_no_two_zero
    (m : Nat)
    (p : Nat → Nat)
    (hstrict : ∀ i, p i < p (i + 1))
    (hpair : ∀ i,
      NatBitIntervalNonzero m (p i) (p (i + 1)) ∨
      NatBitIntervalNonzero m (p (i + 1)) (p (i + 2))) :
    False := by
  let i := m + 1
  have hge : i ≤ p i :=
    strict_precision_ge_index p hstrict i
  have hmp : m < p i := by
    dsimp [i] at hge
    omega
  have hpi : p i < 2 ^ p i :=
    nat_lt_two_pow (p i)
  have hm0 : m < 2 ^ p i := by
    omega
  have hz0 :
      ¬ NatBitIntervalNonzero m (p i) (p (i + 1)) :=
    bit_interval_zero_above_source hm0
  have hs := hstrict i
  have hp1 : p (i + 1) < 2 ^ p (i + 1) :=
    nat_lt_two_pow (p (i + 1))
  have hm1 : m < 2 ^ p (i + 1) := by
    omega
  have hz1 :
      ¬ NatBitIntervalNonzero m (p (i + 1)) (p (i + 2)) :=
    bit_interval_zero_above_source hm1
  rcases hpair i with h0 | h1
  · exact hz0 h0
  · exact hz1 h1

#print axioms nat_lt_two_pow
#print axioms strict_precision_ge_index
#print axioms bit_interval_zero_above_source
#print axioms no_infinite_strict_refinement_no_two_zero

end CollatzFinal.SourceProduct
