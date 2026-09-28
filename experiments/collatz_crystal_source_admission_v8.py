#!/usr/bin/env python3
"""Crystal V8: source-admission quotient for the fixed-origin quarter-splice residual.

Protected consequence:
  for one fixed odd source n>1, eventually either x<n or
  x == 5 (mod 8) with x<=4n.

The V7 separator showed that local affine/bi-adic macro data is too coarse,
while the exact endpoint graph is acyclic on the declared boundary.  This V8
keeps the missing information without simply naming the source: every prefix
carries its exact source-admission cylinder

    n == rho (mod 2^D),   lo <= n <= hi,

where rho is forced by the cumulative affine identity
    2^D y = 3^R n + B,
and [lo,hi] is intersected with every source-relative band/excursion
inequality seen so far.  Since all moduli are powers of two, the cylinder is
equivalently an interval of lift indices n = rho + 2^D*q.

We compare:
  CONTROL          local affine return macro only;
  ADMISSION_COUNT  CONTROL + number/range-shape of lawful source lifts;
  ADMISSION        CONTROL + exact normalized lawful lift interval;
  CYLINDER         CONTROL + full cumulative source cylinder (diagnostic ceiling);
  ENDPOINT         exact endpoint baseline from V7.

A recurrent nonterminal kernel is an exact counterexample to the tested
quotient, not to Collatz.  Empty finite kernel is bounded discovery only.
"""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

def v2(z:int)->int:
    assert z>0
    return (z & -z).bit_length()-1

def odd_step(y:int):
    z=3*y+1
    a=v2(z)
    return z>>a,a

