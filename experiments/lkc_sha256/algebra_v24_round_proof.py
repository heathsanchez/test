#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_fullproof_v21.py"))
src=(OUT/"Submission_algebra_v21_proof.lean").read_text()

old_round='''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := (s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w) &&& w32
  let t2 := (bigSigma0Fast s.a + majFast s.a s.b s.c) &&& w32
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
'''
new_round='''def roundFast (s : Digest) (k w : Nat) : Digest :=
  let t1 := s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w
  let t2 := bigSigma0Fast s.a + majFast s.a s.b s.c
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩
'''
if old_round not in src:
    raise SystemExit("baseline roundFast block missing")
src=src.replace(old_round,new_round,1)

old_theorem='''theorem roundFast_eq_round (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    roundFast s k w = round s k w := by
  unfold roundFast round
  rw [bigSigma1Fast_eq s.e]
  rw [chFast_eq s.e s.f s.g hs.e hs.g]
  rw [bigSigma0Fast_eq s.a]
  rw [majFast_eq s.a s.b s.c]
  rw [mask5_eq_nested s.h (bigSigma1 s.e) (ch s.e s.f s.g) k w]
  rw [show (bigSigma0 s.a + maj s.a s.b s.c) &&& w32 =
      add32 (bigSigma0 s.a) (maj s.a s.b s.c) by rfl]
  rfl
'''

new_theorem='''theorem mask_add_reduced (a b : Nat) :
    (a + b) &&& w32 =
      ((a &&& w32) + (b &&& w32)) &&& w32 := by
  simp only [mask32_eq_mod]
  simp only [Nat.mod_add_mod, Nat.add_mod_mod]

theorem roundFast_eq_round (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    roundFast s k w = round s k w := by
  unfold roundFast round
  rw [bigSigma1Fast_eq s.e]
  rw [chFast_eq s.e s.f s.g hs.e hs.g]
  rw [bigSigma0Fast_eq s.a]
  rw [majFast_eq s.a s.b s.c]
  let raw1 :=
    s.h + bigSigma1 s.e + ch s.e s.f s.g + k + w
  let raw2 := bigSigma0 s.a + maj s.a s.b s.c
  have h1 : raw1 &&& w32 =
      add32 s.h
        (add32 (bigSigma1 s.e)
          (add32 (ch s.e s.f s.g) (add32 k w))) := by
    unfold raw1
    exact mask5_eq_nested s.h (bigSigma1 s.e) (ch s.e s.f s.g) k w
  have h2 : raw2 &&& w32 =
      add32 (bigSigma0 s.a) (maj s.a s.b s.c) := by
    unfold raw2
    rfl
  have ha :
      (raw1 + raw2) &&& w32 =
        add32
          (add32 s.h
            (add32 (bigSigma1 s.e)
              (add32 (ch s.e s.f s.g) (add32 k w))))
          (add32 (bigSigma0 s.a) (maj s.a s.b s.c)) := by
    rw [mask_add_reduced raw1 raw2, h1, h2]
    rfl
  have he :
      (s.d + raw1) &&& w32 =
        add32 s.d
          (add32 s.h
            (add32 (bigSigma1 s.e)
              (add32 (ch s.e s.f s.g) (add32 k w)))) := by
    rw [mask_add_reduced s.d raw1, h1]
    rw [and_mask32_eq_self s.d hs.d]
    rfl
  change
    Digest.mk ((raw1 + raw2) &&& w32) s.a s.b s.c
      ((s.d + raw1) &&& w32) s.e s.f s.g =
    Digest.mk
      (add32
        (add32 s.h
          (add32 (bigSigma1 s.e)
            (add32 (ch s.e s.f s.g) (add32 k w))))
        (add32 (bigSigma0 s.a) (maj s.a s.b s.c)))
      s.a s.b s.c
      (add32 s.d
        (add32 s.h
          (add32 (bigSigma1 s.e)
            (add32 (ch s.e s.f s.g) (add32 k w)))))
      s.e s.f s.g
  rw [ha, he]
'''
if old_theorem not in src:
    raise SystemExit("baseline round theorem missing")
src=src.replace(old_theorem,new_theorem,1)

p=OUT/"Submission_v24_round_proof.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
