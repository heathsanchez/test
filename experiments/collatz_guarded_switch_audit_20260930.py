import json, hashlib
N=3294206330938702138381104133963803
S=2**191*27
ks=(167,178,181)
ms=(401921098006060864059822585962556501,1287599767586799477097898430908365823,1448549738535149411735135734771911551)
qs=(111,119,121)
def step(n): return (3*n+1)//2 if n%2 else n//2
def val(n,p):
    assert n
    k=0
    while n%p==0: n//=p; k+=1
    return k
y=N;q=0;trace=[]
for k in range(182):
    c=3**q*(S//2**k)
    assert y>=N and c>=S, ('direct',k)
    if y%8==5: assert y>4*N and c>=4*S, ('quarter',k)
    if y%3==2: assert (2*y-1)//3>=N and 2*c>=3*S, ('predecessor',k)
    trace.append((y,q,c))
    q+=y%2;y=step(y)
slopes=[]
for k,m,q in zip(ks,ms,qs):
    assert trace[k][0]+1==4*m and trace[k][1]==q
    assert trace[k][2]%4==0
    slopes.append(trace[k][2]//4)
for t in (0,1,17):
    y=N+S*t
    for k in range(182):
        assert y==trace[k][0]+trace[k][2]*t
        y=step(y)
A1,B1,P1=6561,2443,2048
A2,B2,P2=9,1,8
assert P1*ms[1]==A1*ms[0]+B1
assert P2*ms[2]==A2*ms[1]+B2
assert P1*slopes[1]==A1*slopes[0]
assert P2*slopes[2]==A2*slopes[1]
d0=(P1-A1)*ms[0]-B1;d1=(P2-A2)*ms[1]-B2
c0=(P1-A1)*slopes[0];c1=(P2-A2)*slopes[1]
assert (val(d0,2),val(d0,3))==(12,0)
assert (val(d1,2),val(d1,3))==(10,2)
assert c0%2**13==0 and c0%3==0
assert c1%2**11==0 and c1%27==0
J=(P1-A1)*B2-(P2-A2)*B1
incoming=(P1-A1)*ms[1]-B1
outgoing=(P1-A1)*ms[2]-B1
assert P2*outgoing==A2*incoming+J
assert J==-2070 and val(J,2)==val(incoming,2)==val(outgoing,2)==1
result={'status':'GLOBAL_COLLATZ_UNKNOWN','scope':'Universal arithmetic ray; direct, quarter-splice and M1 guards through step 181 only. Not a no-OrdinaryExit theorem.','source':N,'period':S,'steps':ks,'owners':ms,'slopes':slopes,'own_rank_before':[1,0],'own_rank_after':[7,2],'switch_injection':J,'incoming_injection_orders':[1,1],'prefix_guard_steps':182,'literal_lift_checks':[0,1,17]}
canonical=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
result['certificate_sha256']=hashlib.sha256(canonical).hexdigest()
print(json.dumps(result,indent=2))
