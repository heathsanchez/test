#!/usr/bin/env python3
"""Stuttgart source-exact Fig2 ONLY; holdout Fig3b must remain sealed.
Published Figure 2 plots identify columns: prior = third, posterior = second,
despite reversed CSV headings; Fig2c horizontal units scale by 1/(2*pi).
Restricted Gaussian-bath quantum instrument, not full published simulation.
"""
from pathlib import Path
import json,hashlib,csv
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parent
def load(name,md5,n):
    b=(ROOT/'calibration_data'/name).read_bytes()
    assert hashlib.md5(b).hexdigest()==md5,"Original-file MD5 mismatch "+name
    rows=list(csv.reader(b.decode("utf-8-sig").splitlines()))
    assert len(rows)==n+1
    return np.array([[float(t) for t in row] for row in rows[1:]])
def fit(y,x,mode):
    fun=(lambda z:z[0]+z[1]*np.exp(-.5*(x*z[2])**2)) if mode=="fid" else (lambda z:z[0]-z[1]*np.exp(-.5*(x/z[2])**2))
    initial=[.5,.5,1.]
    z=least_squares(lambda z:fun(z)-y,initial,bounds=([0,0,.0001],[2,2,20]),xtol=1e-13,ftol=1e-13,gtol=1e-13).x
    return z,float(np.sqrt(np.mean((fun(z)-y)**2)))
def after(t,sigma,tau,minus=False):
    omega=np.linspace(-8*max(1,sigma),8*max(1,sigma),16001)
    p=np.exp(-.5*(omega/sigma)**2)
    p*=np.sin(.5*tau*omega)**8 if minus else np.cos(.5*tau*omega)**8
    p/=p.sum()
    return np.cos(np.outer(t,omega))@p
b=load('Fig2bdata.csv','b56696a90f7e19eaf74e4efaf77371ce',24)
c=load('Fig2cdata.csv','bd5cd2a1319e4013fb97d19bd211b5b5',45)
tb=b[:,0]/1000
xc=c[:,0]/(2*np.pi)
p,ep=fit(b[:,2],tb,"fid"); q,eq=fit(b[:,1],tb,"fid")
sp,esp=fit(c[:,2],xc,"line"); sq,esq=fit(c[:,1],xc,"line")
guessplus=p[0]+p[1]*after(tb,p[2],.6)
guessminus=p[0]+p[1]*after(tb,p[2],.6,True)
identity=p[0]+p[1]*np.exp(-.5*(tb*p[2])**2)
rmse=lambda v,w:float(np.sqrt(np.mean((v-w)**2)))
out={
 "kind":"Source-exact in-sample calibration and transferred restricted physical model; NO external holdout fit",
 "source":"DaRUS 10.18419/DARUS-3262 V2.1; published Fig2 visual",
 "fig2b_rows":24,"fig2c_rows":45,
 "warning":"Source Figure2 plotted prior=original third CSV column and posterior=second; original literal headings oppose figure. Figure2c xCSV/(2pi) matches plot.",
 "prior_fid":{"b":float(p[0]),"a":float(p[1]),"sigma_rad_per_us":float(p[2]),"RMSE":ep},
 "post_fid":{"b":float(q[0]),"a":float(q[1]),"sigma_rad_per_us":float(q[2]),"RMSE":eq},
 "fid_gaussian_exponent_coefficient_ratio_pre_over_post":float((p[2]/q[2])**2),
 "prior_odmr":{"b":float(sp[0]),"d":float(sp[1]),"sigma_MHz":float(sp[2]),"RMSE":esp},
 "post_odmr":{"b":float(sq[0]),"d":float(sq[1]),"sigma_MHz":float(sq[2]),"RMSE":esq},
 "odmr_width_ratio_post_over_prior":float(sq[2]/sp[2]),
 "restricted_quantum_Kplus_four_RMSE_on_after":rmse(guessplus,b[:,1]),
 "restricted_quantum_Kminus_four_RMSE_on_after":rmse(guessminus,b[:,1]),
 "unchanged_prior_RMSE_on_after":rmse(identity,b[:,1]),
 "data_status":"DaRUS ORIGINAL MD5 VERIFIED; Fig3b SEALED",
 "baseline_scope":"Centered Gaussian dephasing bath, tau=600ns, +/- projective measurement and same readout; NOT full published Hamiltonian, no independent photon-count error bars.",
 "candidate_status":"Cut re-description of this instrument exactly observationally EQUIVALENT; no physically distinct model specified"}
assert 3 < out["fid_gaussian_exponent_coefficient_ratio_pre_over_post"] < 4.5
assert out["odmr_width_ratio_post_over_prior"]<1
assert out["restricted_quantum_Kplus_four_RMSE_on_after"] < out["unchanged_prior_RMSE_on_after"]
dest=ROOT/"calibration_reproduction_results.json";dest.write_text(json.dumps(out,indent=2)+"\n")
print("CALIBRATION_REPRODUCTION",json.dumps(out,indent=2))
