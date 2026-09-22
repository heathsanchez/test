#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"shift_v3.py"))
src=(OUT/"Submission_v3.lean").read_text()
old='''def impl (n : Nat) : Int := resultantFromPolyMul (polyOfShift n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, polyOfShift_eq, resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm
'''
new=r'''/-- V6 probe: dividend is an invariantly trimmed PRS state. The trusted
pseudo-remainder trims each freshly-created next and then trims it again on
recursive entry; this version performs that scan exactly once. -/
def pseudoRemainderGoOnce :
    Nat → Nat → List Int → List Int → Option (List Int)
  | 0, _, _, _ => none
  | fuel + 1, remaining, divisor, dividend =>
      if dividend.length < divisor.length then
        some (scalePolynomial ((divisor.headD 0) ^ remaining) dividend)
      else
        match divisor, dividend with
        | lcG :: divisorTail, lcR :: dividendTail =>
            let next :=
              trimLeading
                (cancelPseudoLeading lcG lcR dividendTail divisorTail)
            pseudoRemainderGoOnce fuel (remaining - 1) divisor next
        | _, _ => none

def pseudoRemainderOnce (dividend divisor : List Int) : Option (List Int) :=
  let dividend := trimLeading dividend
  let divisor := trimLeading divisor
  if divisor.isEmpty then none
  else if dividend.length < divisor.length then some dividend
  else
    pseudoRemainderGoOnce (dividend.length + 1)
      (dividend.length - divisor.length + 1) divisor dividend

def normalResultantGoOnce :
    Nat → Bool → List Int → List Int → Option Int
  | 0, _, _, _ => none
  | fuel + 1, initial, f, g =>
      match pseudoRemainderOnce f g with
      | none => none
      | some raw =>
          let divided :=
            if initial then some raw
            else exactDividePolynomial ((f.headD 0) * (f.headD 0)) raw
          match divided with
          | none => none
          | some coefficients =>
              match trimLeading coefficients with
              | [] => some 0
              | remainder =>
                  if remainder.length + 1 == g.length then
                    match remainder with
                    | [constant] => some constant
                    | _ => normalResultantGoOnce fuel false g remainder
                  else none

def resultantTrimOnce (p : List Int) : Int :=
  let derivative := derivHL p
  match normalResultantGoOnce 25 true p derivative with
  | some resultant => resultant
  | none => bareissDet (monicReducedSylvester p derivative)

def impl (n : Nat) : Int := resultantTrimOnce (polyOfShift n)
'''
if old not in src:
    raise SystemExit("V3 final block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v6_prs_trim_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
