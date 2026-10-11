"""Stuttgart V14 source-checksummed inverse bath model; Figure3b is sealed."""
import hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares, linprog

source=Path(__file__).resolve().parent.parent/"stuttgart_v11/calibration_data/Fig2bdata.csv"
assert hashlib.md5(source.read_bytes()).hexdigest()=="b56696a90f7e19eaf74e4efaf77371ce"
rows=np.genfromtxt(source,delimiter=",",skip_header=1)
assert rows.shape==(24,3)
t=rows[:,0]/1000
prior,post=rows[:,2],rows[:,1]
def fit(y):
    z=least_squares(lambda z:z[0]+z[1]*np.exp(-.5*(z[2]*t)**2)-y,
        [.5,.5,1],bounds=([0,0,.0001],[2,2,20]))
    assert z.success
    return z.x
b0,a0,_=fit(prior)
b1,a1,_=fit(post)
omega=np.linspace(0,12,321)
C=np.cos(np.outer(t,omega))
w=np.cos(.3*omega)**8
pre=b0+a0*C-prior[:,None]
pos=w[None,:]*(b1+a1*C-post[:,None])
def eff(tau):return np.cos(omega*tau/2)**2
def grad(tau):return -omega*np.sin(omega*tau)/2
class Bath:
    def __init__(self,epsilon):
        self.eps=epsilon
        H=np.vstack([pre-epsilon,-pre-epsilon,pos-epsilon*w[None,:],-pos-epsilon*w[None,:]])
        self.H=H
        self.args=dict(A_ub=H,b_ub=np.zeros(len(H)),
            A_eq=np.ones((1,321)),b_eq=[1.],bounds=(0,None),method="highs")
    def ext(self,v):
        lo=linprog(v,**self.args);hi=linprog(-v,**self.args)
        assert lo.success and hi.success,(lo.message,hi.message)
        return float(v@lo.x),float(v@hi.x),lo.x,hi.x
    def width(self,tau):
        low,high,p,q=self.ext(eff(tau))
        return high-low,(low,high,p,q)
    def check(self,p):
        assert abs(sum(p)-1)<1e-7 and min(p)>=-1e-8
        assert max(self.H@p)<1e-6
        initial=b0+a0*(C@p)
        posterior=b1+a1*(C@(p*w))/(p@w)
        assert max(abs(initial-prior))<self.eps+1e-6
        assert max(abs(posterior-post))<self.eps+1e-6
        return {"prior_error":float(max(abs(initial-prior))),
          "post_error":float(max(abs(posterior-post))),
          "postselection_probability":float(p@w),
          "sparse_spectrum":[[float(omega[i]),float(p[i])] for i in range(321) if p[i]>1e-7]}
