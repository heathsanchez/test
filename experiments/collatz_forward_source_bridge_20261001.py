import json,hashlib
N=3294206330938702138381104133963803
S=2**191*27
def step(x):return (3*x+1)//2 if x%2 else x//2
x=N;q=0
for k in range(279):
 assert x>=N,(k,x)
 q+=x%2;x=step(x)
assert x==3189501699593601134635187603066116 and q==176 and 0<x<N
assert 3**q<2**279
for u in [0,1,2,17]:
 n=N+2**279*27*u;y=n
 for k in range(279):y=step(y)
 assert y==x+3**176*27*u and 0<y<n
 assert n==N+S*(2**88*u)
result={'status':'GLOBAL_COLLATZ_UNKNOWN','source':N,'source_ray_period':S,'first_direct_exit':279,'endpoint':x,'odd_count':q,'qualified_ray_parameters':'t=2^88*u, u natural','all_ray_coverage':'UNPROVED','exit_literal_lifts':[0,1,2,17],'start_predecessor_rule':'For every k, if 3 divides y and T^k(p)=y, then p=2^k*y. Universal rule is proved in Lean.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(result,indent=2))
