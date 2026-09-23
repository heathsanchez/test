#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

def proofNextW (k : Nat) (w : Window) (s : Digest) : Window :=
  w.push w.nextFast

def proofNextS (k : Nat) (w : Window) (s : Digest) : Digest :=
  roundFast s k w.x0

def roundsShadow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, w, s =>
      roundsShadow ks (proofNextW k w s) (proofNextS k w s)

theorem scalar_nil_law (w : Window) (s : Digest) :
    roundsScalarMulW [] w s = s := by
  unfold roundsScalarMulW
  rw [roundsScalarMul]

theorem scalar_cons_law (k : Nat) (ks : List Nat) (w : Window) (s : Digest) :
    roundsScalarMulW (k :: ks) w s =
      roundsScalarMulW ks (proofNextW k w s) (proofNextS k w s) := by
  rcases w with ⟨w0,w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15⟩
  rcases s with ⟨a,b,c,d,e,f,g,h⟩
  unfold roundsScalarMulW proofNextW proofNextS
  rw [roundsScalarMul]
  rfl

theorem shadow_nil_law (w : Window) (s : Digest) :
    roundsShadow [] w s = s := by rfl

theorem shadow_cons_law (k : Nat) (ks : List Nat) (w : Window) (s : Digest) :
    roundsShadow (k :: ks) w s =
      roundsShadow ks (proofNextW k w s) (proofNextS k w s) := by rfl

/-- Pure structural theorem: no SHA operation occurs in this proof. -/
theorem runners_equal_of_same_laws
    {K W S : Type}
    (nextW : K → W → S → W)
    (nextS : K → W → S → S)
    (F G : List K → W → S → S)
    (fNil : ∀ w s, F [] w s = s)
    (fCons : ∀ k ks w s,
      F (k :: ks) w s = F ks (nextW k w s) (nextS k w s))
    (gNil : ∀ w s, G [] w s = s)
    (gCons : ∀ k ks w s,
      G (k :: ks) w s = G ks (nextW k w s) (nextS k w s)) :
    ∀ ks w s, F ks w s = G ks w s := by
  intro ks
  induction ks with
  | nil =>
      intro w s
      exact (fNil w s).trans (gNil w s).symm
  | cons k ks ih =>
      intro w s
      calc
        F (k :: ks) w s = F ks (nextW k w s) (nextS k w s) :=
          fCons k ks w s
        _ = G ks (nextW k w s) (nextS k w s) :=
          ih (nextW k w s) (nextS k w s)
        _ = G (k :: ks) w s :=
          (gCons k ks w s).symm

theorem scalar_eq_shadow :
    ∀ ks w s, roundsScalarMulW ks w s = roundsShadow ks w s :=
  runners_equal_of_same_laws
    proofNextW proofNextS roundsScalarMulW roundsShadow
    scalar_nil_law scalar_cons_law shadow_nil_law shadow_cons_law

end Submission
'''
p=OUT/"V31AbstractLawInduction.lean"
p.write_text(prefix+proof)
print(f"generated {p} bytes={len((prefix+proof).encode())}")
