#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

# Preserve exact V1 baseline bytes for paired comparison.
runpy.run_path(str(ROOT / "direct_v1.py"))

text = r'''import Spec

namespace Submission

/-- Proof-facing primality predicate used only to bridge to Mathlib. -/
def isPrimeRef (p : Nat) : Bool :=
  decide (2 ≤ p) && (List.range p).all (fun d => decide (d < 2) || p % d != 0)

theorem isPrimeRef_iff (p : Nat) : isPrimeRef p = true ↔ Nat.Prime p := by
  rw [Nat.prime_def_lt']
  simp only [isPrimeRef, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true,
    List.mem_range, Bool.or_eq_true, bne_iff_ne]
  constructor
  · rintro ⟨hp, h⟩
    refine ⟨hp, ?_⟩
    intro m hm hmp hd
    rcases h m hmp with hsmall | hmod
    · omega
    · exact hmod (Nat.mod_eq_zero_of_dvd hd)
  · rintro ⟨hp, h⟩
    refine ⟨hp, ?_⟩
    intro m hmp
    by_cases hm : m < 2
    · exact Or.inl hm
    · exact Or.inr (fun hmod => h m (by omega) hmp (Nat.dvd_of_mod_eq_zero hmod))

theorem isPrimeRef_eq_mathlib (p : Nat) :
    isPrimeRef p = decide (Nat.Prime p) := by
  apply Bool.eq_iff_iff.mpr
  simpa using isPrimeRef_iff p

/-- Trial division stops once d*d exceeds p. -/
def checkFrom (p : Nat) : Nat → Nat → Bool
  | 0, _ => false
  | fuel + 1, d =>
      if d * d ≤ p then (p % d == 0 || checkFrom p fuel (d + 1))
      else false

def isPrimeFast (p : Nat) : Bool :=
  decide (2 ≤ p) && !checkFrom p p 2

theorem checkFrom_iff (p : Nat) : ∀ fuel d,
    (checkFrom p fuel d = true) ↔
      ∃ e, d ≤ e ∧ e < d + fuel ∧ e * e ≤ p ∧ p % e = 0 := by
  intro fuel
  induction fuel with
  | zero =>
      intro d
      simp only [checkFrom]
      constructor
      · intro h; exact absurd h (by decide)
      · rintro ⟨e, h1, h2, _, _⟩; omega
  | succ f ih =>
      intro d
      rw [checkFrom]
      by_cases hd : d * d ≤ p
      · simp only [hd, if_true, Bool.or_eq_true, beq_iff_eq, ih (d + 1)]
        constructor
        · rintro (hmod | ⟨e, he1, he2, he3, he4⟩)
          · exact ⟨d, Nat.le_refl d, by omega, hd, hmod⟩
          · exact ⟨e, by omega, by omega, he3, he4⟩
        · rintro ⟨e, he1, he2, he3, he4⟩
          by_cases hde : d = e
          · subst hde; exact Or.inl he4
          · exact Or.inr ⟨e, by omega, by omega, he3, he4⟩
      · simp only [hd, if_false]
        constructor
        · intro h; exact absurd h (by decide)
        · rintro ⟨e, he1, _, he3, _⟩
          have := Nat.mul_le_mul he1 he1
          omega

theorem small_factor (p : Nat) :
    (∃ d, 2 ≤ d ∧ d < p ∧ p % d = 0) ↔
      (∃ e, 2 ≤ e ∧ e * e ≤ p ∧ p % e = 0) := by
  constructor
  · rintro ⟨d, hd2, hdp, hdmod⟩
    by_cases hsq : d * d ≤ p
    · exact ⟨d, hd2, hsq, hdmod⟩
    · have hdvd : d ∣ p := Nat.dvd_of_mod_eq_zero hdmod
      have hpe : d * (p / d) = p := Nat.mul_div_cancel' hdvd
      have hge2 : 2 ≤ p / d := by
        have h1 : d * 1 < d * (p / d) := by rw [hpe]; omega
        have := Nat.lt_of_mul_lt_mul_left h1
        omega
      have hlt : p / d < d := by
        have h2 : d * (p / d) < d * d := by rw [hpe]; omega
        exact Nat.lt_of_mul_lt_mul_left h2
      refine ⟨p / d, hge2, ?_, ?_⟩
      · calc
          (p / d) * (p / d) ≤ d * (p / d) :=
            Nat.mul_le_mul (Nat.le_of_lt hlt) (Nat.le_refl _)
          _ = p := hpe
      · have key : p % (p / d) = (d * (p / d)) % (p / d) := by rw [hpe]
        rw [key, Nat.mul_mod_left]
  · rintro ⟨e, he2, hesq, hemod⟩
    have h2e : 2 * e ≤ e * e := Nat.mul_le_mul he2 (Nat.le_refl e)
    exact ⟨e, he2, by omega, hemod⟩

theorem isPrimeFast_eq_ref (p : Nat) : isPrimeFast p = isPrimeRef p := by
  have hcheck : (checkFrom p p 2 = true) ↔
      ∃ d, 2 ≤ d ∧ d < p ∧ p % d = 0 := by
    rw [checkFrom_iff, small_factor]
    constructor
    · rintro ⟨e, h1, _, h3, h4⟩
      exact ⟨e, h1, h3, h4⟩
    · rintro ⟨e, h1, h3, h4⟩
      have : e ≤ e * e := Nat.le_mul_of_pos_right e (by omega)
      exact ⟨e, h1, by omega, h3, h4⟩
  have hall :
      ((List.range p).all (fun d => decide (d < 2) || p % d != 0) = true) ↔
        ¬ ∃ d, 2 ≤ d ∧ d < p ∧ p % d = 0 := by
    simp only [List.all_eq_true, List.mem_range, Bool.or_eq_true,
      decide_eq_true_eq, bne_iff_ne]
    constructor
    · rintro h ⟨d, hd2, hdp, hdmod⟩
      rcases h d hdp with h1 | h2
      · omega
      · exact h2 hdmod
    · intro h d hdp
      by_cases hd2 : d < 2
      · exact Or.inl hd2
      · exact Or.inr (fun hmod => h ⟨d, by omega, hdp, hmod⟩)
  unfold isPrimeFast isPrimeRef
  by_cases hp2 : 2 ≤ p
  · have hd : decide (2 ≤ p) = true := by simp [hp2]
    rw [hd, Bool.true_and, Bool.true_and]
    by_cases hcomp : ∃ d, 2 ≤ d ∧ d < p ∧ p % d = 0
    · have hcf : checkFrom p p 2 = true := hcheck.mpr hcomp
      have haf :
          (List.range p).all (fun d => decide (d < 2) || p % d != 0) = false := by
        cases h :
            (List.range p).all (fun d => decide (d < 2) || p % d != 0)
        · rfl
        · exact absurd hcomp (hall.mp h)
      rw [hcf, haf, Bool.not_true]
    · have hcf : checkFrom p p 2 = false := by
        cases h : checkFrom p p 2
        · rfl
        · exact absurd (hcheck.mp h) hcomp
      have haf :
          (List.range p).all (fun d => decide (d < 2) || p % d != 0) = true :=
        hall.mpr hcomp
      rw [hcf, haf, Bool.not_false]
  · have hd : decide (2 ≤ p) = false := by simp [hp2]
    rw [hd, Bool.false_and, Bool.false_and]

theorem isPrimeFast_eq_mathlib (p : Nat) :
    isPrimeFast p = decide (Nat.Prime p) :=
  (isPrimeFast_eq_ref p).trans (isPrimeRef_eq_mathlib p)

/-- Retain V1's first-order aggregate, replace only the primality predicate. -/
def countDirectFast : Nat → Nat
  | 0 => 0
  | n + 1 => countDirectFast n + if isPrimeFast (n + 1) then 1 else 0

theorem primeCounting_succ_step (n : Nat) :
    Nat.primeCounting (n + 1) =
      Nat.primeCounting n + if Nat.Prime (n + 1) then 1 else 0 := by
  rw [← Nat.primesLE_card_eq_primeCounting (n + 1),
      ← Nat.primesLE_card_eq_primeCounting n,
      Nat.primesLE_succ]
  by_cases hp : Nat.Prime (n + 1)
  · simp [hp, Nat.notMem_primesLE]
  · simp [hp]

theorem countDirectFast_eq (n : Nat) :
    countDirectFast n = Nat.primeCounting n := by
  induction n with
  | zero =>
      simp [countDirectFast]
  | succ n ih =>
      rw [countDirectFast, ih, primeCounting_succ_step]
      simp [isPrimeFast_eq_mathlib]

def impl (n : Nat) : Nat := countDirectFast n

theorem impl_correct : ∀ n, impl n = primeCountSpec n := by
  intro n
  exact countDirectFast_eq n

end Submission
'''
path = OUT / "Submission_v2.lean"
path.write_text(text)
print(f"generated {path} bytes={len(text.encode())}")
