#!/usr/bin/env python3
"""A second algorithmic phase: Euler sparse coefficient through 2-adic inversion.

Research-only Lean implementations, NO impl_correct and NO SAIR submission.
For E(B) = prod_{k=1}^n (1-B^k) mod B^(n+1), E(B) is odd, so
inv := E(B)^(-1) modulo B^(n+1) has packed partition coefficients.
Newton/Hensel lifting computes inv with O(log(bitwidth)) modular iterations:
x' = x * (2 - E*x) (mod 2^(2p)).

This is distinct from V1's large quotient, and it retains the same independent
finite partition-count oracle and declared source/verification boundaries.
"""
from __future__ import annotations
import hashlib,json,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

LEAN=r'''import Spec

namespace Submission

/-!
ALGORITHM SCREEN ONLY. No universal Lean proof is claimed.
The formal inverse and Euler/partition coefficient bridges are open.
-/

/-- Positive and negative coefficients of the sparse Euler product,
evaluated directly in base B. The constant coefficient 1 is added later. -/
def eulerLowParts (n w : Nat) : Nat → Nat → Nat → Nat → Nat × Nat
  | 0, _, pos, neg => (pos, neg)
  | fuel + 1, j, pos, neg =>
      let k := j + 1
      let g1 := k * (3 * k - 1) / 2
      if n < g1 then (pos, neg)
      else
        let g2 := k * (3 * k + 1) / 2
        let t1 := (1 : Nat) <<< (w * g1)
        let t2 := if g2 ≤ n then (1 : Nat) <<< (w * g2) else 0
        if k % 2 = 0 then
          eulerLowParts n w fuel k (pos + t1 + t2) neg
        else
          eulerLowParts n w fuel k pos (neg + t1 + t2)

/-- Newton inverse modulo increasing powers of 2, x=1 at precision 1. -/
def henselLift : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, x, _ => x
  | fuel + 1, euler, targetBits, x, precision =>
      if targetBits ≤ precision then x
      else
        let nextBits := min targetBits (precision * 2)
        let modulus := (1 : Nat) <<< nextBits
        let mask := modulus - 1
        let error := ((euler &&& mask) * x) &&& mask
        let correction := (modulus + 2 - error) &&& mask
        let x' := (x * correction) &&& mask
        henselLift fuel euler targetBits x' nextBits

def packedHensel (n : Nat) : Nat :=
  let w := __WIDTH__
  let bitCount := w * (n + 1)
  let modulus := (1 : Nat) <<< bitCount
  let mask := modulus - 1
  let (pos, neg) := eulerLowParts n w (n + 1) 0 0 0
  let euler := ((modulus + 1 + pos) - neg) &&& mask
  let inverse := henselLift (n + 16) euler bitCount 1 1
  (inverse >>> (w * n)) &&& (((1 : Nat) <<< w) - 1)

def impl : Nat → Nat := packedHensel

end Submission
'''

WIDTHS={
 "standard":"n + 3",
 "narrow":"min (Nat.shiftRight n 1 + 6) (Nat.shiftRight n 2 + 13)"
}

def reference(n:int)->int:
    a=[0]*(n+1)
    a[0]=1
    for k in range(1,n+1):
        for j in range(k,n+1):a[j]+=a[j-k]
    return a[n]

def inverse2(e:int,bits:int)->int:
    x=1;p=1
    while p<bits:
        p=min(bits,p*2)
        modulus=1<<p
        mask=modulus-1
        err=(e*x)&mask
        correction=(modulus+2-err)&mask
        x=(x*correction)&mask
    return x

def kernel_model(n:int,w:int)->tuple[int,int,int]:
    B=1<<w;bits=w*(n+1)
    M=1<<bits;mask=M-1
    pos=neg=0
    j=1
    while j*(3*j-1)//2<=n:
        a=j*(3*j-1)//2;b=j*(3*j+1)//2
        term=B**a+(B**b if b<=n else 0)
        if j%2==0:pos+=term
        else:neg+=term
        j+=1
    e=((M+1+pos)-neg)&mask
    assert e&1
    x=inverse2(e,bits)
    assert (e*x)&mask==1
    return (x>>(w*n))&(B-1),bits,j-1

def width(n:int,name:str)->int:
    if name=="standard": return n+3
    return min(n//2+6,n//4+13)

def main()->None:
    tested={}
    for name in WIDTHS:
        bad=[];samples={}
        for n in range(241):
            expected=reference(n)
            got,bits,pairs=kernel_model(n,width(n,name))
            if got!=expected:bad.append([n,expected,got])
            if n in (0,1,2,14,22,32,36,70,100,240):
                samples[str(n)]={"partition":expected,"got":got,"bits":bits,
                                  "pentagonal_pairs":pairs}
        assert not bad,{name:bad[:8]}
        source=LEAN.replace("__WIDTH__",WIDTHS[name])
        target=OUT/f"Submission_euler_hensel_{name}_probe.lean"
        target.write_text(source)
        tested[name]={"checks":241,"source_sha256":hashlib.sha256(source.encode()).hexdigest(),
                      "bytes":len(source.encode()),"samples":samples}
    assert kernel_model(2,1)[0]!=reference(2)
    result={"status":"FINITE_EXACT_PASS","domain":"0..240 inclusive",
            "independent_oracle":"partition row DP",
            "arms":tested,"negative_bad_width":True,
            "universal_Lean_theorem":False,"official_submission":False}
    (OUT/"euler_hensel_v1_finite.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
