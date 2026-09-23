#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

wins=[f"w{i}" for i in range(16)]
zins=[f"z{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
params=wins+zins+sts
types=" → ".join(["Nat"]*40+["Digest"])
nilpat=", ".join(["[]"]+params)
conspat=", ".join(["k :: ks"]+params)

next_w=wins[1:]+["nw"]
next_z=zins[1:]+["znw"]
next_s=["na","a","b","c","ne","e","f","g"]
nextargs=" ".join(next_w+next_z+next_s)

dup_const=lambda x: x*4294967297
fixed_words=[0x80000000,0,0,0,0,0,0,256]
fixed_dups=[dup_const(x) for x in fixed_words]

body=f'''
/-! V33 probe: cache dup32 for the 16-word schedule window. -/

def smallSigma0Dup (x z : Nat) : Nat :=
  (z >>> 7) ^^^ (z >>> 18) ^^^ (x >>> 3)

def smallSigma1Dup (x z : Nat) : Nat :=
  (z >>> 17) ^^^ (z >>> 19) ^^^ (x >>> 10)

def roundsDupWindow : List Nat → {types}
  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩
  | {conspat} =>
      let nw := (smallSigma1Dup w14 z14 + w9 + smallSigma0Dup w1 z1 + w0) &&& w32
      let znw := dup32 nw
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsDupWindow ks {nextargs}

def fastStepV33 (d : Digest) : Digest :=
  let f := roundsDupWindow K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    (dup32 d.a) (dup32 d.b) (dup32 d.c) (dup32 d.d)
    (dup32 d.e) (dup32 d.f) (dup32 d.g) (dup32 d.h)
    {fixed_dups[0]} {fixed_dups[1]} {fixed_dups[2]} {fixed_dups[3]}
    {fixed_dups[4]} {fixed_dups[5]} {fixed_dups[6]} {fixed_dups[7]}
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implV33 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepV33 (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p=OUT/"Submission_dupwindow_v33_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
