#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

ks=[
"0x428a2f98","0x71374491","0xb5c0fbcf","0xe9b5dba5","0x3956c25b","0x59f111f1","0x923f82a4","0xab1c5ed5",
"0xd807aa98","0x12835b01","0x243185be","0x550c7dc3","0x72be5d74","0x80deb1fe","0x9bdc06a7","0xc19bf174",
"0xe49b69c1","0xefbe4786","0x0fc19dc6","0x240ca1cc","0x2de92c6f","0x4a7484aa","0x5cb0a9dc","0x76f988da",
"0x983e5152","0xa831c66d","0xb00327c8","0xbf597fc7","0xc6e00bf3","0xd5a79147","0x06ca6351","0x14292967",
"0x27b70a85","0x2e1b2138","0x4d2c6dfc","0x53380d13","0x650a7354","0x766a0abb","0x81c2c92e","0x92722c85",
"0xa2bfe8a1","0xa81a664b","0xc24b8b70","0xc76c51a3","0xd192e819","0xd6990624","0xf40e3585","0x106aa070",
"0x19a4c116","0x1e376c08","0x2748774c","0x34b0bcb5","0x391c0cb3","0x4ed8aa4","0x5b9cca4f","0x682e6ff3",
"0x748f82ee","0x78a5636f","0x84c87814","0x8cc70208","0x90befffa","0xa4506ceb","0xbef9a3f7","0xc67178f2"
]
chunks=[ks[i:i+8] for i in range(0,64,8)]

def cons(xs, tail):
    s=tail
    for x in reversed(xs): s=f"{x} :: {s}"
    return s

base=r'''
/-! Function-level V31 certificate: state expressions never enter the lineage term. -/

def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

def ScalarRunner (ks : List Nat) : Window → Digest → Digest :=
  fun w s => roundsScalarMulW ks w s

def FastRunner (ks : List Nat) : Window → Digest → Digest :=
  fun w s => roundsFast ks w s

theorem scalar_step_fun (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsScalarMulW (k :: ks) w s =
      roundsScalarMulW ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rcases w with ⟨w0,w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15⟩
  rcases s with ⟨a,b,c,d,e,f,g,h⟩
  unfold roundsScalarMulW
  rw [roundsScalarMul]
  rfl

theorem fast_step_fun (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsFast (k :: ks) w s =
      roundsFast ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rw [roundsFast]

theorem runner_nil : ScalarRunner [] = FastRunner [] := by
  funext w s
  unfold ScalarRunner FastRunner roundsScalarMulW
  rw [roundsScalarMul, roundsFast]

theorem runner_cons (k : Nat) (ks : List Nat)
    (h : ScalarRunner ks = FastRunner ks) :
    ScalarRunner (k :: ks) = FastRunner (k :: ks) := by
  funext w s
  unfold ScalarRunner FastRunner
  calc
    roundsScalarMulW (k :: ks) w s =
        roundsScalarMulW ks (w.push w.nextFast) (roundFast s k w.x0) :=
      scalar_step_fun k ks w s
    _ = roundsFast ks (w.push w.nextFast) (roundFast s k w.x0) := by
      exact congrFun (congrFun h (w.push w.nextFast)) (roundFast s k w.x0)
    _ = roundsFast (k :: ks) w s := (fast_step_fun k ks w s).symm

'''
parts=[base]
# Each chunk lifts a tail equality across eight fixed constants.
for i,ch in enumerate(chunks):
    tail="tail"
    expr=cons(ch,tail)
    nested="h"
    # runner_cons must be applied from last constant backward.
    suffix=tail
    for k in reversed(ch):
        nested=f"runner_cons {k} ({suffix}) ({nested})"
        suffix=f"{k} :: {suffix}"
    parts.append(f'''
theorem runner_chunk_{i} (tail : List Nat)
    (h : ScalarRunner tail = FastRunner tail) :
    ScalarRunner ({expr}) = FastRunner ({expr}) := by
  exact {nested}
''')

# Compose chunks backwards; tails remain named lists, no state terms.
suffix_expr="[]"
hname="runner_nil"
defs=[]
for i in range(7,-1,-1):
    expr=cons(chunks[i],suffix_expr)
    name=f"runner_suffix_{i}"
    defs.append(f'''
theorem {name} :
    ScalarRunner ({expr}) = FastRunner ({expr}) := by
  exact runner_chunk_{i} {suffix_expr} {hname}
''')
    suffix_expr=expr
    hname=name

full="["+", ".join(ks)+"]"
defs.append(f'''
theorem runner_K : ScalarRunner K = FastRunner K := by
  change ScalarRunner {full} = FastRunner {full}
  exact runner_suffix_0

theorem roundsScalarMulW_K_eq_fun (w : Window) (s : Digest) :
    roundsScalarMulW K w s = roundsFast K w s := by
  exact congrFun (congrFun runner_K w) s

end Submission
''')
text=prefix+"".join(parts)+"".join(defs)
p=OUT/"V31ScalarFunctionCertificate.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
