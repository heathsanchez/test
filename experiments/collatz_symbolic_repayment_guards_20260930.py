"""Symbolic guards extracted from the pinned V53 corpus. No global claim.

Each emitted guard is exact integer arithmetic conditional on the composed
affine relation. Observed coverage does not prove universal word admission.
"""
from contextlib import redirect_stdout
from collections import defaultdict, Counter
from math import gcd
import io, json, hashlib

print('Replaying pinned V53', flush=True)
with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v
assert v.result['certificate_sha256']=='16bc1fafea228c441faa11cd5c19b14a82df7739dba89673fc18127dcfceaecc'

def compose(a,b):
    A,B,P=a; C,E,Q=b
    return C*A,C*B+E*P,Q*P

def shortcut(n):
    return (3*n+1)//2 if n&1 else n//2

def replay(m,anchor,steps):
    x=(1<<anchor)*m-1
    bits=[]
    for _ in range(steps):
        bits.append(x&1); x=shortcut(x)
    return x,tuple(bits)

groups=defaultdict(list)
for z in v.rows: groups[z['t'],z['anchor']].append(z)
stats=Counter(); bank={}; observed=[]; examples=[]; residual_starts=[]
for rs in groups.values():
    rs.sort(key=lambda z:(z['k0'],z['k1']))
    for i,start in enumerate(rs):
        if not start['residual']: continue
        residual_starts.append(start)
        stats['residual_starts']+=1
        total=(1,0,1); first_local=None; found=None
        for j,z in enumerate(rs[i:]):
            if j: assert z['m0']==rs[i+j-1]['m1']
            total=compose(total,(z['A'],z['B'],z['P']))
            A,B,P=total
            assert P*z['m1']==A*start['m0']+B
            if first_local is None and z['progress']: first_local=j
            if z['m1']<start['m0']:
                assert P>A
                floor=B//(P-A)+1
                assert (P-A)*floor>B and (P-A)*(floor-1)<=B
                assert start['m0']>=floor
                D=P.bit_length()-1
                assert P==1<<D and D==z['k1']-start['k0']
                modulus=2*P
                rho=((P-B)*pow(A,-1,modulus))%modulus
                assert start['m0']%modulus==rho
                minimum=rho if rho else modulus
                key=(start['anchor'],A,B,P,rho)
                stats['macro_repays']+=1
                stats['macro_live_floor_repays']+=floor<=start['L']
                stats['whole_positive_owner_cylinder_repays']+=minimum>=floor
                stats['overshoot_then_repays']+=first_local is not None and first_local<j
                final,bits=replay(start['m0'],start['anchor'],D)
                assert final==(1<<start['anchor'])*z['m1']-1
                # Independent raw shortcut replay of upward lifts in the exact
                # owner cylinder; not asserted to preserve source/no-exit.
                for h in (1,2,17):
                    lifted=start['m0']+modulus*h
                    out,bitlift=replay(lifted,start['anchor'],D)
                    assert bits==bitlift
                    assert (out+1)%(1<<start['anchor'])==0
                    mout=(out+1)>>start['anchor']
                    assert P*mout==A*lifted+B and mout<lifted
                bank.setdefault(key,{'anchor':start['anchor'],'A':str(A),'B':str(B),'P':str(P),
                    'D':D,'rho':str(rho),'modulus':str(modulus),'floor':str(floor),
                    'min_admitted_owner':str(minimum),'whole_cylinder':minimum>=floor,
                    'v45_floor_suffices':floor<=start['L'],'observations':0,
                    'word':''.join(map(str,bits))})['observations']+=1
                observed.append((start,key,j+1))
                if first_local is not None and first_local<j and len(examples)<3:
                    examples.append({'source':str(start['source']),'anchor':start['anchor'],
                       'root_depth':start['k0'],'repayment_depth':z['k1'],
                       'returns':j+1,'start_owner':str(start['m0']),'end_owner':str(z['m1']),
                       'guard':bank[key]})
                found=key; break
        if found is None: stats['no_observed_same_anchor_repayment']+=1

# Exact-law bank transfer across a predeclared motif partition. All rows were
# observed previously; this is a synthesis holdout, not fresh source evidence.
train={'N00011101','N11100010','N01011001','N10100110'}
trainbank={key for start,key,_ in observed if start['motif'] in train}
held=[(start,key,wait) for start,key,wait in observed if start['motif'] not in train]
holdstats=Counter()
for start,key,wait in held:
    holdstats['heldout_repaying_starts']+=1
    holdstats['exact_guard_in_frozen_training_bank']+=key in trainbank

# A previously learned law may apply even when it is not the first repayment
# seen in the recorded return list. Test its actual applicability guard rather
# than requiring identity with the observed first law.
guardindex=defaultdict(lambda:defaultdict(dict))
for key in trainbank:
    g=bank[key]
    guardindex[g['anchor']][g['D']][int(g['rho'])]=g
for start in residual_starts:
    if start['motif'] in train: continue
    holdstats['heldout_all_residual_starts']+=1
    matches=[]
    for D,rhos in guardindex[start['anchor']].items():
        g=rhos.get(start['m0']%(1<<(D+1)))
        if g is not None and start['m0']>=int(g['floor']): matches.append(g)
    if matches:
        holdstats['frozen_guard_capability_applies']+=1
        g=min(matches,key=lambda z:z['D'])
        out,bits=replay(start['m0'],start['anchor'],g['D'])
        assert ''.join(map(str,bits))==g['word']
        assert (out+1)%(1<<start['anchor'])==0
        mout=(out+1)>>start['anchor']
        assert int(g['P'])*mout==int(g['A'])*start['m0']+int(g['B'])
        assert mout<start['m0']
    else: holdstats['no_matching_frozen_guard']+=1

result={'schema':'COLLATZ_SYMBOLIC_REPAYMENT_GUARDS_20260930',
    'parent_certificate':v.result['certificate_sha256'],'stats':dict(stats),
    'distinct_guards':len(bank),'training_distinct_guards':len(trainbank),
    'synthesis_holdout':dict(holdstats),
    'max_observed_returns_to_repayment':max(w for _,_,w in observed),
    'guard_D_range':[min(z['D'] for z in bank.values()),max(z['D'] for z in bank.values())],
    'distinct_whole_cylinder_guards':sum(z['whole_cylinder'] for z in bank.values()),
    'distinct_guards_proved_by_existing_live_floor':sum(z['v45_floor_suffices'] for z in bank.values()),
    'examples':examples,'global_collatz':'UNKNOWN',
    'boundary':'Exact conditional affine guards, finite discovery and lifted raw-orbit checks. No universal macro availability, source admission, protected no-exit coverage, or origin-source transport theorem. Owner-cylinder lifts need not belong to the original source family.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
with open('repayment-result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
with open('repayment-guards.json','w') as f: json.dump(list(bank.values()),f,indent=2,sort_keys=True)
print(json.dumps({k:z for k,z in result.items() if k!='examples'},indent=2,sort_keys=True),flush=True)
