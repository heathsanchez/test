import Spec

namespace ModGather63

set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

/-- The modulus that turns one 64-bit lane step into one dense-bit step. -/
def modulus : Nat := 0xfffffffffffffffe

theorem pow64_modeq_two : Nat.ModEq modulus (2 ^ 64) 2 := by
  decide

/-- A generic sparse bit sequence, one bit every 64 positions. -/
def sparse (b : Nat → Nat) : Nat → Nat → Nat
  | _, 0 => 0
  | i, n + 1 => b i + (sparse b (i + 1) n <<< 64)

/-- The corresponding ordinary dense bit sequence. -/
def dense (b : Nat → Nat) : Nat → Nat → Nat
  | _, 0 => 0
  | i, n + 1 => b i + 2 * dense b (i + 1) n

theorem dense_lt_pow
    (b : Nat → Nat) (hb : ∀ i, b i < 2) (i n : Nat) :
    dense b i n < 2 ^ n := by
  induction n generalizing i with
  | zero => simp [dense]
  | succ n ih =>
      simp only [dense]
      have hbit := hb i
      have htail := ih (i + 1)
      rw [Nat.pow_succ]
      omega

theorem sparse_modeq_dense
    (b : Nat → Nat) (i n : Nat) :
    Nat.ModEq modulus (sparse b i n) (dense b i n) := by
  induction n generalizing i with
  | zero => rfl
  | succ n ih =>
      simp only [sparse, dense, Nat.shiftLeft_eq]
      exact (Nat.ModEq.refl (b i)).add ((ih (i + 1)).mul pow64_modeq_two)

/-- For at most 63 lanes the dense value is strictly below `2^64 - 2`,
so the modular residue is the dense integer itself, not merely congruent to it. -/
theorem sparse_mod_eq_dense
    (b : Nat → Nat) (hb : ∀ i, b i < 2) (i n : Nat) (hn : n ≤ 63) :
    sparse b i n % modulus = dense b i n := by
  have hcong := sparse_modeq_dense b i n
  have hd := dense_lt_pow b hb i n
  have hp : 2 ^ n ≤ 2 ^ 63 := Nat.pow_le_pow_right (by omega) hn
  have h63 : 2 ^ 63 < modulus := by decide
  have hlt : dense b i n < modulus := by omega
  simpa [Nat.ModEq, Nat.mod_eq_of_lt hlt] using hcong

end ModGather63
