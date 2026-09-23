#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

W32=(1<<32)-1
iv=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
iv_pack=sum(x << (32*i) for i,x in enumerate(iv))
fixed_win=(0x80000000 << (32*8)) | (256 << (32*15))
state_shift_mask=sum(W32 << (32*i) for i in [1,2,3,5,6,7])

text=f'''import Spec

namespace Submission

def dup32V35 (x : Nat) : Nat := x * 4294967297

def smallSigma0V35 (x : Nat) : Nat :=
  let z := dup32V35 x
  (z >>> 7) ^^^ (z >>> 18) ^^^ (x >>> 3)

def smallSigma1V35 (x : Nat) : Nat :=
  let z := dup32V35 x
  (z >>> 17) ^^^ (z >>> 19) ^^^ (x >>> 10)

def bigSigma0V35 (x : Nat) : Nat :=
  let z := dup32V35 x
  (z >>> 2) ^^^ (z >>> 13) ^^^ (z >>> 22)

def bigSigma1V35 (x : Nat) : Nat :=
  let z := dup32V35 x
  (z >>> 6) ^^^ (z >>> 11) ^^^ (z >>> 25)

def chV35 (x y z : Nat) : Nat :=
  z ^^^ (x &&& (y ^^^ z))

def majV35 (x y z : Nat) : Nat :=
  (x &&& y) ^^^ (z &&& (x ^^^ y))

def packedIVV35 : Nat := {iv_pack}
def fixedWindowV35 : Nat := {fixed_win}
def stateShiftMaskV35 : Nat := {state_shift_mask}

/-- One 512-bit window and one 256-bit working state. Lane 0 is least significant. -/
def roundsPackedV35 : List Nat → Nat → Nat → Nat
  | [], _, st => st
  | k :: ks, win, st =>
      let w0 := win &&& w32
      let w1 := (win >>> 32) &&& w32
      let w9 := (win >>> 288) &&& w32
      let w14 := (win >>> 448) &&& w32
      let a := st &&& w32
      let b := (st >>> 32) &&& w32
      let c := (st >>> 64) &&& w32
      let d := (st >>> 96) &&& w32
      let e := (st >>> 128) &&& w32
      let f := (st >>> 160) &&& w32
      let g := (st >>> 192) &&& w32
      let h := (st >>> 224) &&& w32
      let nw := (smallSigma1V35 w14 + w9 + smallSigma0V35 w1 + w0) &&& w32
      let t1 := h + bigSigma1V35 e + chV35 e f g + k + w0
      let t2 := bigSigma0V35 a + majV35 a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      let win' := (win >>> 32) ||| (nw <<< 480)
      let st' := ((st <<< 32) &&& stateShiftMaskV35) ||| na ||| (ne <<< 128)
      roundsPackedV35 ks win' st'

def feedForwardPackedV35 (f : Nat) : Nat :=
  let a := (iv.a + (f &&& w32)) &&& w32
  let b := (iv.b + ((f >>> 32) &&& w32)) &&& w32
  let c := (iv.c + ((f >>> 64) &&& w32)) &&& w32
  let d := (iv.d + ((f >>> 96) &&& w32)) &&& w32
  let e := (iv.e + ((f >>> 128) &&& w32)) &&& w32
  let ff := (iv.f + ((f >>> 160) &&& w32)) &&& w32
  let g := (iv.g + ((f >>> 192) &&& w32)) &&& w32
  let h := (iv.h + ((f >>> 224) &&& w32)) &&& w32
  a ||| (b <<< 32) ||| (c <<< 64) ||| (d <<< 96) |||
    (e <<< 128) ||| (ff <<< 160) ||| (g <<< 192) ||| (h <<< 224)

def fastStepPackedV35 (digest : Nat) : Nat :=
  let win := digest ||| fixedWindowV35
  feedForwardPackedV35 (roundsPackedV35 K win packedIVV35)

def iterPackedV35 : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedV35 n (fastStepPackedV35 d)

def packSeedDigestV35 (seed : Nat) : Nat :=
  let d := seedDigest seed
  d.a ||| (d.b <<< 32) ||| (d.c <<< 64) ||| (d.d <<< 96) |||
    (d.e <<< 128) ||| (d.f <<< 160) ||| (d.g <<< 192) ||| (d.h <<< 224)

def unpackDigestV35 (x : Nat) : Digest :=
  ⟨x &&& w32,
   (x >>> 32) &&& w32,
   (x >>> 64) &&& w32,
   (x >>> 96) &&& w32,
   (x >>> 128) &&& w32,
   (x >>> 160) &&& w32,
   (x >>> 192) &&& w32,
   (x >>> 224) &&& w32⟩

def implV35 (n : Nat) : Nat :=
  let d0 := packSeedDigestV35 (sha256Seed n)
  encodeDigest (unpackDigestV35 (iterPackedV35 (sha256Steps n) d0))

end Submission
'''
p=OUT/"Submission_bitpacked_v35_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
