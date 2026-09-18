#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

K = [
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
]
packed_k = sum(k << (32*i) for i, k in enumerate(K))
packed_k_lit = hex(packed_k)

text = f'''import Spec

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

/-- 64 FIPS SHA-256 round constants, little-endian in 32-bit lanes. -/
def packedK : Nat := {packed_k_lit}

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
The live round machine is one Nat:
lanes 0..7 = a..h, lanes 8..23 = W[t]..W[t+15].
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

/-- Consume one packed K lane per round: no List allocation or zip/schedule object. -/
def roundsPackedK : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      roundsPackedK n (ks >>> 32) (machineRound st (ks &&& w32))

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
  feedForward (roundsPackedK 64 packedK (initialMachine digest))

def iterPackedSha : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedSha n (packedShaStep d)

def impl (n : Nat) : Nat :=
  let d0 := packDigestBits (seedDigest (sha256Seed n))
  encodeDigest (unpackDigestBits (iterPackedSha (sha256Steps n) d0))

end Submission
'''

p = OUT / "Submission_machine_v11.lean"
p.write_text(text)
print(f"generated {{p}} bytes={{len(text.encode())}} packedK_bits={{packed_k.bit_length()}}")
