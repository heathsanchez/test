#!/usr/bin/env python3
"""Exact periodic low-word fixed-point classification."""
import itertools,json,math
def v2(n):
 c=0
 while n%2==0:c+=1;n//=2
 return c
def U(x):
 z=3*x+1;s=v2(z);return z>>s,s
def realizes(x,w):
 if x<=0 or x%2==0:return False
 for s0 in w:
  x,s=U(x)
  if s!=s0:return False
 return True
def affine(w):
 A=1;C=0;D=1
 for s in w:A*=3;C=3*C+D;D*=1<<s
 return A,C,D
rows=[];fixed=[]
for r in range(1,17):
 exp=con=integ=0; fs=[]
 for w in itertools.product((1,2),repeat=r):
  A,C,D=affine(w)
  if A>D:exp+=1;continue
  con+=1
  den=D-A
  if C%den==0:
   x=C//den
   if realizes(x,w) and x>0:
    integ+=1
    item={"word":"".join(map(str,w)),"x":x,"A":A,"C":C,"D":D}
    fs.append(item)
    if item not in fixed:fixed.append(item)
 rows.append({"r":r,"expanding_words":exp,"contracting_words":con,
              "positive_integral_exact_fixed":integ,"fixed":fs[:20]})
print(json.dumps({"schema":"COLLATZ_PERIODIC_LOW_WORD_FIXED_POINTS_V0","rows":rows,
 "distinct_fixed":fixed[:100],
 "theorem_shape":"expanding periodic low word impossible over positive integers since (D-A)x=C>0 has D-A<0",
 "global_collatz":"UNKNOWN"},indent=2))
