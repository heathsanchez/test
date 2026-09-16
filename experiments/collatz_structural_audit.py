#!/usr/bin/env python3
"""Independent finite checks supporting the accompanying symbolic proofs."""
import json
from pathlib import Path


def T(n): return (3*n+1)//2 if n%2 else n//2


def main():
    checks=0
    for m in range(2,129):
        n=(1<<m)-1; x=n
        for j in range(1,m+1):
            assert x%2==1
            x=T(x)
            assert x==3**j*2**(m-j)-1 and x>n
            checks+=1
    # Replay the discovered transfer independently of compiler functions.
    residue=13822111; modulus=1<<27; A=129140163; B=217068515
    transfer=[]
    for q in (0,1,2,100,10**50):
        n=residue+modulus*q; x=n
        for _ in range(27): x=T(x)
        assert modulus*x==A*n+B and x<n
        transfer.append({'q':str(q),'n':str(n),'endpoint':str(x)})
    out={'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN',
         'all_odd_identity_checks':checks,'transfer_replays':transfer,
         'universal_proofs':'See COLLATZ_FORWARD_WITNESS_AUDIT.md; not formalized in Lean'}
    print(json.dumps(out,indent=2))


if __name__=='__main__': main()
