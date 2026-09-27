#!/usr/bin/env python3
"""First-principles audit of the proposed low-valuation affine rank.

Enumerate low words w in {1,2}^r. For each word derive
 U_w(x)=(3^r*x+C)/2^S and its unique residue class modulo 2^S (if any)
that realizes exactly w. Classify multiplier 3^r/2^S and check whether
positive integer representatives can concatenate w with itself for several
blocks. This falsifies/qualifies any blanket contraction-rank claim.
"""
import itertools,json
def v2(n):
 c=0
 while n%2==0:c+=1;n//=2
 return c
def U(x):
 z=3*x+1;s=v2(z);return z>>s,s
def affine(word):
 A=1;C=0;D=1
 # represent x_i=(A*x+C)/D
 for s in word:
  A*=3;C=3*C+D;D*=2**s
 return A,C,D
def realizes(x,w):
 for s0 in w:
  x,s=U(x)
  if s!=s0:return False
 return True
rows=[]; counter=[]
for r in range(1,13):
 cls={"r":r,"words":2**r,"contracting":0,"neutral":0,"expanding":0,"repeatable_expanding":[]}
 for w in itertools.product((1,2),repeat=r):
  A,C,D=affine(w); typ="contracting" if A<D else ("neutral" if A==D else "expanding")
  cls[typ]+=1
  if typ=="expanding":
   # exact realizing residues are determined mod 2^S; brute one period (S<=24 here)
   mod=D; found=None
   for x in range(1,mod,2):
    if realizes(x,w):found=x;break
   if found is not None:
    # seek a positive representative realizing 4 repeats
    rep=None
    for k in range(64):
     x=found+k*mod
     if realizes(x,w*4):rep=x;break
    if rep is not None:
     item={"word":"".join(map(str,w)),"A":A,"C":C,"D":D,"residue":found,"repeat4":rep}
     cls["repeatable_expanding"].append(item)
     if len(counter)<20:counter.append(item)
 cls["repeatable_expanding"]=cls["repeatable_expanding"][:20];rows.append(cls)
print(json.dumps({"schema":"COLLATZ_LOW_WORD_AFFINE_RANK_AUDIT_V0","rows":rows,
 "first_repeatable_expanding":counter,
 "claim_tested":"indefinitely low-valuation behavior must contain a contracting affine block",
 "status":"FALSIFIED_IF_REPEATABLE_EXPANDING_NONEMPTY","global_collatz":"UNKNOWN"},indent=2))
