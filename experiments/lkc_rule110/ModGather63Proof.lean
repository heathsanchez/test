import Spec

namespace ModGather63

set_option maxRecDepth 1048576
set_option maxHeartbeats 4000000

/-- The modulus that turns one 64-bit lane step into one dense-bit step. -/
def modulus : Nat := 0xfffffffffffffffe

theorem pow64_mod_eq_two : (2 ^ 64) % modulus = 2 := by
  decide

theorem two_mod_eq_two : 2 % modulus = 2 := by
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

/-- Generic modular collapse. Keeping `m` abstract is important: it prevents
Lean from reducing a giant closed modulus while elaborating the induction
motive. -/
theorem sparse_mod_eq_dense_mod_generic
    (m : Nat)
    (h64 : (2 ^ 64) % m = 2)
    (h2 : 2 % m = 2)
    (b : Nat → Nat) (i n : Nat) :
    sparse b i n % m = dense b i n % m := by
  induction n generalizing i with
  | zero => rfl
  | succ n ih =>
      simp only [sparse, dense, Nat.shiftLeft_eq]
      rw [Nat.add_mod, Nat.add_mod]
      congr 1
      rw [Nat.mul_mod, h64, ih, Nat.mul_mod, h2]
      rw [Nat.mul_comm]

/-- Sparse and dense encodings have the same remainder modulo `2^64 - 2`. -/
theorem sparse_mod_eq_dense_mod
    (b : Nat → Nat) (i n : Nat) :
    sparse b i n % modulus = dense b i n % modulus :=
  sparse_mod_eq_dense_mod_generic modulus pow64_mod_eq_two two_mod_eq_two b i n

/-- For at most 63 lanes the dense value is strictly below `2^64 - 2`,
so the modular residue is the dense integer itself. -/
theorem sparse_mod_eq_dense
    (b : Nat → Nat) (hb : ∀ i, b i < 2) (i n : Nat) (hn : n ≤ 63) :
    sparse b i n % modulus = dense b i n := by
  have hcong := sparse_mod_eq_dense_mod b i n
  have hd := dense_lt_pow b hb i n
  have hp : 2 ^ n ≤ 2 ^ 63 := Nat.pow_le_pow_right (by omega) hn
  have h63 : 2 ^ 63 < modulus := by decide
  have hlt : dense b i n < modulus := by omega
  rw [Nat.mod_eq_of_lt hlt] at hcong
  exact hcong

end ModGather63
