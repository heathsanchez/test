import DenseByteBaseProof

namespace DenseByteSequence

open GenericPack
open WideGather
open WideDenseByte
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem packBytesNat_lt (x n : Nat) :
    packBytesNat x n < 256 ^ n := by
  induction n generalizing x with
  | zero =>
      simp [packBytesNat]
  | succ n ih =>
      simp only [packBytesNat, Nat.pow_succ]
      have hb := pack8Nat_lt256 x
      have ht := ih (advance8 x)
      omega

theorem packBytesNat_add (x a b : Nat) :
    packBytesNat x (a + b) =
      packBytesNat x a +
        256 ^ a * packBytesNat (advanceBytes x a) b := by
  induction a generalizing x with
  | zero =>
      simp [packBytesNat, advanceBytes]
  | succ a ih =>
      simp only [Nat.succ_add, packBytesNat, advanceBytes, Nat.pow_succ]
      rw [ih (advance8 x), Nat.mul_add]
      have hmul :
          256 * (256 ^ a * packBytesNat (advanceBytes (advance8 x) a) b) =
            256 ^ a * 256 * packBytesNat (advanceBytes (advance8 x) a) b := by
        rw [← Nat.mul_assoc, Nat.mul_comm 256 (256 ^ a), Nat.mul_assoc]
      rw [hmul]
      exact (Nat.add_assoc _ _ _).symm

theorem packByteTailNat_eq_bytes_tail (x n : Nat) :
    packByteTailNat x n =
      packBytesNat x n +
        256 ^ n * pack6Nat (advanceBytes x n) := by
  induction n generalizing x with
  | zero =>
      simp [packByteTailNat, packBytesNat, advanceBytes]
  | succ n ih =>
      simp only [packByteTailNat, packBytesNat, advanceBytes, Nat.pow_succ]
      rw [ih (advance8 x), Nat.mul_add]
      have hmul :
          256 * (256 ^ n * pack6Nat (advanceBytes (advance8 x) n)) =
            256 ^ n * 256 * pack6Nat (advanceBytes (advance8 x) n) := by
        rw [← Nat.mul_assoc, Nat.mul_comm 256 (256 ^ n), Nat.mul_assoc]
      rw [hmul]
      exact (Nat.add_assoc _ _ _).symm

theorem pow256_eq_pow2 (n : Nat) :
    256 ^ n = 2 ^ (8 * n) := by
  induction n with
  | zero =>
      simp
  | succ n ih =>
      rw [Nat.pow_succ, Nat.mul_succ, Nat.pow_add, ← ih]
      rw [show 2 ^ 8 = 256 by decide]

theorem packBytesNat_double (x n : Nat) :
    packW (8 * n)
      (packBytesNat x n)
      (packBytesNat (x + (8 * n) * stepConst) n) =
      packBytesNat x (n + n) := by
  unfold packW
  rw [packBytesNat_add x n n]
  rw [advanceBytes_eq]
  rw [Nat.shiftLeft_eq]
  rw [← pow256_eq_pow2 n]
  rw [Nat.mul_comm
    (packBytesNat (x + (8 * n) * stepConst) n)
    (256 ^ n)]

theorem packBytesNat_one (x : Nat) :
    packBytesNat x 1 = pack8Nat x := by
  simp [packBytesNat]

end DenseByteSequence
