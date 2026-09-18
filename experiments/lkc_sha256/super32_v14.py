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

HEADER = f'''import Spec

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

def pack16
    (x0 x1 x2 x3 x4 x5 x6 x7
     x8 x9 x10 x11 x12 x13 x14 x15 : Nat) : Nat :=
  x0 ||| (x1 <<< 32) ||| (x2 <<< 64) ||| (x3 <<< 96) |||
  (x4 <<< 128) ||| (x5 <<< 160) ||| (x6 <<< 192) ||| (x7 <<< 224) |||
  (x8 <<< 256) ||| (x9 <<< 288) ||| (x10 <<< 320) ||| (x11 <<< 352) |||
  (x12 <<< 384) ||| (x13 <<< 416) ||| (x14 <<< 448) ||| (x15 <<< 480)

def packedK : Nat := {hex(packed_k)}

def initialWindowBits (d : Nat) : Nat :=
  d ||| (0x80000000 <<< 256) ||| (256 <<< 480)

def initialMachine (digest : Nat) : Nat :=
  pack8 iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h |||
    (initialWindowBits digest <<< 256)

'''

def make_super(c: int) -> str:
    lines = [f"/-- Fuse {c} SHA rounds, unpacking and repacking the machine only once. -/",
             f"def super{c} (st ks : Nat) : Nat :="]
    for i,n in enumerate("abcdefgh"):
        lines.append(f"  let {n}0 := lane32 st {i}")
    for i in range(16):
        lines.append(f"  let w{i} := lane32 st {8+i}")
    for r in range(c):
        lines.append(f"  let k{r} := lane32 ks {r}")
        lines.append(
          f"  let nw{16+r} := add32 (add32 (smallSigma1 w{14+r}) w{9+r}) "
          f"(add32 (smallSigma0 w{1+r}) w{r})")
        lines.append(
          f"  let t1_{r} := add32 h{r} "
          f"(add32 (bigSigma1 e{r}) (add32 (ch e{r} f{r} g{r}) (add32 k{r} w{r})))")
        lines.append(f"  let t2_{r} := add32 (bigSigma0 a{r}) (maj a{r} b{r} c{r})")
        lines.append(f"  let a{r+1} := add32 t1_{r} t2_{r}")
        lines.append(f"  let b{r+1} := a{r}")
        lines.append(f"  let c{r+1} := b{r}")
        lines.append(f"  let d{r+1} := c{r}")
        lines.append(f"  let e{r+1} := add32 d{r} t1_{r}")
        lines.append(f"  let f{r+1} := e{r}")
        lines.append(f"  let g{r+1} := f{r}")
        lines.append(f"  let h{r+1} := g{r}")
        # alias generated schedule word to simple w-name used by later rounds/window packing
        lines.append(f"  let w{16+r} := nw{16+r}")
    digest = f"pack8 a{c} b{c} c{c} d{c} e{c} f{c} g{c} h{c}"
    ws = " ".join(f"w{i}" for i in range(c,c+16))
    lines.append(f"  let digest' := {digest}")
    lines.append(f"  let window' := pack16 {ws}")
    lines.append("  digest' ||| (window' <<< 256)")
    return "\n".join(lines) + "\n\n"

def tail(c: int) -> str:
    groups=64//c
    shift=32*c
    return f'''
def runGroups{c} : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      runGroups{c} n (ks >>> {shift}) (super{c} st ks)

def feedForward{c} (st : Nat) : Nat :=
  pack8
    (add32 iv.a (lane32 st 0))
    (add32 iv.b (lane32 st 1))
    (add32 iv.c (lane32 st 2))
    (add32 iv.d (lane32 st 3))
    (add32 iv.e (lane32 st 4))
    (add32 iv.f (lane32 st 5))
    (add32 iv.g (lane32 st 6))
    (add32 iv.h (lane32 st 7))

def packedShaStep{c} (digest : Nat) : Nat :=
  feedForward{c} (runGroups{c} {groups} packedK (initialMachine digest))

def iterPackedSha{c} : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedSha{c} n (packedShaStep{c} d)

def impl (n : Nat) : Nat :=
  let d0 := packDigestBits (seedDigest (sha256Seed n))
  encodeDigest (unpackDigestBits (iterPackedSha{c} (sha256Steps n) d0))

end Submission
'''

for c in (32,):
    text = HEADER + make_super(c) + tail(c)
    p=OUT/f"Submission_super{c}_v14.lean"
    p.write_text(text)
    print(f"generated {p} bytes={len(text.encode())}")
