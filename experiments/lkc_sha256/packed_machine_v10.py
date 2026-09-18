#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

def lane32 (x i : Nat) : Nat :=
  (x >>> (32 * i)) &&& w32

def pack8 (a b c d e f g h : Nat) : Nat :=
  a ||| (b <<< 32) ||| (c <<< 64) ||| (d <<< 96) |||
  (e <<< 128) ||| (f <<< 160) ||| (g <<< 192) ||| (h <<< 224)

def packDigestBits (d : Digest) : Nat :=
  pack8 d.a d.b d.c d.d d.e d.f d.g d.h

def unpackDigestBits (x : Nat) : Digest :=
  ⟨lane32 x 0, lane32 x 1, lane32 x 2, lane32 x 3,
   lane32 x 4, lane32 x 5, lane32 x 6, lane32 x 7⟩

/-- Initial 16-word message window, packed in little-endian 32-bit lanes. -/
def initialWindowBits (d : Nat) : Nat :=
  d ||| (0x80000000 <<< 256) ||| (256 <<< 480)

def nextWindowWord (w : Nat) : Nat :=
  add32
    (add32 (smallSigma1 (lane32 w 14)) (lane32 w 9))
    (add32 (smallSigma0 (lane32 w 1)) (lane32 w 0))

def advanceWindowBits (w : Nat) : Nat :=
  (w >>> 32) ||| (nextWindowWord w <<< 480)

/--
The entire live round machine is one Nat:
  lanes 0..7   = working digest a..h
  lanes 8..23  = rolling schedule window W[t]..W[t+15]
-/
def initialMachine (digest : Nat) : Nat :=
  digest ||| (initialWindowBits digest <<< 256)

def machineRound (st k : Nat) : Nat :=
  let a := lane32 st 0
  let b := lane32 st 1
  let c := lane32 st 2
  let d := lane32 st 3
  let e := lane32 st 4
  let f := lane32 st 5
  let g := lane32 st 6
  let h := lane32 st 7
  let w := st >>> 256
  let wt := lane32 w 0
  let t1 := add32 h
    (add32 (bigSigma1 e) (add32 (ch e f g) (add32 k wt)))
  let t2 := add32 (bigSigma0 a) (maj a b c)
  let digest' := pack8
    (add32 t1 t2) a b c (add32 d t1) e f g
  digest' ||| (advanceWindowBits w <<< 256)

def roundsMachine : List Nat → Nat → Nat
  | [], st => st
  | k :: ks, st => roundsMachine ks (machineRound st k)

def feedForward (st : Nat) : Nat :=
  pack8
    (add32 iv.a (lane32 st 0))
    (add32 iv.b (lane32 st 1))
    (add32 iv.c (lane32 st 2))
    (add32 iv.d (lane32 st 3))
    (add32 iv.e (lane32 st 4))
    (add32 iv.f (lane32 st 5))
    (add32 iv.g (lane32 st 6))
    (add32 iv.h (lane32 st 7))

def packedShaStep (digest : Nat) : Nat :=
  feedForward (roundsMachine K (initialMachine digest))

def iterPackedSha : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedSha n (packedShaStep d)

def impl (n : Nat) : Nat :=
  let d0 := packDigestBits (seedDigest (sha256Seed n))
  encodeDigest (unpackDigestBits (iterPackedSha (sha256Steps n) d0))

end Submission
'''

p = OUT / "Submission_machine_v10.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
