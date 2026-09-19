#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_v20.py"))
src=(OUT/"Submission_algebra_v20.lean").read_text()

repls={
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
''',
'''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := (s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w) &&& w32
  let t2 := (bigSigma0Fast s.a + majFast s.a s.b s.c) &&& w32
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
''':
'''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w
  let t2 := bigSigma0Fast s.a + majFast s.a s.b s.c
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
'''
}
for old,new in repls.items():
    if old not in src:
        raise SystemExit("expected V23 algebra block missing")
    src=src.replace(old,new,1)

src=src.replace(
  "Raw rotate; callers combine several rotations and mask once at the end.",
  "Raw rotate; V24 defers all sigma masking to the consuming modular boundary.")
src=src.replace(
  "One final reduction mod 2^32 instead of three nested add32 masks.",
  "V24: sigma values stay raw; the schedule masks only after the whole sum.")
src=src.replace(
  "The round algebra only needs the final sums modulo 2^32.\nThis removes three intermediate masks from t1 on every round.",
  "V24: t1/t2 and sigma values remain unmasked; only the two state outputs are reduced modulo 2^32.")

p=OUT/"Submission_algebra_v24_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
