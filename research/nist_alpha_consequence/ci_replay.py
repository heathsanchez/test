#!/usr/bin/env python3
"""Independent CODATA three-estimate consequence replay, stdlib only.

Not an experimental-data source attestation or full NIST correlated adjustment.
"""
import hashlib
import json
import math
from decimal import Decimal as D, getcontext
from fractions import Fraction as F
from pathlib import Path

getcontext().prec=55
sources=[
    ('Parker2018Cs','137.035999046','0.000000027'),
    ('Morel2020Rb','137.035999206','0.000000011'),
    ('Fan2023ElectronQED','137.035999166','0.000000015'),
]
expansion=D('2.5')  # NIST published, NOT independently selected.
c=D('299792458');h=D('6.62607015e-34');e=D('1.602176634e-19')

def unique(rows):
    out={}
    for source_id,value,uncertainty in rows:
        if source_id in out and out[source_id] != (value,uncertainty):
            raise ValueError('CONFLICTING_SOURCE_ID')
        if D(uncertainty)<=0:raise ValueError('INVALID_SIGMA')
        out[source_id]=(value,uncertainty)
    return [(a,*out[a]) for a in out]

def estimate(rows):
    rows=unique(rows)
    weights=[D(1)/D(s)**2 for _,_,s in rows]
    x=sum(D(v)*w for (_,v,_),w in zip(rows,weights))/sum(weights)
    ux=(D(1)/sum(weights)).sqrt()
    chi=sum(((D(v)-x)/D(s))**2 for _,v,s in rows)
    # Truly separate exact-rational implementation.
    wf=[F(1)/F(s)**2 for _,_,s in rows]
    xf=sum((F(v)*w for (_,v,_),w in zip(rows,wf)),F(0))/sum(wf)
    xr=D(xf.numerator)/D(xf.denominator)
    assert abs(x-xr)<D('1e-43'),'INDEPENDENT_NUMERICAL_BACKEND_MISMATCH'
    return x,ux,chi

x,ux,chi=estimate(sources)
v=c/x
z=2*h/(e*e*x)
mu=z/c
eps=1/(z*c)
rk=h/(e*e)
cs,rb=sources[0],sources[1]
pair=abs(D(cs[1])-D(rb[1]))/((D(cs[2])**2+D(rb[2])**2).sqrt())
raw_pull=[(D(vv)-x)/D(ss) for _,vv,ss in sources]
refs={
 'inverse_alpha':('137.035999177','0.000000021',x),
 'atomic_unit_velocity_m_s':('2187691.26216','0.00034',v),
 'impedance_ohm':('376.730313412','0.000000059',z),
 'permeability_N_A2':('1.25663706127e-6','2.0e-16',mu),
 'permittivity_F_m':('8.8541878188e-12','1.4e-21',eps)
}
comparison={key:abs(value-D(published))/D(sigma) for key,(published,sigma,value) in refs.items()}
# Negative: real disagreement cannot be relabeled mutually-confirming.
assert pair>D(5) and chi>D(25)
assert math.exp(-float(chi)/2)<1e-6  # exact chi^2(2) tail probability
assert max(abs(t/expansion) for t in raw_pull)<D(2)
assert chi/(expansion**2)<D(6)
assert max(comparison.values())<D('0.10')
# No pseudo-replication: the same source id cannot narrow uncertainty.
clone=estimate(sources+[sources[1]])
assert clone==(x,ux,chi)
try:
    estimate(sources+[('Morel2020Rb','137.035999200','0.000000011')])
    raise AssertionError('CONFLICTING_SOURCE_WAS_NOT_REJECTED')
except ValueError as ex:
    assert str(ex)=='CONFLICTING_SOURCE_ID'
# Replaying the NIST recommendation itself as a fourth lab is disallowed.
assert len(unique(sources))==3
# Source withdrawal is simulated and changes descendants, not exact SI inputs.
withdrawn_x=estimate([row for row in sources if row[0]!='Morel2020Rb'])[0]
assert withdrawn_x != x and c/withdrawn_x != v
assert (h/(e*e)) == rk
# No optimum measurement design is justified without systematic hypotheses.
unknown='UNKNOWN_SYSTEMATIC_MODEL_AND_INDEPENDENCE_NOT_ESTABLISHED'
record={
 'authority':'WARRANTED_BOUNDED_CODATA_THREE_SOURCE_NUMERICAL_REPLAY',
 'source_values':'MANUALLY_TRANSCRIBED_NOT_SOURCE_BYTES_ATTESTED',
 'source_pdf':'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958143',
 'data':sources,
 'input_sha256':hashlib.sha256(json.dumps(sources,separators=(',',':')).encode()).hexdigest(),
 'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'inverse_alpha':str(x),
 'raw_uncertainty_alpha_inverse':str(ux),
 'codata_2p5_expanded_uncertainty_alpha_inverse':str(expansion*ux),
 'chi2_unexpanded_2dof':str(chi),
 'Cs_vs_Rb_sigma':str(pair),
 'atomic_unit_velocity_m_s':str(v),
 'atomic_unit_velocity_u_m_s':str(v*expansion*ux/x),
 'comparison_z_vs_NIST':{k:str(val) for k,val in comparison.items()},
 'downstream_outputs_share_single_alpha_parameter':True,
 'derived_outputs_do_not_add_independent_support':True,
 'withdrawal_test':'PASS_SIMULATED_RECOMPUTATION_NOT_ACTUAL_SOURCE_RETRACTION',
 'independent_backend':'Decimal_vs_Fraction',
 'full_133_input_CODATA_adjustment':False,
 'source_pdf_bytes_verified':False,
 'optimum_new_physical_experiment':unknown,
 'result':'PASS_BOUNDED_NUMERICAL_REPLAY_ONLY'
}
out=Path('research/nist_alpha_consequence/evidence')
out.mkdir(parents=True,exist_ok=True)
(out/'ci_report.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
