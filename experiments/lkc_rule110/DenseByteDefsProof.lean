import WideDenseByteProof
import Submission

namespace DenseByteSequence

open GenericPack
open WideGather
open WideDenseByte
open Submission

def advanceBytes : Nat → Nat → Nat
  | x, 0 => x
  | x, n + 1 => advanceBytes (advance8 x) n

def packBytesNat : Nat → Nat → Nat
  | _, 0 => 0
  | x, n + 1 => pack8Nat x + 256 * packBytesNat (advance8 x) n

theorem advanceBytes_eq (x n : Nat) :
    advanceBytes x n = x + (8 * n) * stepConst := by
  induction n generalizing x with
  | zero =>
      simp [advanceBytes]
  | succ n ih =>
      simp only [advanceBytes]
      rw [ih (advance8 x), advance8_eq_swar]
      unfold stepConst
      omega

theorem mixBit31Nat_lt2 (x : Nat) :
    mixBit31Nat x < 2 := by
  unfold mixBit31Nat
  exact Nat.mod_lt _ (by decide)

end DenseByteSequence
