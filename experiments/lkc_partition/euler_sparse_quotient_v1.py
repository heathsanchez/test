#!/usr/bin/env python3
"""Sparse Euler-pentagonal integer quotient screen for SAIR Partition.

No Lean correctness proof in this probe. Do not submit.
Unlike the previously rejected n*sqrt(n) pentagonal recurrence, this
computes one sparse denominator and ONE large natural-number division.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

LEAN=r'''import Spec

namespace Submission

/-
EXPERIMENT ONLY: The generated source has no impl_correct. It is not
authorized for formal SAIR submission. Euler-pentagonal identity and
no-carry floor lemma must be independently formalized before promotion.
-/

/-- Sparse numerator and denominator contributions for
  x^0 - x^1 - x^2 + x^5 + x^7 - x^12 - x^15 + ...,
  reversed to integer place values in base B = 2^w. -/
def pentagonalParts (n w : Nat) : Nat → Nat → Nat → Nat → Nat × Nat
  | 0, _, pos, neg => (pos, neg)
  | fuel + 1, k, pos, neg =>
      let j := k + 1
      let g1 := j * (3 * j - 1) / 2
      if n < g1 then (pos, neg)
      else
        let g2 := j * (3 * j + 1) / 2
        let term1 := (1 : Nat) <<< (w * (n - g1))
        let term2 := if g2 ≤ n then (1 : Nat) <<< (w * (n - g2)) else 0
        if j % 2 = 0 then
          pentagonalParts n w fuel j (pos + term1 + term2) neg
        else
          pentagonalParts n w fuel j pos (neg + term1 + term2)

/--
Extract coefficient n of reciprocal Euler product by dividing two
positive integers. All n handled uniformly; no lookup table or
input-specific answer. Kernel correctness still unproved at this stage.
-/
def packedEuler (n : Nat) : Nat :=
  let w := n + 3
  let (pos, neg) := pentagonalParts n w (n + 1) 0 0 0
  let denom := (((1 : Nat) <<< (w * n)) + pos) - neg
  let num := (1 : Nat) <<< (w * (2 * n))
  let mask := ((1 : Nat) <<< w) - 1
  (num / denom) &&& mask

def impl : Nat → Nat := packedEuler

end Submission
'''


def reference(n:int)->int:
    vals=[0]*(n+1)
    vals[0]=1
    for k in range(1,n+1):
        for i in range(k,n+1):
            vals[i]+=vals[i-k]
    return vals[n]


def sparse(n:int,width:int|None=None)->tuple[int,int,int]:
    w=n+3 if width is None else width
    b=1<<w
    pos=neg=0
    cnt=0
    for j in range(1,n+2):
        g1=j*(3*j-1)//2
        if g1>n:break
        g2=j*(3*j+1)//2
        term=b**(n-g1)
        if g2<=n:term+=b**(n-g2)
        if j%2==0:pos+=term
        else:neg+=term
        cnt+=1
    d=b**n+pos-neg
    assert d>0
    res=(b**(2*n)//d)%b
    return res,cnt,(b**(2*n)).bit_length()


def self_test()->dict:
    m=[]
    samples={}
    for n in range(101):
        got,terms,bits=sparse(n)
        exp=reference(n)
        if got!=exp:m.append((n,exp,got))
        if n in (0,1,2,14,22,32,36,50,80,100):
            samples[str(n)]={"p":exp,"pentagonal_pairs":terms,"top_integer_bits":bits}
    assert not m,m
    bad=sparse(1,width=1)[0]
    assert bad!=reference(1)
    return {"status":"FINITE_EXACT_PASS","checked_n":"0..100","checks":101,
            "negative_base_width": {"n":1,"wrong_value":bad,"expected":reference(1)},
            "samples":samples,"universal_Lean_proof":False,
            "official_submission":False}


def main():
    record=self_test()
    p=OUT/"Submission_packed_euler_sparse_probe.lean"
    p.write_text(LEAN)
    q=OUT/"packed_euler_sparse_finite.json"
    q.write_text(json.dumps(record,indent=2)+"\n")
    print(f"GENERATED={p} bytes={p.stat().st_size} sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(json.dumps(record,indent=2))


if __name__=="__main__":
    main()
