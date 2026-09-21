#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def fdBit : Nat → Nat → Nat × Nat
  | 0, _ => (0, 1)
  | _ + 1, 0 => (0, 1)
  | fuel + 1, n + 1 =>
    match fdBit fuel ((n + 1) >>> 1) with
    | (a, b) =>
      if ((n + 1) &&& 1) = 0 then
        (a * (2 * b - a), b * b + a * a)
      else
        (b * b + a * a, a * (2 * b - a) + (b * b + a * a))

theorem half_eq (n : Nat) : n >>> 1 = n / 2 := by
  simp [Nat.shiftRight_eq_div_pow]

theorem parity_eq (n : Nat) : n &&& 1 = n % 2 := by
  simp

theorem fib_odd (m : Nat) :
    Nat.fib (2 * m + 1) =
      Nat.fib (m + 1) * Nat.fib (m + 1) + Nat.fib m * Nat.fib m := by
  simpa only [pow_two] using Nat.fib_two_mul_add_one m

theorem fib_even (m : Nat) :
    Nat.fib (2 * m) = Nat.fib m * (2 * Nat.fib (m + 1) - Nat.fib m) :=
  Nat.fib_two_mul m

theorem fdBit_spec : (fuel n : Nat) → n ≤ fuel →
    fdBit fuel n = (Nat.fib n, Nat.fib (n + 1))
  | 0, 0, _ => rfl
  | _ + 1, 0, _ => rfl
  | fuel + 1, n + 1, h => by
    have hdiv : (n + 1) / 2 ≤ fuel := by omega
    have ih := fdBit_spec fuel ((n + 1) / 2) hdiv
    simp only [fdBit, half_eq, ih]
    rw [parity_eq]
    by_cases hpar : (n + 1) % 2 = 0
    · rw [if_pos hpar]
      show _ = (Nat.fib (n + 1), Nat.fib (n + 2))
      have e1 : 2 * ((n + 1) / 2) = n + 1 := by omega
      have e2 : 2 * ((n + 1) / 2) + 1 = n + 2 := by omega
      have he := fib_even ((n + 1) / 2)
      have ho := fib_odd ((n + 1) / 2)
      rw [e1] at he
      rw [e2] at ho
      rw [he, ho]
    · rw [if_neg hpar]
      show _ = (Nat.fib (n + 1), Nat.fib (n + 2))
      have e1 : 2 * ((n + 1) / 2) + 1 = n + 1 := by omega
      have e2 : 2 * ((n + 1) / 2) + 2 = n + 2 := by omega
      have he := fib_even ((n + 1) / 2)
      have ho := fib_odd ((n + 1) / 2)
      have ho1 := ho
      rw [e1] at ho1
      have hsum :
          Nat.fib (2 * ((n + 1) / 2) + 2) =
            Nat.fib (2 * ((n + 1) / 2)) +
              Nat.fib (2 * ((n + 1) / 2) + 1) :=
        Nat.fib_add_two
      rw [e2] at hsum
      rw [hsum, he, ho, ho1]

def impl (n : Nat) : Nat := (fdBit n n).1

theorem impl_correct : ∀ n, impl n = Nat.fib n := by
  intro n
  show (fdBit n n).1 = Nat.fib n
  rw [fdBit_spec n n (Nat.le_refl _)]

end Submission
'''
p=OUT/"Submission_v2.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
