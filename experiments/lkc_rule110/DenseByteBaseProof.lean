import WideDenseByteProof
import Submission

namespace DenseByteSequence

open GenericPack
open WideGather
open WideDenseByte
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

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

theorem pack6Nat_lt64 (x : Nat) :
    pack6Nat x < 64 := by
  unfold pack6Nat
  have h0 := mixBit31Nat_lt2 x
  have h1 := mixBit31Nat_lt2 (x + stepConst)
  have h2 := mixBit31Nat_lt2 (x + stepConst + stepConst)
  have h3 := mixBit31Nat_lt2 (x + stepConst + stepConst + stepConst)
  have h4 := mixBit31Nat_lt2 (x + stepConst + stepConst + stepConst + stepConst)
  have h5 := mixBit31Nat_lt2
    (x + stepConst + stepConst + stepConst + stepConst + stepConst)
  omega

theorem pack8Nat_decomp6 (x : Nat) :
    pack8Nat x =
      pack6Nat x +
        64 * (mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst) +
        2 * mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)) := by
  unfold pack8Nat pack6Nat
  omega

theorem pack8Nat_mod64_eq_pack6Nat (x : Nat) :
    pack8Nat x % 64 = pack6Nat x := by
  rw [pack8Nat_decomp6]
  have hl := pack6Nat_lt64 x
  rw [Nat.add_mod, Nat.mod_eq_of_lt hl]
  have hm :
      (64 * (mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst) +
        2 * mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst))) % 64 = 0 := by
    rw [Nat.mul_mod]
    simp
  rw [hm]
  simp

theorem pack8Nat_lt256 (x : Nat) :
    pack8Nat x < 256 := by
  have h := dense8_lt x
  rw [dense8_eq_pack8Nat] at h
  simpa using h

end DenseByteSequence
