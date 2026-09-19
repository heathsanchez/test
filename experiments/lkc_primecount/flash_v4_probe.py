#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

/-- Test n using only already discovered primes, in ascending order. -/
def isPrimeFrom : List Nat → Nat → Bool
  | [], n => decide (2 ≤ n)
  | p :: ps, n =>
      if n < 2 then false
      else if n < p * p then true
      else if n % p = 0 then false
      else isPrimeFrom ps n

/-- Incrementally discover primes and count them. No answer table is stored. -/
def primeScan : Nat → Nat → List Nat → Nat → Nat
  | 0, _, _, count => count
  | fuel + 1, k, primes, count =>
      let hp := isPrimeFrom primes k
      let primes' := if hp then primes ++ [k] else primes
      let count' := if hp then count + 1 else count
      primeScan fuel (k + 1) primes' count'

def countPrimeScan (n : Nat) : Nat :=
  if n < 2 then 0 else primeScan (n - 1) 2 [] 0

def impl (n : Nat) : Nat := countPrimeScan n

end Submission
'''
p=OUT/"Submission_v4_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
