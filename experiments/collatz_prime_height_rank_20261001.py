import hashlib,json
N=3294206330938702138381104133963803
NAMES=['v2_fixed_defect','v3_fixed_defect','v2_owner_plus_one','v3_owner_plus_one','v2_endpoint_minus_one','v3_endpoint_minus_one','v2_source_gap','v3_source_gap','endpoint_bit_length','gap_bit_length','endpoint_source_quotient','h3_fixed_defect','h2_owner_plus_one','h3_owner_plus_one','h2_endpoint_minus_one','h3_endpoint_minus_one','h2_source_gap','h3_source_gap']
WEIGHTS={(175,178):40,(187,195):8,(220,225):183,(225,230):639,(230,237):199,(237,243):157,(243,247):309}
def val(x,p):
    x=abs(x);assert x;k=0
    while x%p==0:x//=p;k+=1
    return k
def height(x,p):
    x=abs(x);return (x//p**val(x,p)).bit_length()
def step(x):return (3*x+1)//2 if x%2 else x//2
def features(y):
    m=(y+1)//4;d=-4513*m-2443;g=y-N
    return [val(d,2),val(d,3),val(m+1,2),val(m+1,3),val(y-1,2),val(y-1,3),val(g,2),val(g,3),y.bit_length(),g.bit_length(),y//N,height(d,3),height(m+1,2),height(m+1,3),height(y-1,2),height(y-1,3),height(g,2),height(g,3)]
y=N;q=0;points=[]
for k in range(279):
    assert y>=N
    assert y%8!=5 or (y+1)//4>=N
    assert y%3!=2 or (2*y-1)//3>=N
    if k>=max(167,N.bit_length()) and y%8==3 and y>N:
        m=(y+1)//4;f=features(y)
        assert all(v>=0 for v in f)
        assert N<2**k
        points.append(dict(k=k,q=q,y=y,m=m,f=f))
    q+=y%2;y=step(y)
assert 0<y<N
edges=[]
for a,b in zip(points,points[1:]):
    pair=(a['k'],b['k'])
    if pair not in WEIGHTS:continue
    D=b['k']-a['k'];A=3**(b['q']-a['q']);P=2**D;B=P*b['m']-A*a['m']
    da=-4513*a['m']-2443;db=-4513*b['m']-2443;J=-4513*B-(P-A)*2443
    assert P*db==A*da+J
    gain=val(A*da+J,2)-val(da,2)
    assert b['f'][0]==a['f'][0]-D+gain
    edges.append(dict(weight=WEIGHTS[pair],start=a,end=b,D=D,A=A,B=B,J=J,gain=gain,delta=[v-u for u,v in zip(a['f'],b['f'])]))
assert len(edges)==7
aggregate=[sum(e['weight']*e['delta'][j] for e in edges) for j in range(18)]
assert aggregate==[2465,288,440,0,0,0,0,0,440,440,128548,0,0,0,440,464,440,440]
assert all(x>=0 for x in aggregate)
total_weight=sum(e['weight'] for e in edges)
assert total_weight==1535
payment_rhs=-total_weight-aggregate[0]
assert payment_rhs==-4000
JOINT_WEIGHTS={(167,175):23,(206,213):367,(213,220):419,(220,225):52,(225,230):85,(230,237):52,(243,247):10}
CELLS=[(0,1,2),(0,3,2),(2,1,1),(2,1,2),(2,3,1),(2,3,2)]
def phase(a):
    defect=-4513*a['m']-2443
    return (a['m']%3,(defect//2**a['f'][0])%4,(defect//3**a['f'][1])%3)
phase_edges=[]
for a,b in zip(points,points[1:]):
    pair=(a['k'],b['k'])
    if pair not in JOINT_WEIGHTS:continue
    assert phase(a) in CELLS and phase(b) in CELLS
    D=b['k']-a['k'];A=3**(b['q']-a['q']);P=2**D;B=P*b['m']-A*a['m']
    da=-4513*a['m']-2443;db=-4513*b['m']-2443;J=-4513*B-(P-A)*2443
    assert P*db==A*da+J
    gain=val(A*da+J,2)-val(da,2)
    assert b['f'][0]==a['f'][0]-D+gain
    phase_edges.append(dict(weight=JOINT_WEIGHTS[pair],start=a,end=b,D=D,A=A,B=B,J=J,gain=gain,delta=[v-u for u,v in zip(a['f'],b['f'])],phase_before=phase(a),phase_after=phase(b),phase_delta=[int(phase(b)==c)-int(phase(a)==c) for c in CELLS]))
assert len(phase_edges)==7
phase_base=[sum(e['weight']*e['delta'][j] for e in phase_edges) for j in range(18)]
phase_flow=[sum(e['weight']*e['phase_delta'][j] for e in phase_edges) for j in range(len(CELLS))]
assert phase_base==[0,0,0,0,0,0,0,0,33,33,41355,33,33,0,33,33,33,33]
assert phase_flow==[0]*6
phase_weight=sum(e['weight'] for e in phase_edges)
assert phase_weight==1008

# Original source already exits: this is an immediate-rank rejection, not a survivor.
result=dict(status='DECLARED_PRIME_HEIGHT_LINEAR_RANK_REJECTED',global_collatz='UNKNOWN',scope='18 nonnegative features; immediate decrease on seven source-coherent post-zero-tail anchor-2 returns; D/S/M1 prefix protection only',names=NAMES,source=N,edges=edges,weighted_delta=aggregate,strict_rank_rhs=-total_weight,fixed_reserve_payment_rhs=payment_rhs,first_direct_exit=279,exit_endpoint=y,ordinary_exit_complete_guard='UNPROVED',optimizer_in_verifier=False,phase_cells=CELLS,phase_edges=phase_edges,phase_weighted_delta=phase_base,phase_weighted_flow=phase_flow,phase_strict_rank_rhs=-phase_weight)
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(result,indent=2))
