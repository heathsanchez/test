#!/usr/bin/env python3
import argparse, json, math, time
from pathlib import Path
from pysat.solvers import Cadical195

class C:
    def __init__(self,s):
        self.s=s; self.nv=1; self.nc=1; self.T=1; self.F=-1
        s.add_clause([1])
    def var(self):
        self.nv+=1; return self.nv
    def add(self,cl):
        if self.T in cl: return
        cl=[x for x in cl if x!=self.F]
        self.s.add_clause(cl); self.nc+=1
    def land(self,a,b):
        if a==self.F or b==self.F:return self.F
        if a==self.T:return b
        if b==self.T:return a
        if a==b:return a
        if a==-b:return self.F
        z=self.var(); self.add([-a,-b,z]); self.add([a,-z]); self.add([b,-z]); return z
    def lor(self,a,b):
        if a==self.T or b==self.T:return self.T
        if a==self.F:return b
        if b==self.F:return a
        if a==b:return a
        if a==-b:return self.T
        z=self.var(); self.add([a,b,-z]); self.add([-a,z]); self.add([-b,z]); return z
    def xor(self,a,b):
        if a==self.F:return b
        if b==self.F:return a
        if a==self.T:return -b
        if b==self.T:return -a
        if a==b:return self.F
        if a==-b:return self.T
        z=self.var()
        self.add([-a,-b,-z]); self.add([a,b,-z]); self.add([a,-b,z]); self.add([-a,b,z])
        return z
    def maj(self,a,b,c):
        if a==self.T:return self.lor(b,c)
        if b==self.T:return self.lor(a,c)
        if c==self.T:return self.lor(a,b)
        if a==self.F:return self.land(b,c)
        if b==self.F:return self.land(a,c)
        if c==self.F:return self.land(a,b)
        if a==b or a==c:return a
        if b==c:return b
        if a==-b:return c
        if a==-c:return b
        if b==-c:return a
        z=self.var()
        self.add([-a,-b,z]); self.add([-a,-c,z]); self.add([-b,-c,z])
        self.add([a,b,-z]); self.add([a,c,-z]); self.add([b,c,-z]); return z
    def mux(self,s,a,b): # s ? b : a
        if a==b:return a
        if s==self.F:return a
        if s==self.T:return b
        if a==self.F and b==self.T:return s
        if a==self.T and b==self.F:return -s
        z=self.var()
        self.add([s,-a,z]); self.add([s,a,-z]); self.add([-s,-b,z]); self.add([-s,b,-z])
        return z
    def add2(self,a,b,w):
        aa=a[:w]+[self.F]*max(0,w-len(a)); bb=b[:w]+[self.F]*max(0,w-len(b))
        out=[]; carry=self.F
        for ai,bi in zip(aa,bb):
            x=self.xor(ai,bi); out.append(self.xor(x,carry)); carry=self.maj(ai,bi,carry)
        return out
    def add_const(self,a,k,w):
        b=[self.T if ((k>>i)&1) else self.F for i in range(w)]
        return self.add2(a,b,w)
    def uge_const(self,bits,k):
        gt=self.F; eq=self.T
        for i in range(len(bits)-1,-1,-1):
            xi=bits[i]; bi=(k>>i)&1
            if bi:
                eq=self.land(eq,xi)
            else:
                gt=self.lor(gt,self.land(eq,xi)); eq=self.land(eq,-xi)
        return self.lor(gt,eq)
    def ule_const(self,bits,k):
        lt=self.F; eq=self.T
        for i in range(len(bits)-1,-1,-1):
            xi=bits[i]; bi=(k>>i)&1
            if bi:
                lt=self.lor(lt,self.land(eq,-xi)); eq=self.land(eq,xi)
            else:
                eq=self.land(eq,-xi)
        return self.lor(lt,eq)
    def inc_if(self,bits,cond):
        out=[]; carry=cond
        for x in bits:
            out.append(self.xor(x,carry))
            carry=self.land(x,carry)
        return out

def req_odds(H):
    out=[0]*(H+1); q=0; p3=1
    for t in range(1,H+1):
        p2=1<<t
        while p3<p2:
            q+=1; p3*=3
        out[t]=q
    return out

def worst_width(U,H):
    x=U
    m=x
    for _ in range(H):
        x=(3*x+1)//2
        if x>m:m=x
    return m.bit_length()+1

def replay(n,limit):
    x=n; q=0; fc=None; fd=None; peak=n
    for t in range(1,limit+1):
        if x&1:
            q+=1; x=(3*x+1)//2
        else:
            x//=2
        peak=max(peak,x)
        if fc is None and pow(3,q)<(1<<t): fc=t
        if fd is None and x<n: fd=t
        if fc is not None and fd is not None: break
    return {"first_contract":fc,"first_descent":fd,"stopped_at":t,"x":x,"peak":peak,"q":q}

def checkpoints(s,H):
    xs=sorted({int(x) for x in s.split(",") if x.strip() and int(x)<=H})
    if H not in xs: xs.append(H)
    return xs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--horizon",type=int,required=True)
    ap.add_argument("--checkpoints",required=True)
    ap.add_argument("--replay-limit",type=int,default=5000)
    ap.add_argument("--out",default="coefficient.json")
    A=ap.parse_args()
    K=A.bits; H=A.horizon
    assert 0<=A.lower<=A.upper<(1<<K)
    cps=checkpoints(A.checkpoints,H); cp=set(cps); req=req_odds(H)
    W=worst_width(A.upper,H); QW=(H+1).bit_length()+1
    start=time.time(); rows=[]
    with Cadical195() as solver:
        c=C(solver)
        seed=[c.var() for _ in range(K)]
        c.add([c.uge_const(seed,A.lower)]); c.add([c.ule_const(seed,A.upper)])
        x=seed+[c.F]*(W-K)
        qbits=[c.F]*QW
        print(f"COEFF_CNF bits={K} lo={A.lower} hi={A.upper} H={H} W={W}",flush=True)
        for t in range(1,H+1):
            odd=x[0]
            u=x[1:]+[c.F]
            # odd shortcut: for x=2u+1, T(x)=3u+2
            twice=[c.F]+u[:-1]
            oddx=c.add_const(c.add2(u,twice,W),2,W)
            x=[c.mux(odd,u[i],oddx[i]) for i in range(W)]
            qbits=c.inc_if(qbits,odd)
            c.add([c.uge_const(qbits,req[t])])
            if t not in cp: continue
            s0=time.time(); ok=solver.solve(); sec=time.time()-s0
            row={"horizon":t,"status":"SAT" if ok else "UNSAT","solve_seconds":sec,
                 "vars":c.nv,"clauses":c.nc,"wall_seconds":time.time()-start}
            if ok:
                model=set(v for v in solver.get_model() if v>0)
                n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                rep=replay(n,A.replay_limit)
                assert A.lower<=n<=A.upper
                assert rep["first_contract"] is None or rep["first_contract"]>t,(n,t,rep)
                row["witness"]=n; row["replay"]=rep
            rows.append(row); print("CHECK",json.dumps(row,separators=(",",":")),flush=True)
            if not ok: break
        summary={"kind":"exact_coefficient_persistence_cnf","bits":K,"lower":A.lower,"upper":A.upper,
                 "requested_horizon":H,"width":W,"results":rows,
                 "status":rows[-1]["status"] if rows else "NO_CHECK","wall_seconds":time.time()-start}
        Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
        print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__": main()
