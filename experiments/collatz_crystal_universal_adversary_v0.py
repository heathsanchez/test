#!/usr/bin/env python3
"""Adversarial Crystal fixtures for universal Live-transition completeness.

These are exact arithmetic witnesses, not counterexamples to Collatz. They force
bounded future quotients to represent transitions that finite terminating source
corpora can omit.
"""
from collatz_crystal_future_quotient_v1 import compile_with_separators

def rows():
    # Abstract exact witnesses to source-relative one-step behavior.
    # eA: n=5,y=8 even and y<2n -> next 4<n => EXIT.
    # eB: n=5,y=10 even and y=2n -> next 5, non-descent locally.
    # eC: n=5,y=20 even and y>=2n -> next 10, still non-descent locally.
    # Odd witnesses distinguish v2(3y+1) behavior.
    raw=[
      ("eA",5,8,True,()),
      ("eB",5,10,False,("o5",)),
      ("eC",5,20,False,("eB",)),
      ("o5",5,5,False,("o8",)),
      ("o8",5,8,True,()),
    ]
    out=[]
    for i,n,y,ex,nxt in raw:
      z=3*y+1
      v2=(z&-z).bit_length()-1
      out.append({"id":i,"next":nxt,"exit":ex,
        "endpoint_parity":y%2,"lt2source":y<2*n,"lt4source":y<4*n,
        "odd_v2_3y1":v2 if y%2 else None})
    return out

def main():
    bank=["endpoint_parity","lt2source","lt4source","odd_v2_3y1"]
    out=compile_with_separators(rows(),[],bank)
    print(out)
if __name__=="__main__":main()
