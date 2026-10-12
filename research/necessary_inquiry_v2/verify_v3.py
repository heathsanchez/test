#!/usr/bin/env python3
"""Independent portable V2/V3 verification: the generator is immutable by hash."""
import hashlib,itertools,json,random,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import generator_v3 as G

P=pathlib.Path(__file__).resolve().parent
SOURCE_SHA='9b604161e65d4bc47b7600ee6231939937bc6a2cac102df8ea524909ae00f505'
assert hashlib.sha256((P/'generator_v3.py').read_bytes()).hexdigest()==SOURCE_SHA


def monomials(n,degree):
    return [sum(1<<i for i in c) for c in itertools.combinations(range(n),degree)]


def upto(n,degree):
    return [0]+[m for k in range(1,degree+1) for m in monomials(n,k)]


def table(n,terms):
    return [sum(int((x&t)==t)<<j for j,t in enumerate(terms)) for x in range(1<<n)]


def independent_world(n,terms,coefficients):
    vals=[0]*(1<<n)
    for j,t in enumerate(terms): vals[t]^=(coefficients>>j)&1
    for bit in range(n):
        for x in range(1<<n):
            if (x>>bit)&1: vals[x]^=vals[x^(1<<bit)]
    return vals


def sensor(row,values):
    r=0
    for x in G.members(row):r^=values[x]
    return r


def recover(rows,tf,outcomes,m):
    pivots={}
    for row,value in zip(rows,outcomes):
        a=G.image(row,tf);b=value
        while a:
            k=a.bit_length()-1
            if k in pivots:
                c,d=pivots[k];a^=c;b^=d
            else:
                pivots[k]=(a,b);break
        if not a and b:return None
    if len(pivots)!=m:return None
    answer=0
    for k in sorted(pivots):
        a,b=pivots[k]
        if b^G.parity(a&answer):answer|=1<<k
    return answer


def oldcuts(n):
    allbits=(1<<n)-1
    pairs=set();rows=[]
    for x in range(1,allbits):
        y=allbits^x
        pair=tuple(sorted((x,y)))
        if pair in pairs:continue
        pairs.add(pair)
        rows.append((1<<0)^(1<<x)^(1<<y)^(1<<allbits))
    return rows


def check(n,degree,old=False):
    nuisance=upto(n,degree-1)
    target=monomials(n,degree)
    nf=table(n,nuisance);tf=table(n,target)
    incumbent=oldcuts(n) if old else []
    result=G.synthesize(n,nf,tf,incumbent)
    selected=result['new_rows'];allrows=incumbent+selected
    m=len(target)
    assert result['resulting_rank']==m
    assert len(selected)==m-result['old_rank']==result['lower_bound']
    assert all(G.image(r,nf)==0 for r in allrows)
    assert all(r.bit_count()==(1<<degree) for r in selected)
    assert G.rank([G.image(r,tf) for r in allrows])==m
    assert G.rank([G.image(r,tf) for r in allrows[0:-1]])==m-1
    standard=[sum(1<<sub for sub in range(1<<n) if sub&t==sub) for t in target]
    assert all(G.image(r,tf)==(1<<j) for j,r in enumerate(standard))
    if not old:assert set(selected)==set(standard)
    rng=random.Random(20261012+(4000 if degree==4 else 1000 if degree==3 else 2000)*n)
    cases=256 if n==8 else 128
    for _ in range(cases):
        a=rng.getrandbits(len(nuisance));b=rng.getrandbits(m)
        f=independent_world(n,nuisance+target,a|(b<<len(nuisance)))
        observations=[sensor(r,f) for r in allrows]
        assert recover(allrows,tf,observations,m)==b
        assert all(ob==G.parity(G.image(row,tf)&b) for row,ob in zip(allrows,observations))
    if n==5:
        obs={sum(G.parity(G.image(r,tf)&b)<<i for i,r in enumerate(allrows)) for b in range(1<<m)}
        assert len(obs)==1<<m
    if not old and n>degree:
        outside=(1<<(degree+1))-1
        assert all(not sensor(row,[int((x&outside)==outside) for x in range(1<<n)]) for row in selected)
    unique_raw=len({x for row in selected for x in G.members(row)})
    return {'n':n,'degree':degree,'old_rank':result['old_rank'],
            'new_aggregate_sensors':len(selected),
            'required_new_binary_sensors':result['lower_bound'],
            'support_per_sensor':1<<degree,'replays':cases,
            'unique_raw_inputs_from_new_rows':unique_raw,
            'strong_stateless_interpolation_ties':True}


def main():
    rows=[]
    for n in (5,6,8):rows.append(check(n,2,old=True))
    for degree in (3,4):
        for n in (5,6,8):rows.append(check(n,degree))
    assert len(rows)==9
    print(json.dumps({'status':'PASS_EXACT_BOUNDED','source_sha':SOURCE_SHA,
                      'v2_unchanged_cubic_transfer':'REJECTED_FIXED_N_PLUS_1',
                      'rows':rows},sort_keys=True,indent=2))


if __name__=='__main__':main()
