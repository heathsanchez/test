#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations, product
import hashlib, json
import collatz_switch_state_rank_probe as sr

def vp(x,p):
    x=abs(x)
    if x==0:return None
    v=0
    while x%p==0:
        x//=p;v+=1
    return v

def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def odd_count_from_A(A):
    q=0
    while A>1 and A%3==0:
        A//=3;q+=1
    return q

def state_features(mstart,pulled,c,precision):
    num,den=pulled.numerator,pulled.denominator
    N=den*mstart-num
    assert N!=0
    assert N%(1<<precision)==0
    k=N//(1<<precision)
    assert k%2!=0
    v3=vp(k,3)
    core3=abs(k)//(3**v3)
    C=(1<<c["D"])-c["A"]
    return {
      "precision":precision,
      "k_abs":abs(k),
      "k_bits":abs(k).bit_length(),
      "v3k":v3,
      "core3_abs":core3,
      "core3_bits":core3.bit_length(),
      "den_bits":abs(den).bit_length(),
      "num_bits":abs(num).bit_length(),
      "height_bits":max(abs(num).bit_length(),abs(den).bit_length()),
      "D":c["D"],
      "q":odd_count_from_A(c["A"]),
      "C_bits":abs(C).bit_length(),
      "B_bits":abs(c["B"]).bit_length(),
    }

def collect(lo,hi,K=128):
    out=[];switches=0
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
      for anchor,seq in sr.returns(n,K).items():
        if not seq:continue
        mstart=seq[0][1]
        Abar,Bbar,Pbar=1,0,1
        prev=None
        for c,m0,m1,k0 in seq:
          local=centre(c)
          pulled=(Pbar*local-Bbar)/Abar
          diff=Fraction(mstart)-pulled
          assert diff!=0
          def v2z(z):
            z=abs(z)
            return (z&-z).bit_length()-1
          e=v2z(diff.numerator)-v2z(diff.denominator)
          assert e>=0
          f=state_features(mstart,pulled,c,e)
          cur={"pulled":pulled,"f":f,"c":c,"depth":k0}
          if prev is not None and pulled!=prev["pulled"]:
            switches+=1
            assert e>prev["f"]["precision"]
            loP,hiP=prev["f"]["precision"],e
            block=(mstart>>loP)&((1<<(hiP-loP))-1)
            if block==0:
              out.append({"source":n,"anchor":anchor,"mstart":mstart,
                          "old":prev["f"],"new":f,
                          "old_law":[prev["c"]["A"],prev["c"]["B"],1<<prev["c"]["D"],prev["c"]["D"]],
                          "new_law":[c["A"],c["B"],1<<c["D"],c["D"]],
                          "depth":[prev["depth"],k0]})
          if prev is None or pulled!=prev["pulled"]:
            prev=cur
          Abar,Bbar,Pbar=(c["A"]*Abar,c["A"]*Bbar+c["B"]*Pbar,(1<<c["D"])*Pbar)
    return switches,out

FEATURES=["k_abs","k_bits","v3k","core3_abs","core3_bits","den_bits","num_bits",
          "height_bits","D","q","C_bits","B_bits"]

def audit(rows):
    scalar={}
    for k in FEATURES:
      ds=[r["old"][k]-r["new"][k] for r in rows]
      scalar[k]={"strict_down":all(d>0 for d in ds),"strict_up":all(d<0 for d in ds),
                 "down":sum(d>0 for d in ds),"up":sum(d<0 for d in ds),"eq":sum(d==0 for d in ds)}
    lex=[]
    for a,b in combinations(FEATURES,2):
      for sa,sb in product((1,-1),repeat=2):
        if all((sa*r["old"][a],sb*r["old"][b])>(sa*r["new"][a],sb*r["new"][b]) for r in rows):
          lex.append({"features":[a,b],"signs":[sa,sb]})
    return {"rows":len(rows),"scalar":scalar,"lex":lex[:50]}

def main():
    ts,t=collect(3,8191)
    hs,h=collect(8193,32767)
    u=t+h
    result={"schema":"COLLATZ_ZERO_EXPOSURE_CARRY_TOURNAMENT_20260930",
            "train":{"switches":ts,**audit(t)},
            "heldout":{"switches":hs,**audit(h)},
            "union":audit(u),
            "first_rows":u[:20],
            "verdict":"SIMPLE_CARRY_RANK_FOUND" if audit(u)["lex"] or any(v["strict_down"] or v["strict_up"] for v in audit(u)["scalar"].values()) else "NO_SIMPLE_CARRY_RANK",
            "global_collatz":"UNKNOWN"}
    result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True,default=str))

if __name__=="__main__":main()
