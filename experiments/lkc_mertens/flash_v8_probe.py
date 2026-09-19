#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def isPrimeFrom : List Nat → Nat → Bool
  | [], n => decide (2 ≤ n)
  | p :: ps, n =>
      if n < 2 then false
      else if n < p * p then true
      else if n % p = 0 then false
      else isPrimeFrom ps n

/-- Möbius by already discovered primes; repeated factors terminate immediately. -/
def mobiusFromPrimes : List Nat → Nat → Int → Int
  | _, 0, _ => 0
  | _, 1, sign => sign
  | [], _, sign => -sign
  | p :: ps, n, sign =>
      if n < p * p then -sign
      else if n % p = 0 then
        let q := n / p
        if q % p = 0 then 0
        else mobiusFromPrimes ps q (-sign)
      else
        mobiusFromPrimes ps n sign

/-- One prefix pass shares the discovered prime basis across all Möbius calls. -/
def mertensPrimeScan : Nat → Nat → List Nat → Int → Int
  | 0, _, _, acc => acc
  | fuel + 1, k, primes, acc =>
      let hp := isPrimeFrom primes k
      let mu := if k = 1 then 1 else mobiusFromPrimes primes k 1
      let primes' := if hp then primes ++ [k] else primes
      mertensPrimeScan fuel (k + 1) primes' (acc + mu)

def impl (n : Nat) : Int :=
  mertensPrimeScan (n + 1) 0 [] 0

end Submission
'''
p=OUT/"Submission_v8_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
