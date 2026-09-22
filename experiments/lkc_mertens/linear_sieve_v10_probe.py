#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

structure LinState where
  mu : Array Int
  composite : Array Bool
  primes : Array Nat

def linInner (n i : Nat) : Nat → Nat → LinState → LinState
  | 0, _, st => st
  | fuel + 1, j, st =>
      if j < st.primes.size then
        let p := st.primes.get! j
        let ip := i * p
        if n < ip then st
        else
          let st1 : LinState :=
            { st with composite := st.composite.set! ip true }
          if i % p = 0 then
            { st1 with mu := st1.mu.set! ip 0 }
          else
            let mui := st1.mu.get! i
            let st2 : LinState :=
              { st1 with mu := st1.mu.set! ip (-mui) }
            linInner n i fuel (j + 1) st2
      else st

def linOuter (n : Nat) : Nat → Nat → LinState → LinState
  | 0, _, st => st
  | fuel + 1, i, st =>
      if n < i then st
      else
        let st1 :=
          if st.composite.get! i then st
          else
            { st with
              primes := st.primes.push i
              mu := st.mu.set! i (-1) }
        let st2 := linInner n i (n + 1) 0 st1
        linOuter n fuel (i + 1) st2

def linMu (n : Nat) : Array Int :=
  if n = 0 then #[0]
  else
    let mu0 := (Array.replicate (n + 1) (0 : Int)).set! 1 1
    let st0 : LinState :=
      { mu := mu0
        composite := Array.replicate (n + 1) false
        primes := #[] }
    (linOuter n n 2 st0).mu

def sumMu : Nat → Nat → Array Int → Int
  | 0, _, _ => 0
  | fuel + 1, i, mu => mu.get! i + sumMu fuel (i + 1) mu

def impl (n : Nat) : Int :=
  if n = 0 then 0 else sumMu n 1 (linMu n)

end Submission
'''
p=OUT/"Submission_v10_linear_sieve_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
