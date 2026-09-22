#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_v20.py"))
base=(OUT/"Submission_algebra_v20.lean").read_text()

sigma_repls={
'''def smallSigma0Fast (x : Nat) : Nat :=
  (rotrRaw x 7 ^^^ rotrRaw x 18 ^^^ (x >>> 3)) &&& w32
''':
'''def smallSigma0Fast (x : Nat) : Nat :=
  rotrRaw x 7 ^^^ rotrRaw x 18 ^^^ (x >>> 3)
''',
'''def smallSigma1Fast (x : Nat) : Nat :=
  (rotrRaw x 17 ^^^ rotrRaw x 19 ^^^ (x >>> 10)) &&& w32
''':
'''def smallSigma1Fast (x : Nat) : Nat :=
  rotrRaw x 17 ^^^ rotrRaw x 19 ^^^ (x >>> 10)
''',
'''def bigSigma0Fast (x : Nat) : Nat :=
  (rotrRaw x 2 ^^^ rotrRaw x 13 ^^^ rotrRaw x 22) &&& w32
''':
'''def bigSigma0Fast (x : Nat) : Nat :=
  rotrRaw x 2 ^^^ rotrRaw x 13 ^^^ rotrRaw x 22
''',
'''def bigSigma1Fast (x : Nat) : Nat :=
  (rotrRaw x 6 ^^^ rotrRaw x 11 ^^^ rotrRaw x 25) &&& w32
''':
'''def bigSigma1Fast (x : Nat) : Nat :=
  rotrRaw x 6 ^^^ rotrRaw x 11 ^^^ rotrRaw x 25
'''
}

round_old='''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := (s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w) &&& w32
  let t2 := (bigSigma0Fast s.a + majFast s.a s.b s.c) &&& w32
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
'''
round_new='''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w
  let t2 := bigSigma0Fast s.a + majFast s.a s.b s.c
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
'''

def apply_sigma(src):
    for old,new in sigma_repls.items():
        if old not in src: raise SystemExit("sigma block missing")
        src=src.replace(old,new,1)
    return src

if round_old not in base:
    raise SystemExit("round block missing")

round_only=base.replace(round_old,round_new,1)
sigma_only=apply_sigma(base)
combined=apply_sigma(base).replace(round_old,round_new,1)

for name,src in [
    ("Submission_v24_round_only.lean",round_only),
    ("Submission_v24_sigma_only.lean",sigma_only),
    ("Submission_v24_combined.lean",combined),
]:
    p=OUT/name
    p.write_text(src)
    print(f"generated {p} bytes={len(src.encode())}")
