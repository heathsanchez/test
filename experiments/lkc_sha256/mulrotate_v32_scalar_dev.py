#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
_old_nil="| [], " + ", ".join([f"w{i}" for i in range(16)] + ["a","b","c","d","e","f","g","h"]) + " =>"
_new_nil="| [], " + ", ".join(["_"]*16 + ["a","b","c","d","e","f","g","h"]) + " =>"
src=src.replace(_old_nil,_new_nil,1)
prefix=src.rsplit("\nend Submission",1)[0]

wins=[f"w{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
all_names=wins+sts
binders=" ".join(f"({x} : Nat)" for x in all_names)
args=" ".join(all_names)
win_ctor="⟨"+",".join(wins)+"⟩"
st_ctor="⟨"+",".join(sts)+"⟩"
nextargs=" ".join(wins[1:]+["nw","na","a","b","c","ne","e","f","g"])
intro_names=" ".join(all_names)
proof=f'''
theorem roundsScalarMul_eq_roundsFast_dev :
    ∀ (ks : List Nat) {binders},
      roundsScalarMul ks {args} =
        roundsFast ks {win_ctor} {st_ctor} := by
  intro ks
  induction ks with
  | nil =>
      intro {intro_names}
      rfl
  | cons k ks ih =>
      intro {intro_names}
      simp only [roundsScalarMul, roundsFast]
      simp [Window.nextFast, Window.push, roundFast, ih]

end Submission
'''
p=OUT/"ScalarDev.lean"; p.write_text(prefix+"\n"+proof)
print(f"generated {p} bytes={len(p.read_bytes())}")
