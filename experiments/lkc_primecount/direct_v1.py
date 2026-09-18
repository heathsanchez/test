#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

def isPrime (p : Nat) : Bool := decide (2 ≤ p) && (Nat.minFac p == p)

theorem isPrime_eq (p : Nat) : isPrime p = decide (Nat.Prime p) := by
  apply Bool.eq_iff_iff.mpr
  simp [isPrime, Nat.prime_def_minFac]

/-- Count incrementally instead of materializing [0, ..., n] and traversing it. -/
def countDirect : Nat → Nat
  | 0 => 0
  | n + 1 => countDirect n + if isPrime (n + 1) then 1 else 0

theorem primeCounting_succ_step (n : Nat) :
    Nat.primeCounting (n + 1) =
      Nat.primeCounting n + if Nat.Prime (n + 1) then 1 else 0 := by
  rw [← Nat.primesLE_card_eq_primeCounting (n + 1),
      ← Nat.primesLE_card_eq_primeCounting n,
      Nat.primesLE_succ]
  by_cases hp : Nat.Prime (n + 1)
  · simp [hp, Nat.notMem_primesLE]
  · simp [hp]

theorem countDirect_eq (n : Nat) : countDirect n = Nat.primeCounting n := by
  induction n with
  | zero =>
      simp [countDirect]
  | succ n ih =>
      rw [countDirect, ih, primeCounting_succ_step]
      simp [isPrime_eq]

def impl (n : Nat) : Nat := countDirect n

theorem impl_correct : ∀ n, impl n = primeCountSpec n := by
  intro n
  exact countDirect_eq n

end Submission
'''

path = OUT / "Submission_v1.lean"
path.write_text(text)
print(f"generated {path} bytes={len(text.encode())}")
