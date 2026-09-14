#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195

class Circuit:
    def __init__(self, solver):
        self.s=solver; self.nv=1; self.nc=1; self.T=1; self.F=-1
        self.s.add_clause([self.T])
    def var(self):
        self.nv+=1; return self.nv
    def add(self, clause):
        if self.T in clause: return
        clause=[x for x in clause if x != self.F]
        if not clause:
            self.s.add_clause([]); self.nc+=1; return
        self.s.add_clause(clause); self.nc+=1
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
    def lxor(self,a,b):
        if a==self.F:return b
        if b==self.F:return a
        if a==self.T:return -b
        if b==self.T:return -a
        if a==b:return self.F
        if a==-b:return self.T
        z=self.var()
        self.add([-a,-b,-z]); self.add([a,b,-z]); self.add([a,-b,z]); self.add([-a,b,z])
        return z
    def majority(self,a,b,c):
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
        self.add([a,b,-z]); self.add([a,c,-z]); self.add([b,c,-z])
        return z
    def mux(self,sel,a,b):
        if a==b:return a
        if sel==self.F:return a
        if sel==self.T:return b
        if a==self.F and b==self.T:return sel
        if a==self.T and b==self.F:return -sel
        z=self.var()
        self.add([sel,-a,z]); self.add([sel,a,-z]); self.add([-sel,-b,z]); self.add([-sel,b,-z])
        return z
    def add2(self,a,b,width):
        aa=a[:width]+[self.F]*max(0,width-len(a))
        bb=b[:width]+[self.F]*max(0,width-len(b))
        out=[]; carry=self.F
        for ai,bi in zip(aa,bb):
            x=self.lxor(ai,bi); out.append(self.lxor(x,carry)); carry=self.majority(ai,bi,carry)
        return out
    def add_const(self,a,value,width):
        b=[self.T if ((value>>i)&1) else self.F for i in range(width)]
        return self.add2(a,b,width)
    def uge_bits(self,a,b):
        width=max(len(a),len(b))
        aa=a+[self.F]*(width-len(a)); bb=b+[self.F]*(width-len(b))
        gt=self.F; eq=self.T
        for i in range(width-1,-1,-1):
            gt=self.lor(gt,self.land(eq,self.land(aa[i],-bb[i])))
            eq=self.land(eq,-self.lxor(aa[i],bb[i]))
        return self.lor(gt,eq)
    def uge_const(self,bits,c):
        cb=[self.T if ((c>>i)&1) else self.F for i in range(len(bits))]
        return self.uge_bits(bits,cb)
    def ule_const(self,bits,c):
        cb=[self.T if ((c>>i)&1) else self.F for i in range(len(bits))]
        return self.uge_bits(cb,bits)

def worst_widths(upper,horizon):
    m=upper; out=[max(1,m.bit_length())]
    for _ in range(horizon):
        m=(3*m+1)//2; out.append(max(1,m.bit_length()))
    return out

def replay(n,limit):
    x=n; peak=n
    for t in range(1,limit+1):
        x=(3*x+1)//2 if x&1 else x//2
        peak=max(peak,x)
        if x<n:return {"first_descent":t,"x":x,"peak":peak}
    return {"first_descent":None,"x":x,"peak":peak}

def cps(s,H):
    a=sorted({int(x) for x in s.split(",") if x.strip() and int(x)<=H})
    if H not in a:a.append(H)
    return a

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--horizon",type=int,required=True)
    ap.add_argument("--checkpoints",required=True)
    ap.add_argument("--out",default="even.json")
    A=ap.parse_args()
    K=A.bits
    assert 0<=A.lower<=A.upper<(1<<K)
    checkpoints=cps(A.checkpoints,A.horizon); cp=set(checkpoints)
    widths=worst_widths(A.upper,A.horizon); start=time.time(); results=[]
    with Cadical195() as solver:
        C=Circuit(solver)
        seed=[C.var() for _ in range(K)]
        C.add([C.uge_const(seed,A.lower)]); C.add([C.ule_const(seed,A.upper)])
        x=list(seed)
        print(f"EVEN_CNF_EXACT bits={K} lower={A.lower} upper={A.upper} horizon={A.horizon}",flush=True)
        for t in range(1,A.horizon+1):
            p=x[0]
            u=x[1:]
            # A first descent can only happen on an even input.  If p=0,
            # the next iterate is u=x/2 and must be >= seed.  Since seed has
            # K bits, any set bit of u above K-1 proves the comparison.
            low=u[:K]+[C.F]*max(0,K-len(u))
            low_ge=C.uge_bits(low,seed)
            high=u[K:] if len(u)>K else []
            C.add([p,low_ge]+high)

            ow=widths[t]
            uu=u[:ow]+[C.F]*max(0,ow-len(u))
            twice=([C.F]+u)[:ow]
            twice=twice+[C.F]*max(0,ow-len(twice))
            odd=C.add_const(C.add2(uu,twice,ow),2,ow)
            x=[C.mux(p,uu[i],odd[i]) for i in range(ow)]

            if t not in cp:continue
            s0=time.time(); ok=solver.solve(); sec=time.time()-s0
            row={"horizon":t,"status":"SAT" if ok else "UNSAT","solve_seconds":sec,
                 "vars":C.nv,"clauses":C.nc,"wall_seconds":time.time()-start}
            if ok:
                model=set(v for v in solver.get_model() if v>0)
                n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                rep=replay(n,t+1)
                assert A.lower<=n<=A.upper
                assert rep["first_descent"] is None or rep["first_descent"]>t,(n,t,rep)
                row["witness"]=n; row["replay"]=rep
            results.append(row); print("CHECK",json.dumps(row,separators=(",",":")),flush=True)
            if not ok:break
        summary={"kind":"exact_even_step_cnf_no_descent","bits":K,"lower":A.lower,"upper":A.upper,
                 "requested_horizon":A.horizon,"status":results[-1]["status"] if results else "NO_CHECK",
                 "results":results,"wall_seconds":time.time()-start}
        Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
        print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
