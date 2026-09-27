#!/usr/bin/env python3
"""Proper Crystal protected-future corpus for actual Collatz source paths.

Protected outcome is Lean-aligned OrdinaryExit.  For finite exact corpus we
compute the lower-source reachable set by forward propagation from all smaller
sources, so lower merges are exact on the declared source/depth boundary.
The result is bounded evidence only.
"""
from collections import defaultdict
import json, argparse
from collatz_crystal_future_quotient_v1 import compile_with_separators

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def corpus(N,K):
    # reach[y] contains smaller/equal sources whose <=K-step future hits y.
    reach=defaultdict(set)
    paths={}
    for n in range(1,N+1):
        y=n; p=[y]
        for _ in range(K):
            y=T(y); p.append(y)
        paths[n]=p
        for y in p: reach[y].add(n)

    rows=[]
    for n in range(2,N+1):
        path=paths[n]
        for k,y in enumerate(path):
            terminal=y in (1,2)
            descent=0<y<n
            lower=any(0<p<n for p in reach[y])
            ex=terminal or descent or lower
            # Keep actual source/path identity only for raw occurrence construction.
            # Crystal base quotient starts with protected exit status alone.
            rid=(n,k)
            nxt=() if k==K else ((n,k+1),)
            rows.append({
              "id":rid,"next":nxt,"exit":ex,
              "source":n,"depth":k,"endpoint":y,
              "parity":y&1,"mod3":y%3,
              "source_bits":n.bit_length(),
              "endpoint_bits":y.bit_length(),
              "gap_sign":-1 if y<n else (0 if y==n else 1),
            })
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--N",type=int,default=8191); ap.add_argument("--K",type=int,default=256)
    a=ap.parse_args(); rows=corpus(a.N,a.K)
    # Separator bank deliberately excludes source/depth/endpoint identity.
    bank=["parity","mod3","source_bits","endpoint_bits","gap_sign"]
    out=compile_with_separators(rows,[],bank)
    out.update({"schema":"COLLATZ_CRYSTAL_ORDINARY_EXIT_KERNEL_V0","N":a.N,"K":a.K,
                "rows":len(rows),"claim_boundary":"bounded actual source paths; lower merges exact only within source<=N and forward depth<=K; global Collatz UNKNOWN"})
    print(json.dumps(out,indent=2,default=repr))
if __name__=="__main__": main()

# qualification trigger after workflow installation
