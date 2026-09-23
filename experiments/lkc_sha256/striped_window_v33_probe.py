#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

body=r'''
/-!
V33 probe: four interleaved 4-word schedule stripes.

At each window advance:
  A=[w0,w4,w8,w12], B=[w1,w5,w9,w13],
  C=[w2,w6,w10,w14], D=[w3,w7,w11,w15]
become
  B, C, D, shift(A)+newWord.
Thus only one 128-bit stripe is shifted/updated per round.
-/

def lane32s (x sh : Nat) : Nat :=
  (x >>> sh) &&& w32

def stripeA0 (d : Digest) : Nat :=
  d.a ||| (d.e <<< 32) ||| (0x80000000 <<< 64)

def stripeB0 (d : Digest) : Nat :=
  d.b ||| (d.f <<< 32)

def stripeC0 (d : Digest) : Nat :=
  d.c ||| (d.g <<< 32)

def stripeD0 (d : Digest) : Nat :=
  d.d ||| (d.h <<< 32) ||| (256 <<< 96)

def roundsStriped :
    List Nat → Nat → Nat → Nat → Nat →
    Nat → Nat → Nat → Nat → Nat → Nat → Nat → Nat → Digest
  | [], _, _, _, _, a,b,c,d,e,f,g,h => ⟨a,b,c,d,e,f,g,h⟩
  | k :: ks, A,B,C,D, a,b,c,d,e,f,g,h =>
      let w0 := A &&& w32
      let w1 := B &&& w32
      let w9 := lane32s B 64
      let w14 := lane32s C 96
      let nw := (smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      let D' := (A >>> 32) ||| (nw <<< 96)
      roundsStriped ks B C D D' na a b c ne e f g

def fastStepV33 (d : Digest) : Digest :=
  let f := roundsStriped K
    (stripeA0 d) (stripeB0 d) (stripeC0 d) (stripeD0 d)
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implV33 (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepV33 (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''
p=OUT/"Submission_v33_striped_window_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
