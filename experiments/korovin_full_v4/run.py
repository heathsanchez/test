from pathlib import Path
import sys,json,re,hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from worlds import source_world,transfer_world,noninvertible_control,cyclic_world,relabel_world,rows
from constructor import synthesize,execute,Predicate,conflicts,distinct_behaviors
from verifier import law_audit,element_orders
OUT=HERE/'results'; OUT.mkdir(exist_ok=True)
BANNED=['group','quotient','equivalence','inverse','identity','monoid','dihedral','symmetric','d4','s3','cayley','split_probe']

def leak():
    txt=(HERE/'constructor.py').read_text().lower()
    return {x:txt.count(x) for x in BANNED if x in txt}

def split(w): return rows(w,0,9),rows(w,10,13)

def evaluate(model,test):
    good=0; unknown=0
    for w,o in test:
        s=execute(model,w)
        if s is None: unknown+=1
        elif tuple(model['behaviors'][s])==tuple(o): good+=1
    return {'correct':good,'total':len(test),'accuracy':good/len(test),'unknown':unknown}

def ablate(train,model):
    bs=distinct_behaviors(train); ps=model['predicates']; out=[]
    for i,p in enumerate(ps):
        prog=[Predicate(x['kind'],x['a'],x['b']) for j,x in enumerate(ps) if j!=i]
        c,n,_=conflicts(bs,prog)
        out.append({'removed':p,'conflicts':c,'states':n,'damage':c>0})
    return out

def run(world,causal=False):
    train,test=split(world)
    m=synthesize(train,tuple(world.generators),world.n,max_width=8)
    aud=law_audit(m); mem={w:o for w,o in train}
    base=sum(mem.get(w)==o for w,o in test)/len(test)
    return {'tag':world.tag,'baseline':base,'predicates':m['predicates'],
            'search_history':m['history'],'searched':m['searched'],'states':m['state_count'],
            'heldout':evaluate(m,test),'law_audit':{k:v for k,v in aud.items() if k!='table'},
            'orders':element_orders(aud),'ablation':ablate(train,m) if causal else [],
            'compression':(len(train)+len(test))/m['state_count']}

def main():
    s=run(source_world(),True); t=run(transfer_world()); n=run(noninvertible_control())
    rs=[run(relabel_world(source_world(),q)) for q in (17,29,43,71)]
    gates={'G0_blind_constructor':not leak(),'G1_source_baseline_zero':s['baseline']==0,
      'G2_source_perfect':s['heldout']['accuracy']==1,'G3_source_boolean_basis_nontrivial':len(s['predicates'])>=3,
      'G4_each_predicate_causal':all(x['damage'] for x in s['ablation']),
      'G5_source_group_posthoc':s['law_audit']['group_axiom_bundle'],
      'G6_transfer':t['heldout']['accuracy']==1 and t['law_audit']['group_axiom_bundle'],
      'G7_negative':n['heldout']['accuracy']==1 and not n['law_audit']['group_axiom_bundle'],
      'G8_relabels':all(x['heldout']['accuracy']==1 and x['states']==s['states'] for x in rs),
      'G9_compression':min([s['compression'],t['compression'],n['compression']])>10}
    R={'experiment':'KOROVIN_DISTINCTION_SYNTHESIS_V4','gates':gates,'all_gates_pass':all(gates.values()),
       'claim_boundary':'V4 imports the V3 causal law that observable behavior is the necessary carrier family, then synthesizes a minimum Boolean distinction basis from low-level equality predicates. It is not given coordinate splits or algebraic laws; the predicate grammar and partition semantics remain supplied.',
       'source':s,'transfer':t,'negative':n,'relabels':rs}
    R['sha256']=hashlib.sha256(json.dumps(R,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True))
    print(json.dumps({'all_gates_pass':R['all_gates_pass'],'gates':gates,
      'source':{'predicates':s['predicates'],'states':s['states'],'heldout':s['heldout'],'searched':s['searched'],'history':s['search_history']},
      'transfer':{'predicates':t['predicates'],'states':t['states']},
      'negative':{'predicates':n['predicates'],'states':n['states'],'laws':n['law_audit']}},indent=2))
    if not R['all_gates_pass']: raise SystemExit(1)
if __name__=='__main__': main()
