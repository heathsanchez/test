#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"nozip_v1.py"))
v1=(OUT/"Submission_v1.lean").read_text()
prefix=v1.split("def impl (n : Nat) : Nat :=",1)[0]

body=r'''
def base32 : Nat := 4294967296

def packDigestLE (d : Digest) : Nat :=
  d.a + base32 * (
  d.b + base32 * (
  d.c + base32 * (
  d.d + base32 * (
  d.e + base32 * (
  d.f + base32 * (
  d.g + base32 * d.h))))))

def unpackDigestLE (x : Nat) : Digest :=
  let a := x % base32
  let x := x / base32
  let b := x % base32
  let x := x / base32
  let c := x % base32
  let x := x / base32
  let d := x % base32
  let x := x / base32
  let e := x % base32
  let x := x / base32
  let f := x % base32
  let x := x / base32
  let g := x % base32
  let h := (x / base32) % base32
  ⟨a,b,c,d,e,f,g,h⟩

def packedFastStep (x : Nat) : Nat :=
  packDigestLE (fastStepNoZip (unpackDigestLE x))

/--
Strict chain iterator.  The Nat match forces each complete digest before the
next hash step, preventing the kernel from retaining the entire unevaluated
chain trajectory.
-/
def iterPackedStrict : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d =>
      let next := packedFastStep d
      match next with
      | 0 => iterPackedStrict n 0
      | m + 1 => iterPackedStrict n (m + 1)

def impl (n : Nat) : Nat :=
  let d0 := packDigestLE (seedDigest (sha256Seed n))
  encodeDigest (unpackDigestLE (iterPackedStrict (sha256Steps n) d0))

end Submission
'''

text=prefix+body
p=OUT/"Submission_strict_chain_v17.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
