#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

ks = [
"0x428a2f98","0x71374491","0xb5c0fbcf","0xe9b5dba5",
"0x3956c25b","0x59f111f1","0x923f82a4","0xab1c5ed5",
"0xd807aa98","0x12835b01","0x243185be","0x550c7dc3",
"0x72be5d74","0x80deb1fe","0x9bdc06a7","0xc19bf174",
"0xe49b69c1","0xefbe4786","0x0fc19dc6","0x240ca1cc",
"0x2de92c6f","0x4a7484aa","0x5cb0a9dc","0x76f988da",
"0x983e5152","0xa831c66d","0xb00327c8","0xbf597fc7",
"0xc6e00bf3","0xd5a79147","0x06ca6351","0x14292967",
"0x27b70a85","0x2e1b2138","0x4d2c6dfc","0x53380d13",
"0x650a7354","0x766a0abb","0x81c2c92e","0x92722c85",
"0xa2bfe8a1","0xa81a664b","0xc24b8b70","0xc76c51a3",
"0xd192e819","0xd6990624","0xf40e3585","0x106aa070",
"0x19a4c116","0x1e376c08","0x2748774c","0x34b0bcb5",
"0x391c0cb3","0x4ed8aa4a","0x5b9cca4f","0x682e6ff3",
"0x748f82ee","0x78a5636f","0x84c87814","0x8cc70208",
"0x90befffa","0xa4506ceb","0xbef9a3f7","0xc67178f2"
]
chunks=[ks[i:i+8] for i in range(0,64,8)]

def cons_list(xs, tail="tail"):
    s=tail
    for x in reversed(xs):
        s=f"{x} :: {s}"
    return s

base=r'''
/-! Fixed-K bridge in eight opaque eight-round certificates. -/

def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

theorem scalar_nil_chunk (w : Window) (s : Digest) :
    roundsScalarMulW [] w s = s := by
  unfold roundsScalarMulW
  rw [roundsScalarMul]

theorem scalar_cons_chunk (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsScalarMulW (k :: ks) w s =
      roundsScalarMulW ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rcases w with ⟨w0,w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15⟩
  rcases s with ⟨a,b,c,d,e,f,g,h⟩
  unfold roundsScalarMulW
  rw [roundsScalarMul]
  rfl

theorem fast_nil_chunk (w : Window) (s : Digest) :
    roundsFast [] w s = s := by
  rfl

theorem fast_cons_chunk (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsFast (k :: ks) w s =
      roundsFast ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rfl
'''

parts=[base]
for i,ch in enumerate(chunks):
    expr=cons_list(ch)
    parts.append(f'''
theorem bridge_chunk_{i} (tail : List Nat) (w : Window) (s : Digest)
    (h : ∀ w s, roundsScalarMulW tail w s = roundsFast tail w s) :
    roundsScalarMulW ({expr}) w s =
      roundsFast ({expr}) w s := by
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  rw [scalar_cons_chunk, fast_cons_chunk]
  exact h _ _
''')

full="["+", ".join(ks)+"]"
# Build suffix expressions from each chunk onward.
suffix=[]
for i in range(8):
    suffix.append("["+", ".join(sum(chunks[i:],[]))+"]")

final=r'''
theorem bridge_nil : ∀ w s,
    roundsScalarMulW [] w s = roundsFast [] w s := by
  intro w s
  exact (scalar_nil_chunk w s).trans (fast_nil_chunk w s).symm

'''
for i in range(7,-1,-1):
    tail_expr = "[]" if i==7 else suffix[i+1]
    hprev = "bridge_nil" if i==7 else f"bridge_suffix_{i+1}"
    final+=f'''
theorem bridge_suffix_{i} : ∀ w s,
    roundsScalarMulW {suffix[i]} w s = roundsFast {suffix[i]} w s := by
  intro w s
  change roundsScalarMulW ({cons_list(chunks[i], tail_expr)}) w s =
    roundsFast ({cons_list(chunks[i], tail_expr)}) w s
  exact bridge_chunk_{i} {tail_expr} w s {hprev}
'''

final+=f'''
theorem roundsScalarMulW_K_eq_chunked (w : Window) (s : Digest) :
    roundsScalarMulW K w s = roundsFast K w s := by
  change roundsScalarMulW {full} w s = roundsFast {full} w s
  exact bridge_suffix_0 w s

end Submission
'''
text=prefix+"".join(parts)+final
p=OUT/"V31ScalarFixedKChunked.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
