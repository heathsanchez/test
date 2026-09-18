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
B=1<<32
packed_k=sum(k*(B**i) for i,k in enumerate(K))

text=f'''import Spec

namespace Submission

def base32 : Nat := 4294967296

def laneB (x i : Nat) : Nat :=
  (x / (base32 ^ i)) % base32

def pack8B (a b c d e f g h : Nat) : Nat :=
  a + base32 * (
  b + base32 * (
  c + base32 * (
  d + base32 * (
  e + base32 * (
  f + base32 * (
  g + base32 * h))))))

def packDigestB (d : Digest) : Nat :=
  pack8B d.a d.b d.c d.d d.e d.f d.g d.h

def unpackDigestB (x : Nat) : Digest :=
  ⟨laneB x 0, laneB x 1, laneB x 2, laneB x 3,
   laneB x 4, laneB x 5, laneB x 6, laneB x 7⟩

def packedKBase : Nat := {packed_k}

/-- 16 message words in base-2^32 little-endian lanes. -/
def initialWindowB (digest : Nat) : Nat :=
  digest +
  0x80000000 * (base32 ^ 8) +
  256 * (base32 ^ 15)

def nextWindowWordB (w : Nat) : Nat :=
  add32
    (add32 (smallSigma1 (laneB w 14)) (laneB w 9))
    (add32 (smallSigma0 (laneB w 1)) (laneB w 0))

def advanceWindowB (w : Nat) : Nat :=
  w / base32 + nextWindowWordB w * (base32 ^ 15)

def initialMachineB (digest : Nat) : Nat :=
  pack8B iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h +
    initialWindowB digest * (base32 ^ 8)

def machineRoundB (st k : Nat) : Nat :=
  let a := laneB st 0
  let b := laneB st 1
  let c := laneB st 2
  let d := laneB st 3
  let e := laneB st 4
  let f := laneB st 5
  let g := laneB st 6
  let h := laneB st 7
  let w := st / (base32 ^ 8)
  let wt := laneB w 0
  let t1 := add32 h
    (add32 (bigSigma1 e) (add32 (ch e f g) (add32 k wt)))
  let t2 := add32 (bigSigma0 a) (maj a b c)
  let digest' := pack8B
    (add32 t1 t2) a b c (add32 d t1) e f g
  digest' + advanceWindowB w * (base32 ^ 8)

def roundsPackedKBase : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      roundsPackedKBase n (ks / base32) (machineRoundB st (ks % base32))

def feedForwardB (st : Nat) : Nat :=
  pack8B
    (add32 iv.a (laneB st 0))
    (add32 iv.b (laneB st 1))
    (add32 iv.c (laneB st 2))
    (add32 iv.d (laneB st 3))
    (add32 iv.e (laneB st 4))
    (add32 iv.f (laneB st 5))
    (add32 iv.g (laneB st 6))
    (add32 iv.h (laneB st 7))

def packedShaStepB (digest : Nat) : Nat :=
  feedForwardB (roundsPackedKBase 64 packedKBase (initialMachineB digest))

def iterPackedShaB : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedShaB n (packedShaStepB d)

def impl (n : Nat) : Nat :=
  let d0 := packDigestB (seedDigest (sha256Seed n))
  encodeDigest (unpackDigestB (iterPackedShaB (sha256Steps n) d0))

end Submission
'''

p=OUT/"Submission_machine_v12.lean"
p.write_text(text)
print(f"generated {{p}} bytes={{len(text.encode())}}")
