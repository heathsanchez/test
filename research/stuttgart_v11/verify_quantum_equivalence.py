#!/usr/bin/env python3
"""Finite-dimensional exact-structure quantum equivalence gate; not experiment."""
from pathlib import Path
import json,itertools
import numpy as np
rng=np.random.default_rng(20261012)
omega=np.array([-2.7,-1.1,.8,3.2]);d=len(omega);tau=.69;t=.83
a=np.diag(np.exp(-.5j*tau*omega));b=np.diag(np.exp(+.5j*tau*omega))
U=np.block([[a,np.zeros((d,d))],[np.zeros((d,d)),b]])
X=rng.normal(size=(d,d))+1j*rng.normal(size=(d,d))
rho=X@X.conj().T;rho/=np.trace(rho)
k={'+':np.diag(np.cos(.5*tau*omega)),'-':np.diag(-1j*np.sin(.5*tau*omega))}
W,_=np.linalg.qr(rng.normal(size=(d,d))+1j*rng.normal(size=(d,d)))
rot={x:W@v@W.conj().T for x,v in k.items()}
rhor=W@rho@W.conj().T
E=np.diag(np.exp(-1j*omega*t));Er=W@E@W.conj().T
pr=np.ones((2,2),complex)/2
projs={'+':np.array([1,1])/np.sqrt(2),'-':np.array([1,-1])/np.sqrt(2)}
def full(s,c):
    z=U@np.kron(pr,s)@U.conj().T
    return np.einsum('a,aibj,b->ij',projs[c],z.reshape(2,d,2,d),projs[c])
def branch(s,record,form):
    for c in record:
        s=(full(s,c) if form=='joint' else (k if form=='kraus' else rot)[c]@s@(k if form=='kraus' else rot)[c].conj().T)
    return s
err=0.;fiderr=0.;bad=0
pp=float(np.trace(k['+']@rho@k['+'].conj().T).real)
for n in range(1,6):
    norm=0
    for record in itertools.product('+-',repeat=n):
        x=branch(rho,record,'joint')
        y=branch(rho,record,'kraus')
        z=branch(rhor,record,'rot')
        a1,a2,a3=[float(np.trace(v).real) for v in [x,y,z]]
        err=max(err,abs(a1-a2),abs(a1-a3))
        norm+=a1
        c1=np.trace(x@E)/a1;c2=np.trace(y@E)/a2;c3=np.trace(z@Er)/a3
        fiderr=max(fiderr,abs(c1-c2),abs(c1-c3))
        passive=pp**record.count('+')*(1-pp)**record.count('-')
        bad+=abs(a1-passive)>1e-6
    assert abs(norm-1)<1e-12
assert err<1e-12 and fiderr<1e-12 and bad>0
out={"records":62,"max_probability_discrepancy":float(err),"max_conditioned_fid_discrepancy":float(fiderr),"passive_mismatch_count":bad,"decision":"EQUIVALENT; classical passive product not scientifically adequate","scope":"4D exact-structure instrument numerical checks, not external physical validation"}
(Path(__file__).parent/"quantum_equivalence_results.json").write_text(json.dumps(out,indent=2)+"\n")
print("QUANTUM_EQUIVALENCE",json.dumps(out))
