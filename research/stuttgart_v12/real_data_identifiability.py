#!/usr/bin/env python3
"""Diagnostic only: inverse feasibility for published Fig2b; sealed Fig3b untouched.
Published instrument: Dasari et al (2022) Supplementary Note 2 eqs (9)-(13).
Offsets fixed to separate in-sample Gaussian fits; no physical innovation claimed.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.optimize import linprog,least_squares
root=Path(__file__).resolve().parent
source=root.parent/'stuttgart_v11/calibration_data/Fig2bdata.csv'
raw=source.read_bytes()
assert hashlib.md5(raw).hexdigest()=='b56696a90f7e19eaf74e4efaf77371ce'
a=np.genfromtxt(source,delimiter=',',skip_header=1)
assert a.shape==(24,3)
t=a[:,0]/1000
prior,posterior=a[:,2],a[:,1] # source-Fig2 visual; original CSV headings reversed

def fit(y):
 def m(z):return z[0]+z[1]*np.exp(-.5*(t*z[2])**2)
 return least_squares(lambda z:m(z)-y,[.5,.5,1],
   bounds=([0,0,.0001],[2,2,20]),
   xtol=1e-13,ftol=1e-13,gtol=1e-13).x
b0,A0,s0=fit(prior); b1,A1,s1=fit(posterior)
assert abs(s0-2.5048587548)<.00001 and abs(s1-1.2823846266)<.00001
omega=np.linspace(0,12,321)
C=np.cos(np.outer(t,omega))
qp=np.cos(omega*.6/2)**2
qm=1-qp

def mat(delta,fidelity=1.0,post=True):
 w=(fidelity*qp+(1-fidelity)*qm)**4
 r=b0+A0*C-prior[:,None]
 allrows=[r-delta,-r-delta]
 if post:
  y=w[None,:]*(b1+A1*C-posterior[:,None])
  allrows += [y-delta*w[None,:],-y-delta*w[None,:]]
 return np.vstack(allrows)
def valid(delta,fidelity=1.0):
 H=mat(delta,fidelity)
 z=linprog(np.zeros(len(omega)),A_ub=H,b_ub=np.zeros(len(H)),
  A_eq=np.ones((1,len(omega))),b_eq=[1.],bounds=(0,None),method='highs')
 return z.success
tol={}
for f in (1.,.95):
 lo,hi=.06,.2
 assert valid(hi,f)
 for i in range(13):
  mid=(lo+hi)/2
  if valid(mid,f):hi=mid
  else:lo=mid
 tol[str(f)]=float(hi)
assert .10<tol['1.0']<.13

# Charnes-Cooper LP obtains two concrete nonnegative spectra giving extreme
# CONDITIONAL M---- FID predictions at 1.2 us. 0.12 is deliberately loose:
# NOT a confidence band and not an uncertainty estimate for the experiment.
epsilon=.12
H=mat(epsilon)
w=qm**4
objective=w*np.cos(omega*1.2)
eq=np.vstack([np.r_[w,0],np.r_[np.ones(len(omega)),-1]])
solutions=[]
for sign in (1,-1):
 z=linprog(np.r_[sign*objective,0],A_ub=np.c_[H,np.zeros(len(H))],
  b_ub=np.zeros(len(H)),A_eq=eq,b_eq=[1,0],
  bounds=[(0,None)]*len(omega)+[(0,200)],method='highs')
 assert z.success,z.message
 p=z.x[:-1]/z.x[-1]
 assert abs(sum(p)-1)<1e-6 and (H@p).max()<1e-5
 pp=b0+A0*(C@p)
 wp=qp**4
 po=b1+A1*(C@(p*wp))/(p@wp)
 assert max(abs(pp-prior))<epsilon+.00001
 assert max(abs(po-posterior))<epsilon+.00001
 nz=np.where(p>1e-7)[0]
 solutions.append({'future_M4minus_coherence_1p2us':float(objective@p/(w@p)),
  'M4minus_ideal_success_probability':float(w@p),
  'max_prior_calibration_error':float(max(abs(pp-prior))),
  'max_post_calibration_error':float(max(abs(po-posterior))),
  'support_omega_weight':[[float(omega[k]),float(p[k])] for k in nz]})
spread=solutions[1]['future_M4minus_coherence_1p2us']-solutions[0]['future_M4minus_coherence_1p2us']
assert spread>1.0
out={'status':'CONDITIONAL NEGATIVE IDENTIFIABILITY DIAGNOSTIC, NOT EMPIRICAL REFUTATION',
 'source':'DaRUS 3262 Figure2b + Supplementary Note2, original MD5 verified',
 'model_scope':'Noninteracting pure dephasing, positive symmetric spectrum 0..12 rad/us, tau 0.6us',
 'nuisance':'Fixed independent Gaussian FID fit offsets per condition; unknown optical and power broadening not included',
 'prior_fit':[float(b0),float(A0),float(s0)],'post_fit':[float(b1),float(A1),float(s1)],
 'best_uniform_absolute_point_error_approx':tol,
 'feasibility_tolerance_not_confidence_interval':epsilon,
 'unmeasured_minus_branch_endpoint_spectra':solutions,
 'conditional_future_coherence_spread':float(spread),
 'not_claimed':'Published full experimental-model refutation, measured error bars, new law or novel physics',
 'holdout':'Fig3b data sealed'}
(root/'identifiability_results.json').write_text(json.dumps(out,indent=2)+'\n')
print('IDENTIFIABILITY',json.dumps(out))
