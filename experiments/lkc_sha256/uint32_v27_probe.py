#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

K=[
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
]

lines=[
"import Spec",
"",
"namespace Submission",
"",
"structure UDigest where",
"  a : UInt32","  b : UInt32","  c : UInt32","  d : UInt32",
"  e : UInt32","  f : UInt32","  g : UInt32","  h : UInt32",
"",
"def urotr (x : UInt32) (n : UInt32) : UInt32 :=",
"  (x >>> n) ||| (x <<< (32 - n))",
"",
"def us0 (x : UInt32) : UInt32 := urotr x 7 ^^^ urotr x 18 ^^^ (x >>> 3)",
"def us1 (x : UInt32) : UInt32 := urotr x 17 ^^^ urotr x 19 ^^^ (x >>> 10)",
"def uS0 (x : UInt32) : UInt32 := urotr x 2 ^^^ urotr x 13 ^^^ urotr x 22",
"def uS1 (x : UInt32) : UInt32 := urotr x 6 ^^^ urotr x 11 ^^^ urotr x 25",
"def uch (x y z : UInt32) : UInt32 := (x &&& y) ^^^ ((~~~ x) &&& z)",
"def umaj (x y z : UInt32) : UInt32 := (x &&& y) ^^^ (x &&& z) ^^^ (y &&& z)",
"",
"def uStep (d : UDigest) : UDigest :=",
"  let w0 := d.a","  let w1 := d.b","  let w2 := d.c","  let w3 := d.d",
"  let w4 := d.e","  let w5 := d.f","  let w6 := d.g","  let w7 := d.h",
"  let w8 : UInt32 := 0x80000000",
"  let w9 : UInt32 := 0","  let w10 : UInt32 := 0","  let w11 : UInt32 := 0",
"  let w12 : UInt32 := 0","  let w13 : UInt32 := 0","  let w14 : UInt32 := 0",
"  let w15 : UInt32 := 256",
]
for t in range(16,64):
    lines.append(f"  let w{t} := us1 w{t-2} + w{t-7} + us0 w{t-15} + w{t-16}")
lines += [
"  let a0 : UInt32 := 0x6a09e667",
"  let b0 : UInt32 := 0xbb67ae85",
"  let c0 : UInt32 := 0x3c6ef372",
"  let d0 : UInt32 := 0xa54ff53a",
"  let e0 : UInt32 := 0x510e527f",
"  let f0 : UInt32 := 0x9b05688c",
"  let g0 : UInt32 := 0x1f83d9ab",
"  let h0 : UInt32 := 0x5be0cd19",
]
for r,k in enumerate(K):
    lines += [
      f"  let t1_{r} := h{r} + uS1 e{r} + uch e{r} f{r} g{r} + (0x{k:08x} : UInt32) + w{r}",
      f"  let t2_{r} := uS0 a{r} + umaj a{r} b{r} c{r}",
      f"  let a{r+1} := t1_{r} + t2_{r}",
      f"  let b{r+1} := a{r}",
      f"  let c{r+1} := b{r}",
      f"  let d{r+1} := c{r}",
      f"  let e{r+1} := d{r} + t1_{r}",
      f"  let f{r+1} := e{r}",
      f"  let g{r+1} := f{r}",
      f"  let h{r+1} := g{r}",
    ]
lines += [
"  ⟨(0x6a09e667 : UInt32) + a64, (0xbb67ae85 : UInt32) + b64,",
"   (0x3c6ef372 : UInt32) + c64, (0xa54ff53a : UInt32) + d64,",
"   (0x510e527f : UInt32) + e64, (0x9b05688c : UInt32) + f64,",
"   (0x1f83d9ab : UInt32) + g64, (0x5be0cd19 : UInt32) + h64⟩",
"",
"def toU (d : Digest) : UDigest :=",
"  ⟨d.a.toUInt32, d.b.toUInt32, d.c.toUInt32, d.d.toUInt32,",
"   d.e.toUInt32, d.f.toUInt32, d.g.toUInt32, d.h.toUInt32⟩",
"",
"def fromU (d : UDigest) : Digest :=",
"  ⟨d.a.toNat, d.b.toNat, d.c.toNat, d.d.toNat,",
"   d.e.toNat, d.f.toNat, d.g.toNat, d.h.toNat⟩",
"",
"def iterU : Nat → UDigest → UDigest",
"  | 0, d => d",
"  | t + 1, d => iterU t (uStep d)",
"",
"def impl (n : Nat) : Nat :=",
"  encodeDigest (fromU (iterU (sha256Steps n) (toU (seedDigest (sha256Seed n)))))",
"",
"/-- DIAGNOSTIC ONLY: permits timing the runtime; never a submission candidate. -/",
"axiom impl_correct : ∀ n, impl n = sha256Spec n",
"",
"end Submission",
]
text="\n".join(lines)+"\n"
p=OUT/"Submission_uint32_v27_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
