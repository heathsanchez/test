"""V116: arbitrary finite no-cap prefixes with high endpoint anchors.

For r>=1 and B>=3, choose q>=4 such that
9^r*q = 4 (mod 2^B) and (8^r*q-5) mod 3 != 2.
Then n=8^r*q-5 follows r actual 110 parity blocks,
T^(3r)(n)=9^r*q-5, and v2(n+1)=2.
No k<=3r makes T^k(n) a direct descent or a
2 mod 3 endpoint with inverse-odd predecessor < original n.
This is a finite-horizon negative control, NOT an infinite
nonterminating positive source or Collatz QED.
"""
import json
import hashlib

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def v2(x):
    assert x>0
    return (x & -x).bit_length()-1

def witness(r,B):
    assert r>=1 and B>=3
    m=1<<B
    q=(4*pow(pow(9,r,m),-1,m))%m
    while q<4: q+=m
    for _ in range(3):
        if (8**r*q-5)%3!=2: break
        q+=m
    else:
        raise AssertionError("unexpected CRT residue obstruction")
    n=8**r*q-5
    assert n>1 and n%3!=2 and n%8==3 and v2(n+1)==2
    x=n
    for i in range(r):
        x1=T(x); x2=T(x1); x3=T(x2)
        assert (x%2,x1%2,x2%2)==(1,1,0)
        assert 8*x3==9*x+5 and x3>x
        assert x1>x and x2>x1
        assert x1%3==2 and x2%3==2 and x3%3==1
        for y in (x1,x2,x3):
            assert y>=n
            if y%3==2:
                assert (2*y-1)%3==0
                assert (2*y-1)//3 >= n
        x=x3
        assert x==9**(i+1)*8**(r-i-1)*q-5
    assert x==9**r*q-5 and (x+1)%m==0
    return dict(r=r,B=B,n=n,q=q,last=x,
                source_v2=v2(n+1),endpoint_v2=v2(x+1))

def main():
    rows=[witness(r,B) for r in range(1,21)
          for B in (3,4,5,8,12,20,40,80)]
    assert len(rows)==160
    result=dict(schema="COLLATZ_V116_FINITE_HORIZON_BARRIER",
      status="BOUNDED_EXACT_EXECUTABLE",qed=False,
      global_collatz="UNKNOWN",all_checks_passed=True,
      checks=len(rows),max_horizon=60,max_precision_target=80,
      no_infinite_source_witness=True,
      example_rows=[x for x in rows
        if (x["r"],x["B"]) in ((1,5),(2,12),(5,20),(10,40),(20,80))])
    raw=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["certificate_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
