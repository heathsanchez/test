#!/usr/bin/env python3
# proof-only wrapper keeps elaboration small; runtime remains exact V31 scalar code
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
/-! V31 scalar-state bridge via proof-only structured wrappers. -/

def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

theorem roundsScalarMulW_eq_roundsFast :
    ∀ (ks : List Nat) (w : Window) (s : Digest),
      roundsScalarMulW ks w s = roundsFast ks w s
  | [], w, s => by
      cases w
      cases s
      rfl
  | k :: ks, w, s => by
      cases w with
      | mk w0 w1 w2 w3 w4 w5 w6 w7 w8 w9 w10 w11 w12 w13 w14 w15 =>
        cases s with
        | mk a b c d e f g h =>
          simp only [roundsScalarMulW, roundsScalarMul, roundsFast]
          dsimp only [Window.nextFast, Window.push, roundFast]
          exact roundsScalarMulW_eq_roundsFast ks
            ⟨w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15,
              (smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32⟩
            ⟨(h + bigSigma1Fast e + chFast e f g + k + w0 +
                (bigSigma0Fast a + majFast a b c)) &&& w32,
              a,b,c,
              (d + (h + bigSigma1Fast e + chFast e f g + k + w0)) &&& w32,
              e,f,g⟩

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
