#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def mask8 : Nat :=
  w32 ||| (w32 <<< 64) ||| (w32 <<< 128) ||| (w32 <<< 192) |||
  (w32 <<< 256) ||| (w32 <<< 320) ||| (w32 <<< 384) ||| (w32 <<< 448)

def mask16 : Nat :=
  mask8 ||| (w32 <<< 512) ||| (w32 <<< 576) ||| (w32 <<< 640) |||
  (w32 <<< 704) ||| (w32 <<< 768) ||| (w32 <<< 832) |||
  (w32 <<< 896) ||| (w32 <<< 960)

def lane4Mask : Nat := w32 <<< 256
def lane15Mask : Nat := w32 <<< 960

def lane64 (x i : Nat) : Nat :=
  (x >>> (64 * i)) &&& w32

def pack8Wide (a b c d e f g h : Nat) : Nat :=
  a ||| (b <<< 64) ||| (c <<< 128) ||| (d <<< 192) |||
  (e <<< 256) ||| (f <<< 320) ||| (g <<< 384) ||| (h <<< 448)

def packDigestWide (d : Digest) : Nat :=
  pack8Wide d.a d.b d.c d.d d.e d.f d.g d.h

def rotrWide (x n mask : Nat) : Nat :=
  ((x >>> n) ||| (x <<< (32 - n))) &&& mask

def smallSigma0Wide (x : Nat) : Nat :=
  (rotrWide x 7 mask16) ^^^ (rotrWide x 18 mask16) ^^^ ((x >>> 3) &&& mask16)

def smallSigma1Wide (x : Nat) : Nat :=
  (rotrWide x 17 mask16) ^^^ (rotrWide x 19 mask16) ^^^ ((x >>> 10) &&& mask16)

def bigSigma0Wide (x : Nat) : Nat :=
  (rotrWide x 2 mask8) ^^^ (rotrWide x 13 mask8) ^^^ (rotrWide x 22 mask8)

def bigSigma1Wide (x : Nat) : Nat :=
  (rotrWide x 6 mask8) ^^^ (rotrWide x 11 mask8) ^^^ (rotrWide x 25 mask8)

def chWide (s : Nat) : Nat :=
  let s1 := s >>> 64
  let s2 := s >>> 128
  (s &&& s1) ^^^ ((s ^^^ mask8) &&& s2)

def majWide (s : Nat) : Nat :=
  let s1 := s >>> 64
  let s2 := s >>> 128
  (s &&& s1) ^^^ (s &&& s2) ^^^ (s1 &&& s2)

def initialWindowWide (digest : Nat) : Nat :=
  digest ||| (0x80000000 <<< 512) ||| (256 <<< 960)

/--
Aligned SWAR round.
T1 is accumulated directly in destination lane 4 and T2 directly in lane 0.
64-bit spacing leaves enough guard bits that the five-term lane sum cannot
carry into a neighboring SHA word.
-/
def roundWideAligned (s win k : Nat) : Nat :=
  let bs1 := bigSigma1Wide s
  let bs0 := bigSigma0Wide s
  let cv := chWide s
  let mv := majWide s
  let t1Lane :=
    ((s >>> 192) + bs1 + cv + (k <<< 256) + (win <<< 256)) &&& lane4Mask
  let t2Lane := (bs0 + mv) &&& w32
  let newA := ((t1Lane >>> 256) + t2Lane) &&& w32
  let shifted := (s <<< 64) &&& mask8
  (shifted + t1Lane + newA) &&& mask8

/--
Generate the next schedule word directly in lane 15.  Each summand is aligned
by a whole-lane shift; no individual word extraction is required.
-/
def roundWindowAligned (win : Nat) : Nat :=
  let ss1 := smallSigma1Wide win
  let ss0 := smallSigma0Wide win
  let nextLane :=
    ((ss1 <<< 64) + (win <<< 384) + (ss0 <<< 896) + (win <<< 960)) &&& lane15Mask
  (win >>> 64) + nextLane

def runWideAligned : List Nat → Nat → Nat → Nat
  | [], s, _ => s
  | k :: ks, s, win =>
      runWideAligned ks
        (roundWideAligned s win k)
        (roundWindowAligned win)

def ivWide : Nat :=
  pack8Wide iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h

def packedShaStepWide (digest : Nat) : Nat :=
  let final := runWideAligned K ivWide (initialWindowWide digest)
  (final + ivWide) &&& mask8

def iterWide : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterWide n (packedShaStepWide d)

def encodeWide (d : Nat) : Nat :=
  (((((((lane64 d 0) * 4294967296 + lane64 d 1)
      * 4294967296 + lane64 d 2)
      * 4294967296 + lane64 d 3)
      * 4294967296 + lane64 d 4)
      * 4294967296 + lane64 d 5)
      * 4294967296 + lane64 d 6)
      * 4294967296 + lane64 d 7

def impl (n : Nat) : Nat :=
  let d0 := packDigestWide (seedDigest (sha256Seed n))
  encodeWide (iterWide (sha256Steps n) d0)

end Submission
'''

p=OUT/"Submission_aligned_wide_v19.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
