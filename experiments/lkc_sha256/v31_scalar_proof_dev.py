#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

ws=[f"w{i}" for i in range(16)]
ss=["a","b","c","d","e","f","g","h"]
binders=" ".join([f"({x} : Nat)" for x in ws+ss])
args=" ".join(ws+ss)
win="⟨"+", ".join(ws)+"⟩"
dig="⟨"+", ".join(ss)+"⟩"

proof=f'''
/-! V31 scalar-state interaction bridge. -/

theorem roundsScalarMul_eq_roundsFast :
    ∀ (ks : List Nat) {binders},
      roundsScalarMul ks {args} =
        roundsFast ks {win} {dig}
  | [], {", ".join(ws+ss)} => rfl
  | k :: ks, {", ".join(ws+ss)} => by
      simp only [roundsScalarMul, roundsFast]
      dsimp only [Window.nextFast, Window.push, roundFast]
      exact roundsScalarMul_eq_roundsFast ks
        {" ".join(ws[1:])}
        ((smallSigma1Fast w14 + w9 + smallSigma0Fast w1 + w0) &&& w32)
        ((h + bigSigma1Fast e + chFast e f g + k + w0 +
            (bigSigma0Fast a + majFast a b c)) &&& w32)
        a b c
        ((d + (h + bigSigma1Fast e + chFast e f g + k + w0)) &&& w32)
        e f g

theorem fastStepV31_eq_fastStepAlgebra (d : Digest) :
    fastStepV31 d = fastStepAlgebra d := by
  unfold fastStepV31 fastStepAlgebra initialWindow
  rw [roundsScalarMul_eq_roundsFast]

end Submission
'''
text=prefix+proof
p=OUT/"V31ScalarProofDev.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
