#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

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
0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]

def list_lit(xs):
    return "["+", ".join(hex(x) for x in xs)+"]"

wins=[f"w{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
fields="\n".join([f"  {x} : Nat" for x in wins+sts])
types=" → ".join(["Nat"]*24)

nil_sched=", ".join(["[]"]+["_"]*16+sts)
cons=", ".join(["k :: ks"]+wins+sts)
nextargs=" ".join(wins[1:]+["nw","na","a","b","c","ne","e","f","g"])
phase_ctor="⟨"+",".join(wins+sts)+"⟩"

tail_next=" ".join(wins[1:]+["0","na","a","b","c","ne","e","f","g"])

body=f'''
/-! V40: generate only the 48 schedule words that can still be consumed. -/

def K48V40 : List Nat := {list_lit(K[:48])}
def K16V40 : List Nat := {list_lit(K[48:])}

structure PhaseV40 where
{fields}

def roundsScheduleV40 : List Nat → {types} → PhaseV40
  | {nil_sched} => {phase_ctor}
  | {cons} =>
      let nw := (smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsScheduleV40 ks {nextargs}

def roundsTailV40 : List Nat → {types} → Digest
  | {nil_sched} => ⟨a,b,c,d,e,f,g,h⟩
  | {cons} =>
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsTailV40 ks {tail_next}

def fastStepV40 (d : Digest) : Digest :=
  let m := roundsScheduleV40 K48V40
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  let f := roundsTailV40 K16V40
    m.w0 m.w1 m.w2 m.w3 m.w4 m.w5 m.w6 m.w7
    m.w8 m.w9 m.w10 m.w11 m.w12 m.w13 m.w14 m.w15
    m.a m.b m.c m.d m.e m.f m.g m.h
  feedForwardIV f

def implV40 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepV40
    (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p=OUT/"Submission_no_waste_tail_v40_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
