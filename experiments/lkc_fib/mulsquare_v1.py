#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

/-- Mathlib's fast-doubling binary recursion with x*x in place of x^2.
This changes only reduction shape, not the underlying algorithm. -/
def fastFibMulAux : Nat → Nat × Nat :=
  Nat.binaryRec (Nat.fib 0, Nat.fib 1) fun b _ p =>
    if b then
      (p.2 * p.2 + p.1 * p.1, p.2 * (2 * p.1 + p.2))
    else
      (p.1 * (2 * p.2 - p.1), p.2 * p.2 + p.1 * p.1)

theorem fastFibMulAux_bit_false (n : Nat) :
    fastFibMulAux (Nat.bit false n) =
      let p := fastFibMulAux n
      (p.1 * (2 * p.2 - p.1), p.2 * p.2 + p.1 * p.1) := by
  rw [fastFibMulAux, Nat.binaryRec_eq]
  · rfl
  · simp

theorem fastFibMulAux_bit_true (n : Nat) :
    fastFibMulAux (Nat.bit true n) =
      let p := fastFibMulAux n
      (p.2 * p.2 + p.1 * p.1, p.2 * (2 * p.1 + p.2)) := by
  rw [fastFibMulAux, Nat.binaryRec_eq]
  · rfl
  · simp

theorem fastFibMulAux_eq (n : Nat) :
    fastFibMulAux n = (Nat.fib n, Nat.fib (n + 1)) := by
  refine Nat.binaryRec ?_ ?_ n
  · simp [fastFibMulAux]
  · rintro (_ | _) n' ih <;>
      simp only [fastFibMulAux_bit_false, fastFibMulAux_bit_true,
        congr_arg Prod.fst ih, congr_arg Prod.snd ih, Prod.mk_inj] <;>
      simp [Nat.bit, Nat.fib_two_mul, Nat.fib_two_mul_add_one,
        Nat.fib_two_mul_add_two, pow_two]

def impl (n : Nat) : Nat := (fastFibMulAux n).1

theorem impl_correct : ∀ n, impl n = Nat.fib n := by
  intro n
  show (fastFibMulAux n).1 = Nat.fib n
  rw [fastFibMulAux_eq n]

end Submission
'''

path = OUT / "Submission_v1.lean"
path.write_text(text)
print(f"generated {path} bytes={len(text.encode())}")
