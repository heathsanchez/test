#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

theorem coefficientsFrom_length :
    ∀ count k index state,
      (coefficientsFrom count k index state).length = count
  | 0, _, _, _ => rfl
  | count + 1, k, index, state => by
      simp [coefficientsFrom, coefficientsFrom_length count]

theorem polyOf_length (n : Nat) : (polyOf n).length = 25 := by
  simp [polyOf, coefficientsFrom_length]

theorem discSpec_eq_resultant (n : Nat) :
    discSpec n = resultantFromPoly (polyOf n) := by
  unfold discSpec discriminantFromPoly
  simp [polyOf_length]

/-- Degree is fixed at 24, so (-1)^(24*23/2) = +1. -/
def impl (n : Nat) : Int := resultantFromPoly (polyOf n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  exact (discSpec_eq_resultant n).symm

end Submission
'''

path = OUT / "Submission_v1.lean"
path.write_text(text)
print(f"generated {path} bytes={len(text.encode())}")
