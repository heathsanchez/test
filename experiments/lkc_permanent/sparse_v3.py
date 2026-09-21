#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

core=r'''import Spec

namespace Submission

def permanentSparse : Nat → Nat → List Nat → Nat → Nat
  | _dimension, _seed, [], _ => 1
  | dimension, seed, i :: is, used =>
      if dimension < 3 then
        (List.range dimension).foldl (fun total j =>
          if used.testBit j then total
          else total + permanentSparse dimension seed is (used ||| (1 <<< j))) 0
      else
        let c1 := permanentColumnOne dimension seed i
        let c2 := permanentColumnTwo dimension seed i
        (if used.testBit i then 0 else permanentSparse dimension seed is (used ||| (1 <<< i))) +
        (if used.testBit c1 then 0 else permanentSparse dimension seed is (used ||| (1 <<< c1))) +
        (if used.testBit c2 then 0 else permanentSparse dimension seed is (used ||| (1 <<< c2)))

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0
'''

# Probe exact semantic equivalence on small complete dimensions.
probe=core+r'''
example : impl 0 = permanentSpecN 0 := by decide +kernel
example : impl 4294967296 = permanentSpecN 4294967296 := by decide +kernel
example : impl 8589934592 = permanentSpecN 8589934592 := by decide +kernel
example : impl 12884901888 = permanentSpecN 12884901888 := by decide +kernel
example : impl 12884901889 = permanentSpecN 12884901889 := by decide +kernel
example : impl 17179869184 = permanentSpecN 17179869184 := by decide +kernel
example : impl 21474836487 = permanentSpecN 21474836487 := by decide +kernel

end Submission
'''
(OUT/"Probe_v3.lean").write_text(probe)

submission=core+r'''
/-- RED frontier: prove the three generated columns are exactly the nonzero row support
for every dimension >= 3, with the full-square fallback below dimension 3. -/
theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rfl

end Submission
'''
(OUT/"Submission_v3.lean").write_text(submission)
print(f"generated {(OUT/'Probe_v3.lean')} bytes={(OUT/'Probe_v3.lean').stat().st_size}")
print(f"generated {(OUT/'Submission_v3.lean')} bytes={(OUT/'Submission_v3.lean').stat().st_size}")
