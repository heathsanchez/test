#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated";OUT.mkdir(parents=True,exist_ok=True)
text=r'''import Spec

namespace Submission

def clearBitIfSet (bits i : Nat) : Nat :=
  if bits.testBit i then bits ^^^ (1 <<< i) else bits

def toggleBit (bits i : Nat) : Nat := bits ^^^ (1 <<< i)

def clearMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, p, m, bits =>
      if n < m then bits
      else clearMultiples fuel n p (m + p) (clearBitIfSet bits m)

def sieveLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, bits => bits
  | fuel + 1, n, p, bits =>
      if n < p * p then bits
      else
        let bits' :=
          if bits.testBit p then clearMultiples (n + 1) n p (p * p) bits
          else bits
        sieveLoop fuel n (p + 1) bits'

def primeBits (n : Nat) : Nat :=
  if n < 2 then 0
  else sieveLoop (n + 1) n 2 (((1 <<< (n + 1)) - 1) ^^^ 3)

def toggleMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, p, m, bits =>
      if n < m then bits
      else toggleMultiples fuel n p (m + p) (toggleBit bits m)

def clearSquareMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, step, m, bits =>
      if n < m then bits
      else clearSquareMultiples fuel n step (m + step) (clearBitIfSet bits m)

def mobiusMasksLoop : Nat → Nat → Nat → Nat → Nat → Nat → Nat × Nat
  | 0, _, _, _, parity, squarefree => (parity, squarefree)
  | fuel + 1, n, p, primes, parity, squarefree =>
      if n < p then (parity, squarefree)
      else if primes.testBit p then
        let parity' := toggleMultiples (n + 1) n p p parity
        let pp := p * p
        let squarefree' :=
          if n < pp then squarefree
          else clearSquareMultiples (n + 1) n pp pp squarefree
        mobiusMasksLoop fuel n (p + 1) primes parity' squarefree'
      else
        mobiusMasksLoop fuel n (p + 1) primes parity squarefree

def sumMobiusBits : Nat → Nat → Nat → Nat → Int
  | 0, _, _, _ => 0
  | fuel + 1, i, parity, squarefree =>
      let mu : Int :=
        if squarefree.testBit i then
          if parity.testBit i then -1 else 1
        else 0
      mu + sumMobiusBits fuel (i + 1) parity squarefree

def impl (n : Nat) : Int :=
  if n = 0 then 0
  else
    let primes := primeBits n
    let squarefree0 := ((1 <<< (n + 1)) - 1) ^^^ 1
    let (parity, squarefree) :=
      mobiusMasksLoop (n + 1) n 2 primes 0 squarefree0
    sumMobiusBits n 1 parity squarefree

end Submission
'''
p=OUT/"Submission_v9_bitset_probe.lean";p.write_text(text);print(f"generated {p} bytes={len(text.encode())}")
