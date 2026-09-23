#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
src=(OUT/"Submission_algebra_v24_probe.lean").read_text()
prefix=src.split("def impl (n : Nat) : Nat :=",1)[0]

K=[
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]

L=[
"/-- V26 runtime-only straight-line transition. -/",
"def straightStep (d : Digest) : Digest :=",
"  let w0 := d.a","  let w1 := d.b","  let w2 := d.c","  let w3 := d.d",
"  let w4 := d.e","  let w5 := d.f","  let w6 := d.g","  let w7 := d.h",
"  let w8 : Nat := 0x80000000","  let w9 : Nat := 0","  let w10 : Nat := 0",
"  let w11 : Nat := 0","  let w12 : Nat := 0","  let w13 : Nat := 0",
"  let w14 : Nat := 0","  let w15 : Nat := 256"]
for t in range(16,64):
    L.append(f"  let w{t} := (smallSigma1Fast w{t-2} + w{t-7} + smallSigma0Fast w{t-15} + w{t-16}) &&& w32")
L += ["  let a0 := iv.a","  let b0 := iv.b","  let c0 := iv.c","  let d0 := iv.d",
      "  let e0 := iv.e","  let f0 := iv.f","  let g0 := iv.g","  let h0 := iv.h"]
for r,k in enumerate(K):
    L += [
      f"  let t1_{r} := h{r} + bigSigma1Fast e{r} + chFast e{r} f{r} g{r} + 0x{k:08x} + w{r}",
      f"  let t2_{r} := bigSigma0Fast a{r} + majFast a{r} b{r} c{r}",
      f"  let a{r+1} := (t1_{r} + t2_{r}) &&& w32",
      f"  let b{r+1} := a{r}", f"  let c{r+1} := b{r}", f"  let d{r+1} := c{r}",
      f"  let e{r+1} := (d{r} + t1_{r}) &&& w32",
      f"  let f{r+1} := e{r}", f"  let g{r+1} := f{r}", f"  let h{r+1} := g{r}"]
L += ["  feedForwardIV ⟨a64,b64,c64,d64,e64,f64,g64,h64⟩","",
      "def impl (n : Nat) : Nat :=",
      "  encodeDigest (iterDigest straightStep (sha256Steps n) (seedDigest (sha256Seed n)))",
      "", "/-- DIAGNOSTIC ONLY: timing stub; not a qualifying submission. -/",
      "axiom impl_correct : ∀ n, impl n = sha256Spec n",
      "", "end Submission",""]
text=prefix+"\n".join(L)
p=OUT/"Submission_straight_v26_probe.lean"; p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
