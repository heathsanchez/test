#!/usr/bin/env python3
"""Source-specified non-interacting spin-bath history quotient, with noncommuting negative control.
Dasari et al., Nat Commun 13, 7527 (2022), Supplementary Notes 1-2 Eqs (9)-(13).
Numerical source-calibrated width is a model-input, not microscopic experimental tomography.
Never reads designated heldout Fig3b data.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json
import numpy as np

# Angular width comes from V11 source-mapped observed Fig2b prior fit.
sigma=2.5048587547988044
omega=np.linspace(-11,11,401)
p=np.exp(-.5*(omega/sigma)**2); p/=p.sum()
tau=.6
qpos=np.cos(omega*tau/2)**2
qneg=1-qpos
future_t=np.array([.27,.51,.75,1.11,1.47,2.07])
probes=np.cos(np.outer(future_t,omega))

def outcome(h):
    likelihood=np.ones_like(p)
    for c in h: likelihood *= qpos if c=='+' else qneg
    mass=float(p@likelihood)
    state=p*likelihood/mass
    return mass,state,probes@state

hist={}
groups={}
for h in product('+-',repeat=4):
    h=''.join(h)
    hist[h]=outcome(h)
    groups.setdefault(h.count('-'),[]).append(h)

max_mass_err=0.; max_future_err=0.; max_state_err=0.
for group in groups.values():
    ref=hist[group[0]]
    for h in group[1:]:
        mass,state,pred=hist[h]
        max_mass_err=max(max_mass_err,abs(mass-ref[0]))
        max_state_err=max(max_state_err,float(np.max(np.abs(state-ref[1]))))
        max_future_err=max(max_future_err,float(np.max(np.abs(pred-ref[2]))))
sum_prob=sum(v[0] for v in hist.values())
nonselective=sum((v[0]*v[1] for v in hist.values()))
max_reconstruction=float(np.max(abs(nonselective-p)))
assert len(hist)==16 and len(groups)==5
assert max_mass_err<1e-12 and max_future_err<1e-12 and max_reconstruction<1e-12
assert abs(sum_prob-1)<1e-12
# Each two different counts is experimentally separable by at least one declared future probe.
for a in groups:
    for b in groups:
        if a<b:
            va=hist[groups[a][0]][2];vb=hist[groups[b][0]][2]
            assert np.max(abs(va-vb))>1e-3
# 2x2 exact rational countercontrol: U is an orthogonal intra-bath rotation.
# Q±² are complete; M±=Q± U are an ordinary valid quantum instrument.
U=np.array([[F(3,5),-F(4,5)],[F(4,5),F(3,5)]],dtype=object)
Qp=np.diag([F(3,5),F(4,5)]).astype(object)
Qm=np.diag([F(4,5),F(3,5)]).astype(object)
rho=np.diag([F(3,4),F(1,4)]).astype(object)
assert (Qp@Qp+Qm@Qm).tolist()==np.eye(2,dtype=object).tolist()
def exact_branch(h):
    x=rho
    for s in h:
        T=(Qp if s=='+' else Qm)@U
        x=T@x@T.T
    return x[0,0]+x[1,1]
a=exact_branch('+-');b=exact_branch('-+')
assert a!=b
assert sum([exact_branch(''.join(h)) for h in product('+-',repeat=2)],F(0))==1
output={
 'source':'Dasari et al. 2022, SI Note 2 Eq. (11)-(13), fixed tau and noninteracting bath',
 'model_scope':'Measured pre FID width input; ideal Gaussian dephasing bath; numerical structural check not direct empirical heldout',
 'tau_microseconds':tau, 'measurement_count':4,
 'total_history_records':len(hist),'distinct_future_classes':len(groups),
 'records_by_minus_count':{str(k):len(v) for k,v in groups.items()},
 'max_within_class_record_probability_difference':max_mass_err,
 'max_within_class_conditioned_future_difference':max_future_err,
 'max_within_class_bath_population_difference':max_state_err,
 'unread_measurement_reconstruction_max_abs':max_reconstruction,
 'total_record_probability':sum_prob,
 'm20_history_count':2**20,'m20_state_count_under_source_assumptions':21,
 'noncommuting_countercontrol_plus_minus_probability':str(a),
 'noncommuting_countercontrol_minus_plus_probability':str(b),
 'noncommuting_countercontrol_exact_difference':str(a-b),
 'countercontrol_two_step_probability_sum':'1',
 'status':'WARRANTED source-conditioned consequence, already implied by published standard quantum instrument; novel law REJECTED',
 'holdout':'Fig3b untouched'
}
out=Path(__file__).resolve().parent/'history_quotient_results.json'
out.write_text(json.dumps(output,indent=2)+'\n')
print('HISTORY_QUOTIENT',json.dumps(output))
