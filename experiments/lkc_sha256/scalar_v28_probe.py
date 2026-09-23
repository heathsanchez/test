#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
src=(OUT/"Submission_algebra_v24_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

wins=[f"w{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
args=", ".join(wins+sts)
types=" → ".join(["Nat"]*(16+8)+["Digest"])
nilpat=", ".join(["[]"]+wins+sts)
conspat=", ".join(["k :: ks"]+wins+sts)
nextargs=" ".join(wins[1:]+["nw","na","a","b","c","ne","e","f","g"])

body=f'''
/-! V28 diagnostic: preserve recursive sharing, eliminate per-round Window/Digest construction. -/
def roundsScalar : List Nat → {types}
  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩
  | {conspat} =>
      let nw := (smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsScalar ks {nextargs}

def fastStepScalar (d : Digest) : Digest :=
  let f := roundsScalar K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implScalar (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepScalar (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''
p=OUT/"Submission_scalar_v28_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
