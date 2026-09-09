"""Generic compiler for the frozen square-certificate language.
Consumes a selected certificate, not the target oracle or withheld source proof.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from fractions import Fraction as Q
from grammar import generate_extensions,validate_extension
from emit_form import scalar,polynomial


def render(e):
    assert validate_extension(e)
    c=e.candidate;a=scalar(c.slope);b=scalar(c.coefficient);n=c.exponent
    k=e.k; A=scalar(e.square['A']);r=scalar(e.square['r']);D=scalar(e.square['D'])
    p=polynomial(dict(c.certificate))
    expr=f'({a}) * z - ({b}) * z ^ {n}'
    dexpr=f'({a}) - ({b}) * (({n} : ℕ) * y ^ ({n} - 1))'
    square=f'y ^ {k} * (({A}) * (y - ({r})) ^ 2 + ({D}))'
    return f'''import Mathlib

/-! Generated from an exact rational certificate. The old expression grammar
is unchanged; the new certificate is a monomial times a nonnegative square.
No withheld source lower estimate is imported. -/
noncomputable section
namespace CrossDomainResidual.CertificateGenesis
open Real Set

private theorem polynomial_identity (y : ℝ) :
    ({p}) = {square} := by ring

private theorem polynomial_nonneg (y : ℝ) (hy : 0 ≤ y) :
    0 ≤ ({p}) := by
  rw [polynomial_identity]
  have hpow : 0 ≤ y ^ {k} := pow_nonneg hy _
  have hsq : 0 ≤ (y - ({r})) ^ 2 := sq_nonneg _
  have hA : 0 ≤ ({A} : ℝ) := by norm_num
  have hD : 0 ≤ ({D} : ℝ) := by norm_num
  exact mul_nonneg hpow (add_nonneg (mul_nonneg hA hsq) hD)

private theorem polynomial_derivative_certificate (y : ℝ) :
    deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      ({p}) / (1 + y ^ 2) := by
  have hlin : HasDerivAt (fun z : ℝ => ({a}) * z) ({a}) y := by
    simpa using ((hasDerivAt_id' y).const_mul ({a}))
  have hpow : HasDerivAt (fun z : ℝ => ({b}) * z ^ {n})
      (({b}) * (({n} : ℕ) * y ^ ({n} - 1))) y := by
    exact (hasDerivAt_pow {n} y).const_mul ({b})
  have hp : HasDerivAt (fun z : ℝ => {expr}) ({dexpr}) y := hlin.sub hpow
  have hd : deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      1 / (1 + y ^ 2) - ({dexpr}) :=
    ((hasDerivAt_arctan y).sub hp).deriv
  rw [hd]
  have hden : 0 < 1 + y ^ 2 := by positivity
  field_simp [ne_of_gt hden]
  ring

/-- Universal lower estimate from the generated half-line certificate. -/
theorem recovered_lower {{x : ℝ}} (hx : 0 ≤ x) :
    ({a}) * x - ({b}) * x ^ {n} ≤ Real.arctan x := by
  let f : ℝ → ℝ := fun z => Real.arctan z - (({a}) * z - ({b}) * z ^ {n})
  have hdiff : Differentiable ℝ f :=
    differentiable_arctan.sub (by fun_prop)
  have hmono : MonotoneOn f (Ici (0 : ℝ)) := by
    apply monotoneOn_of_deriv_nonneg (convex_Ici 0)
    · exact hdiff.continuous.continuousOn
    · exact hdiff.differentiableOn
    · intro y hy
      have hypos : 0 < y := by simpa only [interior_Ici, mem_Ioi] using hy
      change 0 ≤ deriv (fun z : ℝ => Real.arctan z - ({expr})) y
      rw [polynomial_derivative_certificate]
      exact div_nonneg (polynomial_nonneg y hypos.le) (by positivity)
  have h := hmono (show (0 : ℝ) ∈ Ici 0 by simp) (show x ∈ Ici 0 from hx) hx
  dsimp [f] at h
  simp only [Real.arctan_zero] at h
  norm_num at h
  linarith

#print axioms recovered_lower
end CrossDomainResidual.CertificateGenesis
'''


def emit(result,output,certificate):
    if result['status']!='PASS' or len(result['selected'])!=1:
        raise ValueError('No unique qualified expression to compile')
    _,_,_,extensions,_=generate_extensions()
    record=result['selected'][0]
    matches=[e for e in extensions if e.record()==record]
    if len(matches)!=1:raise ValueError('Selected certificate does not match frozen grammar')
    e=matches[0]
    Path(output).write_text(render(e))
    Path(certificate).write_text(json.dumps(record,indent=2)+'\n')
    return e


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--result',required=True);p.add_argument('--output',required=True)
    p.add_argument('--certificate',required=True)
    args=p.parse_args()
    e=emit(json.loads(Path(args.result).read_text()),args.output,args.certificate)
    print('EMITTED_CERTIFICATE',e.record())

if __name__=='__main__':main()
