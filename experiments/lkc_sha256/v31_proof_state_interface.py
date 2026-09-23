#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

fields="\n".join([f"  w{i} : Nat" for i in range(16)] + [f"  {x} : Nat" for x in "abcdefgh"])
ctor=", ".join([f"w.x{i}" for i in range(16)] + [f"s.{x}" for x in "abcdefgh"])
args=" ".join([f"p.w{i}" for i in range(16)] + [f"p.{x}" for x in "abcdefgh"])

proof=f'''
/-! Proof-only state compression: measured V31 runtime is unchanged. -/

structure ProofState where
{fields}

def ProofState.ofWS (w : Window) (s : Digest) : ProofState :=
  ⟨{ctor}⟩

def ProofState.window (p : ProofState) : Window :=
  ⟨p.w0,p.w1,p.w2,p.w3,p.w4,p.w5,p.w6,p.w7,
   p.w8,p.w9,p.w10,p.w11,p.w12,p.w13,p.w14,p.w15⟩

def ProofState.digest (p : ProofState) : Digest :=
  ⟨p.a,p.b,p.c,p.d,p.e,p.f,p.g,p.h⟩

def ProofState.next (k : Nat) (p : ProofState) : ProofState :=
  let w := p.window
  let s := p.digest
  ProofState.ofWS (w.push w.nextFast) (roundFast s k w.x0)

def scalarPacked (ks : List Nat) (p : ProofState) : Digest :=
  roundsScalarMul ks {args}

def shadowPacked : List Nat → ProofState → Digest
  | [], p => p.digest
  | k :: ks, p => shadowPacked ks (p.next k)

theorem scalarPacked_nil (p : ProofState) :
    scalarPacked [] p = p.digest := by
  rcases p with ⟨{",".join([f"w{i}" for i in range(16)] + list("abcdefgh"))}⟩
  unfold scalarPacked ProofState.digest
  rw [roundsScalarMul]

theorem scalarPacked_cons (k : Nat) (ks : List Nat) (p : ProofState) :
    scalarPacked (k :: ks) p = scalarPacked ks (p.next k) := by
  rcases p with ⟨{",".join([f"w{i}" for i in range(16)] + list("abcdefgh"))}⟩
  unfold scalarPacked ProofState.next ProofState.window ProofState.digest ProofState.ofWS
  rw [roundsScalarMul]
  rfl

theorem shadowPacked_nil (p : ProofState) :
    shadowPacked [] p = p.digest := by rfl

theorem shadowPacked_cons (k : Nat) (ks : List Nat) (p : ProofState) :
    shadowPacked (k :: ks) p = shadowPacked ks (p.next k) := by rfl

theorem runners_equal_packed
    {{K P O : Type}}
    (next : K → P → P)
    (base : P → O)
    (F G : List K → P → O)
    (fNil : ∀ p, F [] p = base p)
    (fCons : ∀ k ks p, F (k :: ks) p = F ks (next k p))
    (gNil : ∀ p, G [] p = base p)
    (gCons : ∀ k ks p, G (k :: ks) p = G ks (next k p)) :
    ∀ ks p, F ks p = G ks p := by
  intro ks
  induction ks with
  | nil =>
      intro p
      exact (fNil p).trans (gNil p).symm
  | cons k ks ih =>
      intro p
      calc
        F (k :: ks) p = F ks (next k p) := fCons k ks p
        _ = G ks (next k p) := ih (next k p)
        _ = G (k :: ks) p := (gCons k ks p).symm

theorem scalarPacked_eq_shadowPacked :
    ∀ ks p, scalarPacked ks p = shadowPacked ks p :=
  runners_equal_packed ProofState.next ProofState.digest
    scalarPacked shadowPacked
    scalarPacked_nil scalarPacked_cons shadowPacked_nil shadowPacked_cons

theorem scalarPacked_ofWS (ks : List Nat) (w : Window) (s : Digest) :
    scalarPacked ks (ProofState.ofWS w s) =
      roundsScalarMul ks
        w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
        w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
        s.a s.b s.c s.d s.e s.f s.g s.h := by
  rfl

end Submission
'''
p=OUT/"V31ProofStateInterface.lean"
p.write_text(prefix+proof)
print(f"generated {{p}} bytes={{len((prefix+proof).encode())}}")
