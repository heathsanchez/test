import Submission

namespace DenseAlgebraProbe

open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem packMixBit_lt_probe (x k : Nat) :
    packMixBit x k < 2 ^ k := by
  induction k generalizing x with
  | zero => simp [packMixBit]
  | succ k ih =>
      simp only [packMixBit, Nat.pow_succ]
      have hb : (if mixBit31 x then 1 else 0) < 2 := by
        split <;> omega
      have ht := ih (x + stepConst)
      omega

theorem packMixBit_add_probe (x a b : Nat) :
    packMixBit x (a + b) =
      packMixBit x a + 2 ^ a * packMixBit (x + a * stepConst) b := by
  induction a generalizing x with
  | zero =>
      simp [packMixBit]
  | succ a ih =>
      simp only [Nat.succ_add, packMixBit, Nat.pow_succ]
      rw [ih (x + stepConst)]
      have hx :
          x + stepConst + a * stepConst =
            x + (a + 1) * stepConst := by
        unfold stepConst
        omega
      rw [hx, Nat.mul_add]
      have hmul :
          2 * (2 ^ a * packMixBit (x + (a + 1) * stepConst) b) =
            2 ^ a * 2 * packMixBit (x + (a + 1) * stepConst) b := by
        rw [← Nat.mul_assoc, Nat.mul_comm 2 (2 ^ a), Nat.mul_assoc]
      rw [hmul]
      exact (Nat.add_assoc _ _ _).symm

theorem packMixBit_mod_pow_probe (x a b : Nat) :
    packMixBit x (a + b) % 2 ^ a = packMixBit x a := by
  rw [packMixBit_add_probe]
  have hp := packMixBit_lt_probe x a
  simp [Nat.add_mod, Nat.mod_eq_of_lt hp]

end DenseAlgebraProbe
