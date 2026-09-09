"""Compile the exact selected certificate data into independent Lean obligations.
No source lower-bound theorem is imported. No synthesis occurs in source jobs.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from fractions import Fraction as Q
from certcheck import norm,verify,encode
from procedures import build


def scalar(v):
    q=Q(v)
    return str(q.numerator) if q.denominator==1 else f'({q.numerator} / {q.denominator} : ℝ)'


def poly(p,var='x'):
    p=norm(p)
    return ' + '.join(f'({scalar(v)}) * {var} ^ {k}' for k,v in sorted(p.items())) or '(0 : ℝ)'


def certificate_expr(c,var='x'):
    kind=c['kind']
    if kind=='coeff':return poly(c['polynomial'],var)
    if kind=='square':
        return f'{var} ^ {c["power"]} * (({scalar(c["A"])}) * ({var} - ({scalar(c["r"])})) ^ 2 + ({scalar(c["D"])}))'
    if kind=='affine':return f'(({scalar(c["a"])}) * {var} + ({scalar(c["b"])}))'
    if kind in ('sum','product'):
        op=' + ' if kind=='sum' else ' * '
        return '('+op.join(certificate_expr(x,var) for x in c['children'])+')'
    raise ValueError(kind)


def certificate_proof(c,domain,var='x',prefix='h'):
    kind=c['kind']
    if kind=='square':
        return f'''  exact ProcedureRules.halfLineSquare_sound {c['power']} ({scalar(c['A'])}) ({scalar(c['r'])}) ({scalar(c['D'])}) (by norm_num) (by norm_num) hx'''
    if kind=='affine':
        return f'''  exact ProcedureRules.intervalAffine_sound ({scalar(c['a'])}) ({scalar(c['b'])}) ({scalar(domain[1])}) ({scalar(domain[2])}) (by norm_num) (by norm_num) hx'''
    if kind=='product':
        lines=[]
        for i,child in enumerate(c['children']):
            e=certificate_expr(child,var)
            lines.append(f'  have h{i} : 0 ≤ {e} := by\n'+'\n'.join('    '+line.lstrip() for line in certificate_proof(child,domain,var,prefix+str(i)).splitlines()))
        if len(c['children'])!=2:raise ValueError('binary product required')
        lines.append('  exact ProcedureRules.product_sound h0 h1')
        return '\n'.join(lines)
    if kind=='coeff':
        coeffs=[Q(c['polynomial'].get(str(k),0)) for k in range(max([int(k) for k in c['polynomial']],default=-1)+1)]
        return f'''  have h := ProcedureRules.coeffPoly_sound [{', '.join(scalar(x) for x in coeffs)}] (by simp; norm_num) hx
  simpa [ProcedureRules.coeffPoly] using h'''
    raise ValueError(kind)


def render_nonneg(name,p,domain,c):
    expr=poly(p)
    cert=certificate_expr(c)
    domain_text='0 ≤ x' if domain[0]=='ray' else f'({scalar(domain[1])}) ≤ x ∧ x ≤ ({scalar(domain[2])})'
    return f'''private theorem {name}_identity (x : ℝ) :
    {expr} = {cert} := by ring

theorem {name} {{x : ℝ}} (hx : {domain_text}) :
    0 ≤ {expr} := by
  rw [{name}_identity]
{certificate_proof(c,domain)}
'''


def render_lower(p,domain,c):
    P=poly(p,'y');expr='(1 : ℝ) * z - (1 / 4 : ℝ) * z ^ 2'
    return f'''import Mathlib
import ProcedureRules

/-! Generated from a replayed certificate; no withheld lower theorem. -/
noncomputable section
namespace CrossDomainResidual.ProcedureRepair
open Real Set

{render_nonneg('derivative_nonneg',p,domain,c)}
private theorem derivative_certificate (y : ℝ) :
    deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      ({P}) / (1 + y ^ 2) := by
  have hlin : HasDerivAt (fun z : ℝ => (1 : ℝ) * z) 1 y := by
    simpa using ((hasDerivAt_id' y).const_mul (1 : ℝ))
  have hpow : HasDerivAt (fun z : ℝ => (1 / 4 : ℝ) * z ^ 2)
      ((1 / 4 : ℝ) * ((2 : ℕ) * y ^ (2 - 1))) y := by
    exact (hasDerivAt_pow 2 y).const_mul (1 / 4 : ℝ)
  have hp : HasDerivAt (fun z : ℝ => {expr})
      (1 - (1 / 4 : ℝ) * ((2 : ℕ) * y ^ (2 - 1))) y := hlin.sub hpow
  have hd : deriv (fun z : ℝ => Real.arctan z - ({expr})) y =
      1 / (1 + y ^ 2) - (1 - (1 / 4 : ℝ) * ((2 : ℕ) * y ^ (2 - 1))) :=
    ((hasDerivAt_arctan y).sub hp).deriv
  rw [hd]
  have hden : 0 < 1 + y ^ 2 := by positivity
  field_simp [ne_of_gt hden]
  ring

/-- The original obligation becomes provable using the repaired procedure. -/
theorem recovered_lower {{x : ℝ}} (hx : 0 ≤ x) :
    x - x ^ 2 / 4 ≤ Real.arctan x := by
  let f : ℝ → ℝ := fun z => Real.arctan z - ({expr})
  have hdiff : Differentiable ℝ f :=
    differentiable_arctan.sub (by fun_prop)
  have hmono : MonotoneOn f (Ici (0 : ℝ)) := by
    apply monotoneOn_of_deriv_nonneg (convex_Ici 0)
    · exact hdiff.continuous.continuousOn
    · exact hdiff.differentiableOn
    · intro y hy
      have hypos : 0 < y := by simpa only [interior_Ici, mem_Ioi] using hy
      change 0 ≤ deriv (fun z : ℝ => Real.arctan z - ({expr})) y
      rw [derivative_certificate]
      exact div_nonneg (derivative_nonneg hypos.le) (by positivity)
  have h := hmono (show (0 : ℝ) ∈ Ici 0 by simp) (show x ∈ Ici 0 from hx) hx
  dsimp [f] at h
  simp only [Real.arctan_zero] at h
  norm_num at h
  linarith

#print axioms derivative_nonneg
#print axioms recovered_lower
end CrossDomainResidual.ProcedureRepair
'''


def render_interval(p,domain,c):
    return f'''import Mathlib
import ProcedureRules

namespace CrossDomainResidual.ProcedureRepair
{render_nonneg('interval_nonneg',p,domain,c)}
#print axioms interval_nonneg
end CrossDomainResidual.ProcedureRepair
'''


def emit(result,out):
    if result['status']!='PASS':raise ValueError('qualification failed')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[]
    for task,stage in zip((
        ({1:Q(1,2),2:Q(-1),3:Q(1,2)},('ray',)),
        ({0:Q(1),2:Q(-1)},('interval',Q(0),Q(1)))),result['stages']):
        p,domain=task
        promoted=stage['residual']['promoted_certificates']
        if len(promoted)!=1:raise ValueError('no unique promoted repair')
        name,c=next(iter(promoted.items()))
        if build(name,p,domain)!=c or not verify(p,domain,c):raise ValueError('invalid certificate')
        records.append({'procedure':name,'polynomial':encode(p),'domain':[str(x) for x in domain],'certificate':c})
    (out/'certificate.json').write_text(json.dumps(records,indent=2)+'\n')
    (out/'RecoveredProcedures.lean').write_text(render_lower({1:Q(1,2),2:Q(-1),3:Q(1,2)},('ray',),records[0]['certificate']))
    (out/'HeldoutProcedure.lean').write_text(render_interval({0:Q(1),2:Q(-1)},('interval',Q(0),Q(1)),records[1]['certificate']))
    print('EMITTED_PROCEDURES',json.dumps(records))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--result',required=True);a.add_argument('--out',required=True);args=a.parse_args()
    emit(json.loads(Path(args.result).read_text()),args.out)
