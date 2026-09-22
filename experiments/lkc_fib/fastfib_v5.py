#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
text=r'''import Spec
import Mathlib.Data.Nat.Fib.Basic

namespace Submission

/-- Reuse Mathlib's verified binary pair-state evaluator directly. -/
def impl (n : Nat) : Nat := Nat.fastFib n

theorem impl_correct : ∀ n, impl n = Nat.fib n := by
  intro n
  exact Nat.fast_fib_eq n

end Submission
'''
p=OUT/"Submission_v5_fastfib.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
