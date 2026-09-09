"""Post-freeze source comparison only; never used by expression synthesis.

The known source statement is intentionally present here. The recovered form
is read from the immutable certificate after target qualification.
"""
import argparse,json
from pathlib import Path
from fractions import Fraction as Q
from form_synthesis import generate
from emit_form import scalar

def render(record):
    a=scalar(Q(record['slope'])); c=scalar(Q(record['coefficient'])); n=int(record['exponent'])
    return f'''import EulerBlowup.Elementary
import RecoveredForm

noncomputable section
namespace CrossDomainResidual.FormSourceCheck

private theorem expression_agreement (x : ℝ) :
    ({a}) * x - ({c}) * x ^ {n} = x - x ^ 3 / 3 := by ring

/-- Recovered estimate implies the exact source statement. -/
theorem recovered_implies_source {{x : ℝ}} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x := by
  rw [← expression_agreement]
  exact FormRecovered.recovered_lower hx

/-- Original source estimate implies the recovered statement. -/
theorem source_implies_recovered {{x : ℝ}} (hx : 0 ≤ x) :
    ({a}) * x - ({c}) * x ^ {n} ≤ Real.arctan x := by
  rw [expression_agreement]
  exact EulerBlowup.self_sub_cube_le_arctan hx

#print axioms expression_agreement
#print axioms recovered_implies_source
#print axioms source_implies_recovered
end CrossDomainResidual.FormSourceCheck
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--certificate',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();record=json.loads(Path(args.certificate).read_text())
    cs,_,_=generate();matches=[c for c in cs if c.name==record['name']]
    if len(matches)!=1 or matches[0].record()!=record:raise ValueError('Invalid frozen certificate')
    Path(args.output).write_text(render(record))

if __name__=='__main__':main()