def ceil_div(a:int,b:int)->int:
    assert b>0
    return -((-a)//b)

class Admission:
    def __init__(self):
        self.R=0
        self.D=0
        self.B=0
        self.lo=3
        self.hi=None

    @property
    def A(self): return pow(3,self.R)
    @property
    def M(self): return 1<<self.D

    def _cap_hi(self,h:int):
        self.hi = h if self.hi is None else min(self.hi,h)

    def _raise_lo(self,l:int):
        self.lo=max(self.lo,l)

    def band(self):
        """Impose n <= y <= 4n for the current cumulative affine state."""
        A,M,B=self.A,self.M,self.B
        # y >= n: (A-M)n + B >= 0.
        if A<M:
            self._cap_hi(B//(M-A))
        # y <= 4n: B <= (4M-A)n.
        c=4*M-A
        if c<=0:
            raise AssertionError(("band upper impossible",self.R,self.D,self.B,c))
        self._raise_lo(ceil_div(B,c))

    def above(self):
        """Impose y > 4n for the current cumulative affine state."""
        A,M,B=self.A,self.M,self.B
        c=4*M-A
        if c>0:
            self._cap_hi((B-1)//c)
        elif B==0 and c==0:
            raise AssertionError(("strict above impossible",self.R,self.D,self.B))

    def step(self,a:int):
        # If 2^D y = 3^R n + B and 2^a y' = 3y+1, then
        # 2^(D+a)y' = 3^(R+1)n + (3B+2^D).
        self.B=3*self.B+(1<<self.D)
        self.R+=1
        self.D+=a

    def cylinder(self,n:int):
        M=self.M
        A=self.A
        rho=0 if M==1 else (-self.B*pow(A,-1,M))%M
        assert n%M==rho, (n,self.R,self.D,self.B,rho)
        klo=max(0,ceil_div(self.lo-rho,M))
        khi=None if self.hi is None else (self.hi-rho)//M
        k=(n-rho)//M
        assert klo<=k and (khi is None or k<=khi), (n,klo,k,khi,self.lo,self.hi,rho,M)
        count=None if khi is None else max(0,khi-klo+1)
        return rho,M,klo,khi,count,k

def kernel_rank(g):
    rev=collections.defaultdict(list)
    out={u:len(vs) for u,vs in g.items()}
    for u,vs in g.items():
        for v in vs: rev[v].append(u)
    q=collections.deque(u for u,d in out.items() if d==0)
    rank={u:0 for u in q}
    while q:
        u=q.popleft()
        for p in rev.get(u,()):
            if out[p]<=0: continue
            out[p]-=1
            rank[p]=max(rank.get(p,0),rank[u]+1)
            if out[p]==0:q.append(p)
    ker=[u for u,d in out.items() if d>0]
    return {
        "nodes":len(g),
        "edges":sum(len(vs) for vs in g.values()),
        "kernel_nodes":len(ker),
        "max_rank":max(rank.values(),default=0),
        "kernel_witness":repr(min(ker,key=repr))[:700] if ker else None,
    }

def count_class(c):
    if c is None:return "INF"
    if c<=1:return str(c)
    if c<=3:return "2-3"
    if c<=7:return "4-7"
    if c<=31:return "8-31"
    return "32+"

def run(limit:int,cap:int,out:Path):
    modes=("CONTROL","ADMISSION_COUNT","ADMISSION","CYLINDER","ENDPOINT")
    graphs={m:{} for m in modes}
    outcomes={m:collections.defaultdict(set) for m in modes}
    counts=collections.Counter()
    first_unresolved=[]
    max_events=(0,0)
    max_steps=(0,0)
    max_admission_count=0
    finite_cylinders=0
    singleton_cylinders=0
    zero_lift_events=0

    def add_node(g,k):g.setdefault(k,set())
    def add_edge(g,a,b):
        g.setdefault(a,set()).add(b);g.setdefault(b,set())

    for n in range(3,limit,2):
        counts["tested_odd_sources"]+=1
        y=n;steps=0;events=0
        adm=Admission()
        prev={m:None for m in modes}
        terminal=None
        while steps<cap:
            if y<n:
                terminal="DESCENT";break
            if y<=4*n and y%8==5:
                terminal="SPLICE";break
            if y>4*n:
                terminal="INTERNAL_ERROR";break

            # Exact current band admission.
            adm.band()
            y0=y
            r=d=b=0
            while steps<cap:
                y1,a=odd_step(y)
                b=3*b+(1<<d);r+=1;d+=a
                adm.step(a)
                y=y1;steps+=1
                if y<n:
                    break
                if y<=4*n:
                    adm.band()
                    break
                adm.above()

            rho,M,klo,khi,cnt,kactual=adm.cylinder(n)
            if cnt is not None:
                finite_cylinders+=1
                max_admission_count=max(max_admission_count,cnt)
                if cnt==1:singleton_cylinders+=1
            if kactual==0:zero_lift_events+=1

            local=(r,d,b)
            adm_count=(local,count_class(cnt), int(kactual==0),
                       None if khi is None else min(khi-klo,64))
            adm_state=(local,klo,khi)
            cyl=(local,adm.D,rho,klo,khi)
            keys={
                "CONTROL":local,
                "ADMISSION_COUNT":adm_count,
                "ADMISSION":adm_state,
                "CYLINDER":cyl,
                "ENDPOINT":y0,
            }
            for m,key in keys.items():
                add_node(graphs[m],key)
                if prev[m] is not None:add_edge(graphs[m],prev[m],key)
                prev[m]=key
            events+=1

            if y<n:
                terminal="DESCENT";break
            if y%8==5:
                terminal="SPLICE";break

        if terminal is None:terminal="CAP"
        counts["resolved_"+terminal]+=1
        if terminal in ("CAP","INTERNAL_ERROR") and len(first_unresolved)<20:
            first_unresolved.append([n,steps,y])
        for m,key in prev.items():
            if key is not None:outcomes[m][key].add(terminal)
        if events>max_events[0]:max_events=(events,n)
        if steps>max_steps[0]:max_steps=(steps,n)

    stats={m:kernel_rank(graphs[m]) for m in modes}
    unresolved=counts["resolved_CAP"]+counts["resolved_INTERNAL_ERROR"]
    if unresolved:
        verdict="BOUNDARY_UNRESOLVED"
    elif stats["CONTROL"]["kernel_nodes"]==0:
        verdict="CONTROL_ALREADY_ACYCLIC"
    elif stats["ADMISSION"]["kernel_nodes"]==0:
        verdict="SOURCE_ADMISSION_REMOVES_RECURRENT_KERNEL"
    elif stats["CYLINDER"]["kernel_nodes"]==0:
        verdict="FULL_CYLINDER_REQUIRED_ON_BOUNDARY"
    else:
        verdict="SOURCE_ADMISSION_STILL_RECURRENT"

    result={
      "schema":"COLLATZ_CRYSTAL_SOURCE_ADMISSION_V8",
      "boundary":{"limit":limit,"cap":cap},
      "counts":dict(sorted(counts.items())),
      "first_unresolved":first_unresolved,
      "record_band_events":{"count":max_events[0],"source":max_events[1]},
      "record_odd_steps":{"count":max_steps[0],"source":max_steps[1]},
      "admission":{
        "finite_event_cylinders":finite_cylinders,
        "singleton_event_cylinders":singleton_cylinders,
        "zero_actual_lift_events":zero_lift_events,
        "max_finite_admissible_sources_in_one_cylinder":max_admission_count,
        "law":"same natural source must remain in cumulative n=rho (mod 2^D), lo<=n<=hi cylinder forced by all band/excursion inequalities"
      },
      "representations":stats,
      "verdict":verdict,
      "interpretation":(
        "Tests the exact cross-depth source-admission distinction earned by V7. "
        "ADMISSION uses no raw source or endpoint identity; CYLINDER is the diagnostic ceiling."
      ),
      "universal_status":"UNKNOWN",
      "global_collatz":"UNKNOWN"
    }
    body=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["closure_certificate"]=hashlib.sha256(body.encode()).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=1<<19)
    ap.add_argument("--cap",type=int,default=4096)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.limit,a.cap,a.output)
