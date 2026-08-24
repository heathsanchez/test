import json, math, random
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT.parent/'law_induction_v1b'/'cases.json').read_text())
CODES={'J':0,'K':1,'L':2,'M':3}; INV={v:k for k,v in CODES.items()}
SEED=2026082505
TEMPLATES=[
    {'id':'t1','initial':['CX','CY','DX','DY'],'target':'BY','queries':['AX','AY','BX']},
    {'id':'t2','initial':['BX','BY','DX','DY'],'target':'CY','queries':['AX','AY','CX']},
    {'id':'t3','initial':['AX','AY','DX','DY'],'target':'CY','queries':['BX','BY','CX']},
    {'id':'t4','initial':['AX','AY','BX','BY'],'target':'CY','queries':['CX','DX','DY']},
]


def parse_oracle(c):
    import re
    b={k:int(v) for k,v in re.findall(r'([ABCD])=(\d)',c['oracle'])}
    o={k:int(v) for k,v in re.findall(r'([XY])=(\d)',c['oracle'])}
    return b,o


def world_value(c,pair):
    b,o=parse_oracle(c)
    return (b[pair[0]]+o[pair[1]])%4


def all_hypotheses():
    hs=[]
    for vals in product(range(4), repeat=5):
        b=dict(zip('ABCD',vals[:4])); y=vals[4]
        hs.append((b,{'X':0,'Y':y}))
    return hs

HYPOTHESES=all_hypotheses()


def pred(h,pair):
    b,o=h
    return (b[pair[0]]+o[pair[1]])%4


def survivors(c, pairs):
    return [h for h in HYPOTHESES if all(pred(h,p)==world_value(c,p) for p in pairs)]


def entropy(values):
    cnt=Counter(values); n=len(values)
    if n==0: return 0.0
    return -sum((v/n)*math.log2(v/n) for v in cnt.values() if v)


def target_entropy(H,target):
    return entropy([pred(h,target) for h in H])


def expected_target_entropy(H,q,target):
    groups=defaultdict(list)
    for h in H: groups[pred(h,q)].append(h)
    return sum((len(g)/len(H))*target_entropy(g,target) for g in groups.values())


def majority(H,target):
    cnt=Counter(pred(h,target) for h in H)
    m=max(cnt.values())
    winners=sorted(k for k,v in cnt.items() if v==m)
    return winners[0]


def update(H,q,answer):
    return [h for h in H if pred(h,q)==answer]

rng=random.Random(SEED)
rows=[]
for c in DATA['cases']:
    for t in TEMPLATES:
        H0=survivors(c,t['initial'])
        e0=target_entropy(H0,t['target'])
        truth=world_value(c,t['target'])

        # NO_EXTRA
        p0=majority(H0,t['target'])
        rows.append({'case_id':c['id'],'template':t['id'],'arm':'NO_EXTRA','query':None,'target':t['target'],
                     'target_truth':INV[truth],'target_pred':INV[p0],'correct':p0==truth,
                     'n_before':len(H0),'n_after':len(H0),'entropy_before':e0,'entropy_after':e0})

        # RANDOM_QUERY
        rq=rng.choice(t['queries']); ra=world_value(c,rq); Hr=update(H0,rq,ra); rp=majority(Hr,t['target'])
        rows.append({'case_id':c['id'],'template':t['id'],'arm':'RANDOM_QUERY','query':rq,'query_answer':INV[ra],
                     'target':t['target'],'target_truth':INV[truth],'target_pred':INV[rp],'correct':rp==truth,
                     'n_before':len(H0),'n_after':len(Hr),'entropy_before':e0,'entropy_after':target_entropy(Hr,t['target'])})

        # INFO_GAIN_QUERY — expected target entropy before seeing outcome.
        ig_scores={q:e0-expected_target_entropy(H0,q,t['target']) for q in t['queries']}
        iq=sorted(t['queries'], key=lambda q:(-ig_scores[q],q))[0]
        ia=world_value(c,iq); Hi=update(H0,iq,ia); ip=majority(Hi,t['target'])
        rows.append({'case_id':c['id'],'template':t['id'],'arm':'INFO_GAIN_QUERY','query':iq,'query_answer':INV[ia],
                     'query_expected_target_info_gain':ig_scores[iq], 'target':t['target'],'target_truth':INV[truth],
                     'target_pred':INV[ip],'correct':ip==truth,'n_before':len(H0),'n_after':len(Hi),
                     'entropy_before':e0,'entropy_after':target_entropy(Hi,t['target'])})

        # ORACLE_QUERY — outcome-aware ceiling among the same 3 allowed queries.
        opts=[]
        for q in t['queries']:
            a=world_value(c,q); Hq=update(H0,q,a)
            opts.append((target_entropy(Hq,t['target']),len(Hq),q,Hq,a))
        _,_,oq,Ho,oa=sorted(opts,key=lambda x:(x[0],x[1],x[2]))[0]
        op=majority(Ho,t['target'])
        rows.append({'case_id':c['id'],'template':t['id'],'arm':'ORACLE_QUERY','query':oq,'query_answer':INV[oa],
                     'target':t['target'],'target_truth':INV[truth],'target_pred':INV[op],'correct':op==truth,
                     'n_before':len(H0),'n_after':len(Ho),'entropy_before':e0,'entropy_after':target_entropy(Ho,t['target'])})

(ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'active.latent.disambiguation.v1','seed':SEED,
    'worlds':len(DATA['cases']),'templates':TEMPLATES,'tasks':len(DATA['cases'])*len(TEMPLATES),
    'hypothesis_family':'add_mod4 gauge X=0','llm_used':False},indent=2))
print('ACTIVE_LATENT_DISAMBIGUATION_V1_RUN_PASS',len(rows),flush=True)
