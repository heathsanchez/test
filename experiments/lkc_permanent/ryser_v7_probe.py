#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"support_v3.py"))
support=(OUT/"Support_v3.lean").read_text()
support_body=support.replace("import Spec\n\nnamespace Submission\n\n","",1)
support_body=support_body.rsplit("\nend Submission",1)[0]

core=r'''import Spec

namespace Submission

def bitNat (mask j : Nat) : Nat :=
  if mask.testBit j then 1 else 0

def rowSumSparse (dimension seed i mask : Nat) : Nat :=
  if dimension < 3 then
    Nat.fold dimension (fun j _ acc => acc + bitNat mask j) 0
  else
    bitNat mask i +
      bitNat mask (permanentColumnOne dimension seed i) +
      bitNat mask (permanentColumnTwo dimension seed i)

def rowsProduct : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, acc => acc
  | fuel + 1, dimension, seed, i, acc =>
      rowsProduct fuel dimension seed (i + 1)
        (acc * rowSumSparse dimension seed i)

def bitParity : Nat → Nat → Bool → Bool
  | 0, _, acc => acc
  | fuel + 1, mask, acc =>
      bitParity fuel (mask >>> 1)
        (if mask.testBit 0 then !acc else acc)

def ryserLoop : Nat → Nat → Nat → Nat → Int → Int
  | 0, _, _, _, acc => acc
  | fuel + 1, dimension, seed, mask, acc =>
      let prod := rowsProduct dimension dimension seed 0 1
      let term : Int := prod
      let acc' :=
        if bitParity dimension mask false then acc - term else acc + term
      ryserLoop fuel dimension seed (mask + 1) acc'

def permanentRyser (dimension seed : Nat) : Nat :=
  if dimension = 0 then 1
  else if dimension = 1 then 1
  else if dimension = 2 then 2
  else
    let total := ryserLoop (1 <<< dimension) dimension seed 0 0
    Int.toNat (if bitParity dimension dimension false then -total else total)

def impl (n : Nat) : Nat :=
  permanentRyser (permanentDimension n) (permanentSeed n)

end Submission
'''
# Correct a deliberately simple source transformation: rowsProduct needs the subset mask.
core=core.replace(
'''def rowsProduct : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, acc => acc
  | fuel + 1, dimension, seed, i, acc =>
      rowsProduct fuel dimension seed (i + 1)
        (acc * rowSumSparse dimension seed i)

def bitParity''',
'''def rowsProduct : Nat → Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, _, acc => acc
  | fuel + 1, dimension, seed, mask, i, acc =>
      rowsProduct fuel dimension seed mask (i + 1)
        (acc * rowSumSparse dimension seed i mask)

def bitParity''')
core=core.replace(
'let prod := rowsProduct dimension dimension seed 0 1',
'let prod := rowsProduct dimension dimension seed mask 0 1')
text=core+support_body+"\nend Submission\n"
p=OUT/"Submission_v7_ryser_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
