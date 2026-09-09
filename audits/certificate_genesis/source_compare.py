"""Post-freeze source comparison. The original theorem is used only here."""
import argparse,json
from pathlib import Path
from fractions import Fraction as Q
from grammar import generate_extensions
from emit_form import scalar

def render(record):
    a=scalar(Q(record['slope']));c=scalar(Q(record['coefficient']));n=int(record['exponent'])
    expr=f'({a}) * x - ({c}) * x ^ {n}'
    return f'''import EulerBlowup.Elementary
import RecoveredGenesis

noncomputable section
namespace CrossDomainResidual.GenesisSourceCheck

/-- The new estimate dominates the source cubic estimate on the stated ray. -/
theorem quadratic_stronger_on {{x : ℝ}} (hx : 3 / 4 ≤ x) :
    x - x ^ 3 / 3 ≤ {expr} := by
  have h0 : 0 ≤ x ^ 2 := sq_nonneg x
  have h1 : 0 ≤ 4 * x - 3 := by linarith
  nlinarith [mul_nonneg h0 h1]

/-- The generated bound implies the original source estimate on that ray. -/
theorem recovered_implies_source_on {{x : ℝ}} (hx : 3 / 4 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x := by
  have h0 : 0 ≤ x := by linarith
  exact (quadratic_stronger_on hx).trans (CertificateGenesis.recovered_lower h0)

/-- The genuine source theorem remains independently available. -/
theorem original_source_check {{x : ℝ}} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x :=
  EulerBlowup.self_sub_cube_le_arctan hx

/-- The two certified lower bounds are distinct at the protected point. -/
theorem strict_improvement_at_one :
    (1 : ℝ) - 1 ^ 3 / 3 < ({a}) * 1 - ({c}) * 1 ^ {n} := by norm_num

#print axioms quadratic_stronger_on
#print axioms recovered_implies_source_on
#print axioms original_source_check
#print axioms strict_improvement_at_one
end CrossDomainResidual.GenesisSourceCheck
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--certificate',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();record=json.loads(Path(args.certificate).read_text())
    _,_,_,extensions,_=generate_extensions()
    matches=[e for e in extensions if e.record()==record]
    if len(matches)!=1:raise ValueError('Invalid frozen certificate')
    Path(args.output).write_text(render(record))
if __name__=='__main__':main()
