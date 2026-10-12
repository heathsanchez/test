"""Bounded counterexample-guided synthesis of a reusable finite Moore refinement program.
No held-out family is used during selection. No claim of unrestricted grammar invention.
"""
import itertools, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from falsifier import PROGRAMS,TRAIN,HOLD,machine,evaluate,partition,step,fixed

def execute(obs,tr,prog):
    mode,guard,bound=prog
    p=partition(obs)
    for _ in range({'one':1,'two':2,'states':len(obs)}[bound]):
        q=step(p,tr,mode)
        if guard=='same' and q==p:break
        if guard=='different' and q!=p:break
        p=q
    return p

def independent_oracle(obs,tr):
    n=len(obs)
    signatures=[]
    for state in range(n):
        record=[]
        for length in range(n):
            for word in itertools.product((0,1),repeat=length):
                v=state
                for a in word:v=tr[v][a]
                record.append(obs[v])
        signatures.append(tuple(record))
    return partition(signatures)

def machines(n):
    for obs in itertools.product((0,1),repeat=n):
        for edges in itertools.product(range(n),repeat=2*n):
            yield obs,tuple((edges[2*i],edges[2*i+1]) for i in range(n))

def witness(prog,n):
    for obs,tr in machines(n):
        want=independent_oracle(obs,tr)
        if execute(obs,tr,prog)!=want:
            return {'n':n,'observations':list(obs),'transitions':[list(x) for x in tr], 'expected':list(want),'actual':list(execute(obs,tr,prog))}
    return None

def main():
    # Selection receives only training problems, then exact small-state counterexamples.
    survivors=[p for p in PROGRAMS if all(evaluate(name,p)['pass'] for name in TRAIN)]
    initial=len(survivors)
    rounds=[]
    for n in (2,3):
        rejected=[]
        for p in survivors:
            bad=witness(p,n)
            if bad:rejected.append((p,bad))
        survivors=[p for p in survivors if p not in {x[0] for x in rejected}]
        rounds.append({'size':n,'rejected':len(rejected),'remaining':len(survivors),'first_counterexample':rejected[0][1] if rejected else None})
    # Independent four-state adversarial family: delayed successor-observation split.
    adversarial4=([0,0,0,1],[(0,0),(0,2),(3,0),(3,3)])
    rejects4=[p for p in survivors if execute(*adversarial4,p)!=independent_oracle(*adversarial4)]
    survivors=[p for p in survivors if p not in rejects4]
    rounds.append({"size":4,"kind":"predeclared_delayed_successor_adversary","rejected":len(rejects4),"remaining":len(survivors)})
    adversarial5=([0,0,0,0,1],[(1,0),(2,0),(3,0),(4,0),(4,4)])
    rejects5=[p for p in survivors if execute(*adversarial5,p)!=independent_oracle(*adversarial5)]
    survivors=[p for p in survivors if p not in rejects5]
    rounds.append({"size":5,"kind":"predeclared_deeper_successor_adversary","rejected":len(rejects5),"remaining":len(survivors)})
    selected=min(survivors,key=lambda p:({'one':1,'two':2,'states':3}[p[2]],p)) if survivors else None
    held={name:evaluate(name,selected) for name in HOLD} if selected else {}
    # Adversarial proof-relevant necessity of successor closure on the delayed observation case.
    proof={'finite_state_termination_bound':'at most n-1 strict class splits; check stability by n iterations',
           'soundness_condition':'output agreement and successor-congruence for both actions',
           'unrestricted_new_operator_invention':False}
    result={'status':'BOUNDED_SYNTHESIS','train':TRAIN,'holdout':HOLD,'candidate_count':len(PROGRAMS),
            'train_survivors':initial,'adversarial_rounds':rounds,'remaining':len(survivors),
            'selected':selected,'heldout':held,'all_holdout_pass':all(v['pass'] for v in held.values()) if selected else False,
            'oracle':'independent future-word enumeration','semantic_prior':'fixed 27-program grammar; verifier; 2/3-state adversarial search',
            'theorem_argument':proof}
    print(json.dumps(result,indent=2,sort_keys=True))
    if selected is None or not result['all_holdout_pass']:raise SystemExit(1)
if __name__=='__main__':main()
