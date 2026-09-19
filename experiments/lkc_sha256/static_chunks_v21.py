#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"aligned_wide_v19.py"))
src=(OUT/"Submission_aligned_wide_v19.lean").read_text()

K=[
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

start=src.index("def runWideAligned")
end=src.index("def ivWide")
prefix=src[:start]
suffix=src[end:]

chunks=[]
for c in range(8):
    lines=[
      f"/-- Static rounds {8*c}..{8*c+7}; no runtime K-list recursion. -/",
      f"def chunk{c} (m : Nat) : Nat :=",
      "  let s0 := m &&& mask8",
      "  let w0 := m >>> 512",
    ]
    for r in range(8):
        k=K[8*c+r]
        lines.append(f"  let s{r+1} := roundWideAligned s{r} w{r} 0x{k:08x}")
        lines.append(f"  let w{r+1} := roundWindowAligned w{r}")
    lines.append("  s8 ||| (w8 <<< 512)")
    chunks.append("\n".join(lines)+"\n")

text=prefix+"\n".join(chunks)+"\n"+suffix
old='''def packedShaStepWide (digest : Nat) : Nat :=
  let final := runWideAligned K ivWide (initialWindowWide digest)
  (final + ivWide) &&& mask8
'''
new='''def packedShaStepWide (digest : Nat) : Nat :=
  let m0 := ivWide ||| (initialWindowWide digest <<< 512)
  let m1 := chunk0 m0
  let m2 := chunk1 m1
  let m3 := chunk2 m2
  let m4 := chunk3 m3
  let m5 := chunk4 m4
  let m6 := chunk5 m5
  let m7 := chunk6 m6
  let m8 := chunk7 m7
  let final := m8 &&& mask8
  (final + ivWide) &&& mask8
'''
if old not in text:
    raise RuntimeError("packedShaStepWide marker not found")
text=text.replace(old,new)

p=OUT/"Submission_static_chunks_v21.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
