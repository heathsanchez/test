"""Compile the recovered rational certificate into a Lean proof.

The template uses the arctangent derivative, polynomial differentiation,
positivity and monotonicity. It does not import or inspect the withheld source
lower-bound theorem. The derivative elaboration repair changes no mathematics.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from fractions import Fraction as Q
from heldout_recovery import synthesize_coefficient

def scalar(q):
    q=Q(q)
    return str(q.numerator) if q.denominator==1 else f'({q.numerator} / {q.denominator} : ℝ)'

def polynomial(p,variable='y'):
    terms=[]
    for k,v in sorted(p.items()):
        if v:
            terms.append(f'({scalar(v)}) * {variable} ^ {k}')
    return ' + '.join(terms) if terms else '(0 : ℝ)'

def render(result):
    assert result['status']=='PASS'
    c=result['coefficient']; p=polynomial(result['certificate'])
    return f'''import Mathlib

/-! Generated from the exact certificate in heldout_recovery.py.
No imported source lower-bound theorem or proof body. The polynomial basis,
derivative identity and monotonicity proof method were supplied in advance.
The recovered rational coefficient is {c}. -/
noncomputable section
namespace CrossDomainResidual.RecoveredLower
open Real Set

private theorem polynomial_derivative_certificate (y : ℝ) :
    deriv (fun z : ℝ => Real.arctan z - (z - ({scalar(c)}) * z ^ 3)) y =
      ({p}) / (1 + y ^ 2) := by
  have hp : HasDerivAt (fun z : ℝ => z - ({scalar(c)}) * z ^ 3)
      (1 - 3 * ({scalar(c)}) * y ^ 2) y := by
    have h3 : HasDerivAt (fun z : ℝ => z ^ 3) ((3 : ℕ) * y ^ (3 - 1)) y :=
      hasDerivAt_pow 3 y
    have h4 := (hasDerivAt_id' y).sub (h3.const_mul ({scalar(c)}))
    have h5 : (1 : ℝ) - ({scalar(c)}) * ((3 : ℕ) * y ^ (3 - 1)) =
        1 - 3 * ({scalar(c)}) * y ^ 2 := by push_cast; ring
    rw [h5] at h4
    exact h4
  have hd : deriv (fun z : ℝ => Real.arctan z - (z - ({scalar(c)}) * z ^ 3)) y =
      1 / (1 + y ^ 2) - (1 - 3 * ({scalar(c)}) * y ^ 2) :=
    ((hasDerivAt_arctan y).sub hp).deriv
  rw [hd]
  have hden : 0 < 1 + y ^ 2 := by positivity
  field_simp [ne_of_gt hden]
  ring

/-- Recovered lower estimate, independently proved for every nonnegative real. -/
theorem recovered_arctan_lower {{x : ℝ}} (hx : 0 ≤ x) :
    x - ({scalar(c)}) * x ^ 3 ≤ Real.arctan x := by
  have hmono : Monotone (fun x : ℝ => Real.arctan x - (x - ({scalar(c)}) * x ^ 3)) := by
    apply monotone_of_deriv_nonneg
    · exact differentiable_arctan.sub (by fun_prop)
    · intro y
      rw [polynomial_derivative_certificate]
      exact div_nonneg (by positivity) (by positivity)
  have h := hmono hx
  simp only [Real.arctan_zero] at h
  norm_num at h
  linarith

#print axioms recovered_arctan_lower
end CrossDomainResidual.RecoveredLower
'''

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--output',required=True)
    a.add_argument('--certificate',required=True)
    args=a.parse_args()
    result=synthesize_coefficient()
    if result['status']!='PASS':raise SystemExit('GRAMMAR_INSUFFICIENT')
    text=render(result)
    Path(args.output).write_text(text)
    Path(args.certificate).write_text(json.dumps({
      'coefficient':str(result['coefficient']),
      'polynomial':{str(k):str(v) for k,v in result['certificate'].items()},
      'basis':result['basis'],'method':result['method']},indent=2)+'\n')
    print('RECOVERED_COEFFICIENT',result['coefficient'])
    print('DERIVATIVE_CERTIFICATE',result['certificate'])

if __name__=='__main__':main()
