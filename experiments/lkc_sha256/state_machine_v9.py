#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

/--
The minimum runtime state for one SHA-256 block:
a 16-word rolling message window plus the eight working words.
No 64-word schedule and no generated straight-line body.
-/
structure Window where
  x0 : Nat
  x1 : Nat
  x2 : Nat
  x3 : Nat
  x4 : Nat
  x5 : Nat
  x6 : Nat
  x7 : Nat
  x8 : Nat
  x9 : Nat
  x10 : Nat
  x11 : Nat
  x12 : Nat
  x13 : Nat
  x14 : Nat
  x15 : Nat

def Window.nextWord (w : Window) : Nat :=
  add32 (add32 (smallSigma1 w.x14) w.x9)
    (add32 (smallSigma0 w.x1) w.x0)

def Window.advance (w : Window) : Window :=
  ⟨w.x1, w.x2, w.x3, w.x4, w.x5, w.x6, w.x7, w.x8,
   w.x9, w.x10, w.x11, w.x12, w.x13, w.x14, w.x15, w.nextWord⟩

def initialWindow (d : Digest) : Window :=
  ⟨d.a, d.b, d.c, d.d, d.e, d.f, d.g, d.h,
   0x80000000, 0, 0, 0, 0, 0, 0, 256⟩

/--
Consume the fixed round-constant list while carrying only the current window.
At round t, x0 is W[t]; advance shifts and computes W[t+16].
-/
def roundsWindow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, w, s =>
      roundsWindow ks w.advance (round s k w.x0)

def fastStepWindow (d : Digest) : Digest :=
  let f := roundsWindow K (initialWindow d) iv
  ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
   add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩

def impl (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepWindow (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p = OUT / "Submission_state_v9.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
