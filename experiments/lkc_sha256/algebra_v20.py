#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

structure Window where
  x0 : Nat
  x1 : Nat
  x2 : Nat
  x3 : Nat
  x4 : Nat
  x5 : Nat
  x6 : Nat
  x7 : Nat
  x8 : Nat
  x9 : Nat
  x10 : Nat
  x11 : Nat
  x12 : Nat
  x13 : Nat
  x14 : Nat
  x15 : Nat

/-- Raw rotate; callers combine several rotations and mask once at the end. -/
def rotrRaw (x n : Nat) : Nat :=
  (x >>> n) ||| (x <<< (32 - n))

def smallSigma0Fast (x : Nat) : Nat :=
  (rotrRaw x 7 ^^^ rotrRaw x 18 ^^^ (x >>> 3)) &&& w32

def smallSigma1Fast (x : Nat) : Nat :=
  (rotrRaw x 17 ^^^ rotrRaw x 19 ^^^ (x >>> 10)) &&& w32

def bigSigma0Fast (x : Nat) : Nat :=
  (rotrRaw x 2 ^^^ rotrRaw x 13 ^^^ rotrRaw x 22) &&& w32

def bigSigma1Fast (x : Nat) : Nat :=
  (rotrRaw x 6 ^^^ rotrRaw x 11 ^^^ rotrRaw x 25) &&& w32

/-- One final reduction mod 2^32 instead of three nested add32 masks. -/
def Window.nextFast (w : Window) : Nat :=
  (smallSigma1Fast w.x14 + w.x9 + smallSigma0Fast w.x1 + w.x0) &&& w32

def Window.push (w : Window) (x : Nat) : Window :=
  ⟨w.x1, w.x2, w.x3, w.x4, w.x5, w.x6, w.x7, w.x8,
   w.x9, w.x10, w.x11, w.x12, w.x13, w.x14, w.x15, x⟩

def initialWindow (d : Digest) : Window :=
  ⟨d.a, d.b, d.c, d.d, d.e, d.f, d.g, d.h,
   0x80000000, 0, 0, 0, 0, 0, 0, 256⟩

/-- Lower-operation Boolean identities for SHA Ch and Maj. -/
def chFast (x y z : Nat) : Nat :=
  z ^^^ (x &&& (y ^^^ z))

def majFast (x y z : Nat) : Nat :=
  (x &&& y) ^^^ (z &&& (x ^^^ y))

/--
The round algebra only needs the final sums modulo 2^32.
This removes three intermediate masks from t1 on every round.
-/
def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := (s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w) &&& w32
  let t2 := (bigSigma0Fast s.a + majFast s.a s.b s.c) &&& w32
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩

/-- Stream the message schedule and constants together; no 64-word schedule or zip. -/
def roundsFast : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, win, s =>
      let next := win.nextFast
      roundsFast ks (win.push next) (roundFast s k win.x0)

def feedForwardIV (f : Digest) : Digest :=
  ⟨(iv.a + f.a) &&& w32, (iv.b + f.b) &&& w32,
   (iv.c + f.c) &&& w32, (iv.d + f.d) &&& w32,
   (iv.e + f.e) &&& w32, (iv.f + f.f) &&& w32,
   (iv.g + f.g) &&& w32, (iv.h + f.h) &&& w32⟩

def fastStepAlgebra (d : Digest) : Digest :=
  feedForwardIV (roundsFast K (initialWindow d) iv)

def impl (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepAlgebra (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p=OUT/"Submission_algebra_v20.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
