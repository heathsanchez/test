#!/usr/bin/env python3
# scalar proof assembled from small recursion-equation lemmas
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
/-! V31 scalar-state bridge through certified recursion equations. -/

def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

theorem roundsScalarMulW_nil (w : Window) (s : Digest) :
    roundsScalarMulW [] w s = s := by
  unfold roundsScalarMulW
  rw [roundsScalarMul]

theorem roundsScalarMulW_cons (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsScalarMulW (k :: ks) w s =
      roundsScalarMulW ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rcases w with ⟨w0,w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15⟩
  rcases s with ⟨a,b,c,d,e,f,g,h⟩
  unfold roundsScalarMulW
  rw [roundsScalarMul]
  rfl

theorem roundsScalarMulW_eq_roundsFast :
    ∀ (ks : List Nat) (w : Window) (s : Digest),
      roundsScalarMulW ks w s = roundsFast ks w s
  | [], w, s => by
      rw [roundsScalarMulW_nil]
      rfl
  | k :: ks, w, s => by
      rw [roundsScalarMulW_cons]
      simp only [roundsFast]
      exact roundsScalarMulW_eq_roundsFast ks
        (w.push w.nextFast) (roundFast s k w.x0)

theorem fastStepV31_eq_fastStepAlgebra (d : Digest) :
    fastStepV31 d = fastStepAlgebra d := by
  unfold fastStepV31 fastStepAlgebra
  change
    feedForwardIV
      (roundsScalarMulW K (initialWindow d) iv) =
    feedForwardIV
      (roundsFast K (initialWindow d) iv)
  rw [roundsScalarMulW_eq_roundsFast]

end Submission
'''
p=OUT/"V31ScalarProofDev.lean"
p.write_text(prefix+proof)
print(f"generated {p} bytes={len((prefix+proof).encode())}")
