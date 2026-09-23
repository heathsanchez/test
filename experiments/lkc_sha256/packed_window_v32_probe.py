#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

body=r'''
/-!
V32 probe: preserve V31's mul-fused word algebra and scalar digest state,
but compress only the 16-word rolling message schedule into one Nat.
-/

def lane32Shift (x sh : Nat) : Nat :=
  (x >>> sh) &&& w32

def initialPackedWindow (d : Digest) : Nat :=
  d.a ||| (d.b <<< 32) ||| (d.c <<< 64) ||| (d.d <<< 96) |||
  (d.e <<< 128) ||| (d.f <<< 160) ||| (d.g <<< 192) ||| (d.h <<< 224) |||
  (0x80000000 <<< 256) ||| (256 <<< 480)

def roundsPackedWindow :
    List Nat → Nat →
    Nat → Nat → Nat → Nat → Nat → Nat → Nat → Nat → Digest
  | [], _, a,b,c,d,e,f,g,h => ⟨a,b,c,d,e,f,g,h⟩
  | k :: ks, win, a,b,c,d,e,f,g,h =>
      let w0 := win &&& w32
      let w1 := lane32Shift win 32
      let w9 := lane32Shift win 288
      let w14 := lane32Shift win 448
      let nw := (smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32
      let t1 := h + bigSigma1Fast e + chFast e f g + k + w0
      let t2 := bigSigma0Fast a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      let win' := (win >>> 32) ||| (nw <<< 480)
      roundsPackedWindow ks win' na a b c ne e f g

def fastStepV32 (d : Digest) : Digest :=
  let f := roundsPackedWindow K (initialPackedWindow d)
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implV32 (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepV32 (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''
p=OUT/"Submission_v32_packed_window_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
