"""Generic proof compiler for the frozen one-correction expression grammar.

Only consumes the selected certificate and form_synthesis. No target oracle,
source estimate, source proof, or source comparison is imported here.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from fractions import Fraction as Q
from form_synthesis import generate,validate

def scalar(q):
    q=Q(q)
    return str(q.numerator) if q.denominator==1 else f'({q.numerator} / {q.denominator} : ℝ)'

def polynomial(p,variable='y'):
    return ' + '.join(f'({scalar(v)}) * {variable} ^ {k}' for k,v in sorted(p.items()) if v) or '(0 : ℝ)'

def render(candidate):
    assert validate(candidate)
    a=scalar(candidate.slope);c=scalar(candidate.coefficient);n=candidate.exponent
    p=polynomial(dict(candidate.certificate))
    expr=f'({a}) * z - ({c}) * z ^ {n}'
    dexpr=f'({a}) - ({c}) * (({n} : ℕ) * y ^ ({n} - 1))'
    return f'''import Mathlib

/-! Generated from a rational expression and exact derivative certificate.
The candidate exponent and coefficient are data, not a source proof import.
The bounded grammar and the calculus proof method were supplied in advance. -/
noncomputable section
namespace CrossDomainResidual.FormRecovered
open Real Set

private theorem polynomial_derivative_certificate (y : ℝ) :
    deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      ({p}) / (1 + y ^ 2) := by
  have hlin : HasDerivAt (fun z : ℝ => ({a}) * z) ({a}) y := by
    simpa using ((hasDerivAt_id' y).const_mul ({a}))
  have hpow : HasDerivAt (fun z : ℝ => ({c}) * z ^ {n})
      (({c}) * (({n} : ℕ) * y ^ ({n} - 1))) y := by
    exact (hasDerivAt_pow {n} y).const_mul ({c})
  have hp : HasDerivAt (fun z : ℝ => {expr}) ({dexpr}) y :=
    hlin.sub hpow
  have hd : deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      1 / (1 + y ^ 2) - ({dexpr}) :=
    ((hasDerivAt_arctan y).sub hp).deriv
  rw [hd]
  have hden : 0 < 1 + y ^ 2 := by positivity
  field_simp [ne_of_gt hden]
  ring

/-- Universal lower estimate reconstructed from the selected expression. -/
theorem recovered_lower {{x : ℝ}} (hx : 0 ≤ x) :
    ({a}) * x - ({c}) * x ^ {n} ≤ Real.arctan x := by
  have hmono : Monotone (fun x : ℝ => Real.arctan x - (({a}) * x - ({c}) * x ^ {n})) := by
    apply monotone_of_deriv_nonneg
    · exact differentiable_arctan.sub (by fun_prop)
    · intro y
      rw [polynomial_derivative_certificate]
      exact div_nonneg (by positivity) (by positivity)
  have h := hmono hx
  simp only [Real.arctan_zero] at h
  norm_num at h
  linarith

#print axioms recovered_lower
end CrossDomainResidual.FormRecovered
'''

def emit(result,output,certificate):
    if result['status']!='PASS' or len(result['selected'])!=1:
        raise ValueError('No unique qualified expression to compile')
    candidates,_,_=generate()
    record=result['selected'][0]
    matches=[c for c in candidates if c.name==record['name']]
    if len(matches)!=1 or matches[0].record()!=record:
        raise ValueError('Selected expression or certificate does not match frozen grammar')
    c=matches[0]
    text=render(c)
    Path(output).write_text(text)
    Path(certificate).write_text(json.dumps(c.record(),indent=2,default=str)+'\n')
    return c

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--result',required=True);p.add_argument('--output',required=True)
    p.add_argument('--certificate',required=True)
    args=p.parse_args()
    c=emit(json.loads(Path(args.result).read_text()),args.output,args.certificate)
    print('EMITTED_FORM',c.record())

if __name__=='__main__':main()
