"""Frozen finite Q7 selection-vs-genesis falsifier. Standard-library only."""
import itertools,json,hashlib,pathlib
TRAIN=("parity","mod3","suffix2","contains11")
HOLD=("contains101","mod5","mod7")
MODES=("left","right","both")
GUARDS=("none","same","different")
BOUNDS=("one","two","states")
PROGRAMS=tuple(itertools.product(MODES,GUARDS,BOUNDS))
def machine(name):
    if name=="parity": return (2,[0,1],[(1,0),(0,1)])
    if name=="mod3": return (3,[0,1,0],[(0,1),(2,0),(1,2)])
    if name=="mod5": return (5,[0,0,1,0,1],[(0,1),(2,3),(4,0),(1,2),(3,4)])
    if name=="mod7": return (7,[0,0,1,0,1,0,1],[(0,1),(2,3),(4,5),(6,0),(1,2),(3,4),(5,6)])
    if name=="suffix2": return (4,[0,0,1,1],[(0,1),(2,3),(0,1),(2,3)])
    if name=="contains11": return (3,[0,0,1],[(0,1),(0,2),(2,2)])
    if name=="contains101": return (4,[0,0,0,1],[(0,1),(2,1),(0,3),(3,3)])
    raise ValueError(name)
def partition(labels):
    keys={};out=[]
    for k in labels:
        if k not in keys: keys[k]=len(keys)
        out.append(keys[k])
    return tuple(out)
def step(p,tr,mode):
    return partition([(p[i],)+tuple(p[tr[i][j]] for j in ((0,1) if mode=="both" else ((0,) if mode=="left" else (1,)))) for i in range(len(p))])
def fixed(obs,tr):
    p=partition(obs)
    for _ in range(len(obs)+1):
        q=step(p,tr,"both")
        if q==p:return p
        p=q
    raise AssertionError("no fixed point")
def evaluate(name,prog):
    n,obs,tr=machine(name); mode,guard,bound=prog
    p=partition(obs)
    limit={"one":1,"two":2,"states":n}[bound]
    rounds=0
    for _ in range(limit):
        q=step(p,tr,mode);rounds+=1
        if guard=="same" and q==p:break
        if guard=="different" and q!=p:break
        p=q
    return {"pass":p==fixed(obs,tr),"steps":rounds}
def choose(name,history):
    stats=[]
    for p in PROGRAMS:
        rows=[history[(t,p)] for t in TRAIN]
        stats.append((p,sum(x["pass"] for x in rows),sum(x["steps"] for x in rows)))
    if name=="lexicographic":return PROGRAMS[0]
    if name=="empirical":return min(stats,key=lambda x:(-x[1],x[2],x[0]))[0]
    if name=="htilt_lite":return min(stats,key=lambda x:(-(x[1]-.1*x[2]),x[0]))[0]
    if name=="supplied_semantic_guard":
        return min((x for x in stats if x[1]==len(TRAIN) and x[0][0]=="both" and x[0][1]=="same" and x[0][2]!="one"),key=lambda x:(x[2],x[0]))[0]
    raise ValueError(name)
def main():
    history={(t,p):evaluate(t,p) for t in TRAIN for p in PROGRAMS}
    policies=("lexicographic","empirical","htilt_lite","supplied_semantic_guard")
    selected={s:choose(s,history) for s in policies}
    holdout={s:{t:evaluate(t,p) for t in HOLD} for s,p in selected.items()}
    assert len(history)==108
    assert all(sum(x["pass"] for x in holdout[s].values())==2 for s in policies[:3])
    assert all(x["pass"] for x in holdout["supplied_semantic_guard"].values())
    assert selected["empirical"]==selected["htilt_lite"]
    out={"status":"BOUNDED_FINITE_FALSIFIER","candidate_count":27,"historical_evaluations":108,
         "train":TRAIN,"holdout":HOLD,"selected":selected,"holdout_results":holdout,
         "htilt_strict_advantage":False,"genesis_has_extra_semantic_prior":True,
         "limits":["synthetic Moore families","supplied grammar","no new primitive invention","no natural-domain transfer","no Lean verification","no strong-ledger cost advantage"]}
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=="__main__":main()
