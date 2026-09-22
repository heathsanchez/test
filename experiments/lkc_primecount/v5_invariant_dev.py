#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"v5_bitset_proof_dev.py"))
src=(OUT/"Submission_v5_bitset_proof_dev.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

extra=r'''
/-! V5 interaction invariant: the bitset denotes the least-factor frontier. -/

def AliveAt (p i : Nat) : Prop :=
  Nat.Prime i ∨ p ≤ i.minFac

def SieveInv (n p bits : Nat) : Prop :=
  ∀ i, 2 ≤ i → i ≤ n →
    bits.testBit i = decide (AliveAt p i)

theorem minFac_two_le_of_two_le (i : Nat) (hi : 2 ≤ i) :
    2 ≤ i.minFac := by
  have hne : i ≠ 1 := by omega
  exact (Nat.minFac_prime hne).two_le

theorem initialPrimeBits_alive
    (n i : Nat) (hi2 : 2 ≤ i) (hin : i ≤ n) :
    ((((1 <<< (n + 1)) - 1) ^^^ 3).testBit i) =
      decide (AliveAt 2 i) := by
  rw [initialPrimeBits_between n i hin]
  have hmf : 2 ≤ i.minFac := minFac_two_le_of_two_le i hi2
  simp [AliveAt, hi2, hmf]

theorem initial_sieve_inv (n : Nat) :
    SieveInv n 2 (((1 <<< (n + 1)) - 1) ^^^ 3) := by
  intro i hi2 hin
  exact initialPrimeBits_alive n i hi2 hin

theorem alive_self_iff_prime (p : Nat) (hp2 : 2 ≤ p) :
    AliveAt p p ↔ Nat.Prime p := by
  constructor
  · intro h
    rcases h with hp | hmin
    · exact hp
    · apply Nat.prime_def_minFac.2
      constructor
      · exact hp2
      · exact le_antisymm (Nat.minFac_le (by omega)) hmin
  · intro hp
    exact Or.inl hp

theorem alive_stop_iff_prime
    (n p i : Nat) (hp2 : 2 ≤ p)
    (hi2 : 2 ≤ i) (hin : i ≤ n)
    (hstop : n < p * p) :
    AliveAt p i ↔ Nat.Prime i := by
  constructor
  · intro h
    rcases h with hip | hmin
    · exact hip
    · by_contra hcomp
      have hsq := Nat.minFac_sq_le_self (by omega : 0 < i) hcomp
      have hmul : p * p ≤ i.minFac * i.minFac :=
        Nat.mul_le_mul hmin hmin
      have hsq' : i.minFac * i.minFac ≤ i := by
        simpa [pow_two] using hsq
      have hpn : p * p ≤ n :=
        le_trans hmul (le_trans hsq' hin)
      omega
  · intro hip
    exact Or.inl hip

theorem alive_step_of_not_prime
    (p i : Nat) (hp2 : 2 ≤ p) (hi2 : 2 ≤ i)
    (hp : ¬ Nat.Prime p) :
    AliveAt p i ↔ AliveAt (p + 1) i := by
  constructor
  · intro h
    rcases h with hip | hmin
    · exact Or.inl hip
    · right
      have hmfprime : Nat.Prime i.minFac :=
        Nat.minFac_prime (by omega : i ≠ 1)
      have hne : i.minFac ≠ p := by
        intro heq
        apply hp
        simpa [heq] using hmfprime
      omega
  · intro h
    rcases h with hip | hmin
    · exact Or.inl hip
    · exact Or.inr (by omega)

theorem sieve_inv_step_of_not_prime
    (n p bits : Nat) (hp2 : 2 ≤ p)
    (hp : ¬ Nat.Prime p)
    (hinv : SieveInv n p bits) :
    SieveInv n (p + 1) bits := by
  intro i hi2 hin
  rw [hinv i hi2 hin]
  have hiff := alive_step_of_not_prime p i hp2 hi2 hp
  exact congrArg decide (propext hiff)
'''

p=OUT/"Submission_v5_invariant_dev.lean"
p.write_text(prefix+"\n"+extra+"\nend Submission\n")
print(f"generated {p} bytes={len(p.read_bytes())}")
