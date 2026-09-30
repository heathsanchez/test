import json
from fractions import Fraction
import hashlib
N=3294206330938702138381104133963803

def val(x,p):
    assert x != 0
    x=abs(x);k=0
    while x%p==0:x//=p;k+=1
    return k

def step(x):return (3*x+1)//2 if x%2 else x//2

def features(y,n):
    m=(y+1)//4;d=-4513*m-2443
    return [val(d,3),val(m+1,2),val(m+1,3),val(y-1,2),val(y-1,3),val(y-n,2),val(y-n,3),y.bit_length(),(y-n).bit_length(),y//n]

names=['v3_fixed_defect','v2_owner_plus_one','v3_owner_plus_one','v2_endpoint_minus_one','v3_endpoint_minus_one','v2_source_gap','v3_source_gap','endpoint_bit_length','gap_bit_length','endpoint_source_quotient']
y=N;q=0;pts=[]
for k in range(279):
    assert y>=N
    assert y%8!=5 or (y+1)//4>=N
    assert y%3!=2 or (2*y-1)//3>=N
    if k>=167 and y%8==3:
        m=(y+1)//4
        pts.append({'k':k,'q':q,'y':y,'m':m,'reserve':val(-4513*m-2443,2),'features':features(y,N)})
    q+=y%2;y=step(y)
edges=[]
for a,b in zip(pts,pts[1:]):
    D=b['k']-a['k'];A=3**(b['q']-a['q']);P=2**D;B=P*b['m']-A*a['m']
    x=-4513*a['m']-2443;y=-4513*b['m']-2443;J=-4513*B-(P-A)*2443
    assert P*y==A*x+J
    gain=val(A*x+J,2)-val(x,2)
    assert b['reserve']==a['reserve']-D+gain
    edges.append({'from':a['k'],'to':b['k'],'feature_delta':[y-x for x,y in zip(a['features'],b['features'])],'reserve_delta':b['reserve']-a['reserve'],'D':D,'A':A,'B':B,'J':J,'gain':gain})
# The optimizer proposed these integers; only exact arithmetic is authoritative.
C=[e['feature_delta'] for e in edges];rhs=[-1-e['reserve_delta'] for e in edges]
chosen={(167,175):16,(175,178):10,(220,225):21,(225,230):235,(230,237):26}
weights=[Fraction(chosen.get((e['from'],e['to']),0),308) for e in edges]
assert all(x>=0 for x in weights) and sum(weights)==1
lhs=[sum(w*row[j] for w,row in zip(weights,C)) for j in range(len(names))]
right=sum(w*b for w,b in zip(weights,rhs))
assert all(x>=0 for x in lhs) and right<0
certificate={'weights':[{'edge':[e['from'],e['to']],'weight':str(w)} for e,w in zip(edges,weights) if w],'summed_feature_delta':list(map(str,lhs)),'summed_rhs':str(right)}
# Independent literal replay of finite plateau instances; universal law is in Lean.
for length in (0,1,2,8,32,128):
 for z in (1,2,5,17):
  original=864*8**length*z-5
  current=original
  for i in range(length+1):
   expected=864*9**i*8**(length-i)*z-5
   assert current==expected
   m=(current+1)//4;delta=-4513*m-2443
   assert (val(delta,2),val(delta,3))==(1,2)
   if i<length:
    for _ in range(3):
     assert current>=original
     assert current%8!=5
     assert current%3!=2 or (2*current-1)//3>=original
     current=step(current)
result={'status':'GLOBAL_COLLATZ_UNKNOWN','scope':'Immediate payment on the declared actual anchor-2 returns; D/S/M1 protection only; eventual progress and full no-OrdinaryExit remain open','source':N,'feature_names':names,'points':pts,'edges':edges,'certificate':certificate,'plateau_literal_lengths':[0,1,2,8,32,128]}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(result,indent=2))
