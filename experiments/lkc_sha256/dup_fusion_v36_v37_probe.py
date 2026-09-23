#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

wins=[f"w{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
types=" → ".join(["Nat"]*24+["Digest"])
nilpat=", ".join(["[]"]+["_"]*16+sts)
conspat=", ".join(["k :: ks"]+wins+sts)
nextargs=" ".join(wins[1:]+["nw","na","a","b","c","ne","e","f","g"])

body=f'''
/-! V36 pair-dup and V37 quad-dup probes. -/

def roundsPairDupV36 : List Nat → {types}
  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩
  | {conspat} =>
      let zae := (a ||| (e <<< 64)) * 4294967297
      let zww := (w1 ||| (w14 <<< 64)) * 4294967297
      let s0 := (zww >>> 7) ^^^ (zww >>> 18) ^^^ (w1 >>> 3)
      let s1 := (zww >>> 81) ^^^ (zww >>> 83) ^^^ (w14 >>> 10)
      let b0 := (zae >>> 2) ^^^ (zae >>> 13) ^^^ (zae >>> 22)
      let b1 := (zae >>> 70) ^^^ (zae >>> 75) ^^^ (zae >>> 89)
      let nw := (s1 + w9 + s0 + w0) &&& w32
      let t1 := h + b1 + chFast e f g + k + w0
      let t2 := b0 + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsPairDupV36 ks {nextargs}

def fastStepPairDupV36 (d : Digest) : Digest :=
  let f := roundsPairDupV36 K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implPairDupV36 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepPairDupV36
    (sha256Steps n) (seedDigest (sha256Seed n)))

def roundsQuadDupV37 : List Nat → {types}
  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩
  | {conspat} =>
      let z := (a ||| (e <<< 64) ||| (w1 <<< 128) ||| (w14 <<< 192)) * 4294967297
      let s0 := (z >>> 135) ^^^ (z >>> 146) ^^^ (w1 >>> 3)
      let s1 := (z >>> 209) ^^^ (z >>> 211) ^^^ (w14 >>> 10)
      let b0 := (z >>> 2) ^^^ (z >>> 13) ^^^ (z >>> 22)
      let b1 := (z >>> 70) ^^^ (z >>> 75) ^^^ (z >>> 89)
      let nw := (s1 + w9 + s0 + w0) &&& w32
      let t1 := h + b1 + chFast e f g + k + w0
      let t2 := b0 + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsQuadDupV37 ks {nextargs}

def fastStepQuadDupV37 (d : Digest) : Digest :=
  let f := roundsQuadDupV37 K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implQuadDupV37 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepQuadDupV37
    (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p=OUT/"Submission_dup_fusion_v36_v37_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
