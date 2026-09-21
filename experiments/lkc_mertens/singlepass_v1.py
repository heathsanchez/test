#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated" / "Submission_v1.lean"
OUT.parent.mkdir(parents=True, exist_ok=True)

text = r'''import Spec

namespace Submission

/-- Evaluate the Möbius sign from one prime-factor list traversal.
A duplicate factor witnesses non-squarefreeness; otherwise each distinct
factor flips the sign. -/
def moebiusList : List Nat → Int
  | [] => 1
  | a :: xs => if a ∈ xs then 0 else - moebiusList xs

theorem moebiusList_eq (xs : List Nat) :
    moebiusList xs = if xs.Nodup then (-1 : Int) ^ xs.length else 0 := by
  induction xs with
  | nil => simp [moebiusList]
  | cons a xs ih =>
      by_cases hmem : a ∈ xs
      · simp [moebiusList, hmem]
      · by_cases hnd : xs.Nodup
        · simp [moebiusList, hmem, hnd, ih, pow_succ]
        · simp [moebiusList, hmem, hnd, ih]

def moebiusSingle (n : Nat) : Int :=
  if n = 0 then 0 else moebiusList n.primeFactorsList

theorem moebiusSingle_eq (n : Nat) :
    moebiusSingle n = ArithmeticFunction.moebius n := by
  by_cases hn : n = 0
  · subst n
    simp [moebiusSingle]
  · simp [moebiusSingle, hn, moebiusList_eq,
      ArithmeticFunction.moebius, ArithmeticFunction.coe_mk,
      ← Nat.squarefree_iff_nodup_primeFactorsList hn,
      ArithmeticFunction.cardFactors_apply]

def impl (n : Nat) : Int :=
  ∑ k ∈ Finset.range (n + 1), moebiusSingle k

theorem impl_correct : ∀ n, impl n = mertensSpec n := by
  intro n
  simp only [impl, mertensSpec, moebiusSingle_eq]

end Submission
'''

OUT.write_text(text)
print(f"generated {OUT} bytes={len(text)}")
