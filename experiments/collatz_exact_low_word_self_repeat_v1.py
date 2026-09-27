#!/usr/bin/env python3
"""Exact symbolic self-repeat criterion for low valuation words w in {1,2}^r.

A word w with total valuation S has a unique odd residue rho mod 2^S
realizing it. U_w(x)=(3^r x+C)/2^S.
For x=rho+2^S t, self-repeat means U_w(x) == rho (mod 2^S), i.e.
3^r*t == K (mod 2^S), K=rho-(3^r*rho+C)/2^S.
Since 3^r is odd this congruence ALWAYS has one t mod 2^S. Thus every
finite word is self-repeatable 2-adically; positivity of the representative
and exact repeated valuation are then checked constructively.

We derive the least positive representative for N repeats by CRT-style
lifting, classify growth, and expose whether expanding blocks can repeat
arbitrarily many finite times.
"""
import itertools,json
def v2(n):
 c=0
 while n%2==0:c+=1;n//=2
 return c
def U(x):
 z=3*x+1;s=v2(z);return z>>s,s
def realizes(x,w):
 for s0 in w:
  x,s=U(x)
  if s!=s0:return False
 return True
def affine(w):
 A=1;C=0;D=1
 for s in w:A*=3;C=3*C+D;D*=1<<s
 return A,C,D
def residue(w):
 S=sum(w);M=1<<S
 # derive by brute only one period; audit lengths kept small
 for x in range(1,M,2):
  if realizes(x,w):return x
 raise AssertionError
def lift_repeat(w,N):
 A,C,D=affine(w);rho=residue(w);x=rho;mod=D
 # iteratively choose lift x+k*mod preserving previous and adding one block
 for blocks in range(2,N+1):
  found=None
  # next constraint adds S bits => k modulo D
  for k in range(D):
   z=x+k*mod
   if realizes(z,w*blocks):found=z;break
  if found is None:return None
  x=found;mod*=D
 return x
rows=[];examples=[]
for r in range(1,9):
 rr={"r":r,"expanding":0,"repeat2":0,"repeat3":0,"repeat4":0,"examples":[]}
 for w in itertools.product((1,2),repeat=r):
  A,C,D=affine(w)
  if A<=D:continue
  rr["expanding"]+=1
  vals=[]
  for N in (2,3,4):
   x=lift_repeat(w,N)
   vals.append(x)
   if x is not None:rr[f"repeat{N}"]+=1
  if all(x is not None for x in vals) and len(rr["examples"])<8:
   e={"word":"".join(map(str,w)),"A":A,"C":C,"D":D,"rho":residue(w),
      "repeat2":vals[0],"repeat3":vals[1],"repeat4":vals[2]}
   rr["examples"].append(e);examples.append(e)
 rows.append(rr)
print(json.dumps({"schema":"COLLATZ_EXACT_LOW_WORD_SELF_REPEAT_V1","rows":rows,
 "examples":examples[:20],
 "conclusion":"finite expanding low words can be lifted to repeat; acyclicity of expanding cylinders is false if repeat counts are nonzero",
 "global_collatz":"UNKNOWN"},indent=2))
