from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from worlds import source_world,transfer_world,noninvertible_control,execute
from theory import synthesize_theory,saturate,audit_congruence

OUT=HERE/'results';OUT.mkdir(exist_ok=True)

def semantic(world): return lambda w: execute(world,w)
def fmt(w): return 'ε' if not w else ''.join(w)

def run_world(world, require_complete=True):
    toks=tuple(world.generators)
    sem=semantic(world)
    th=synthesize_theory(toks,sem,train_h=7,candidate_h=4,max_rules=8)
    U9,d9=saturate(toks,9,th['rules'])
    held=audit_congruence(U9,d9,sem)
    ab=[]
    for i,r in enumerate(th['rules']):
        rs=[x for j,x in enumerate(th['rules']) if j!=i]
        Ua,da=saturate(toks,7,rs)
        aa=audit_congruence(Ua,da,sem)
        ab.append({'removed':[fmt(r[0]),fmt(r[1])],'exact_after_removal':aa['exact'],
                   'classes_after_removal':aa['congruence_classes'],
                   'semantic_classes':aa['semantic_classes']})
    return {'tag':world.tag,'rules':[{'lhs':fmt(a),'rhs':fmt(b)} for a,b in th['rules']],
            'candidate_count':th['candidate_count'],'history':th['history'],
            'train_audit':th['train_audit'],'protected_h9_audit':held,'ablation':ab}

def main():
    s=run_world(source_world()); t=run_world(transfer_world()); n=run_world(noninvertible_control(),False)
    gates={
      'G1_source_compact_theory':1<=len(s['rules'])<=4,
      'G2_source_train_exact':s['train_audit']['exact'],
      'G3_source_protected_exact':s['protected_h9_audit']['exact'],
      'G4_source_every_rule_causal':all(not x['exact_after_removal'] for x in s['ablation']),
      'G5_transfer_train_exact':t['train_audit']['exact'],
      'G6_transfer_protected_exact':t['protected_h9_audit']['exact'],
      'G7_transfer_compact':len(t['rules'])<=5,
      'G8_no_false_merges_anywhere':all(x['protected_h9_audit']['false_merges']==0 for x in (s,t,n)),
    }
    R={'experiment':'KOROVIN_USABLE_THEORY_FORMATION_V5','gates':gates,'all_gates_pass':all(gates.values()),
       'claim_boundary':'A generic generator proposes short equations, an external exact semantic oracle admits only true ones, and a generic contextual-closure learner selects a compact causally necessary theory. Exactness is bounded to the declared word horizons; this is not proof of a globally complete presentation.',
       'source':s,'transfer':t,'negative_control':n}
    R['sha256']=hashlib.sha256(json.dumps(R,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True))
    print(json.dumps({'all_gates_pass':R['all_gates_pass'],'gates':gates,
      'source':{'rules':s['rules'],'train':s['train_audit'],'protected':s['protected_h9_audit'],'ablation':s['ablation']},
      'transfer':{'rules':t['rules'],'train':t['train_audit'],'protected':t['protected_h9_audit']},
      'negative':{'rules':n['rules'],'train':n['train_audit'],'protected':n['protected_h9_audit']}},indent=2))
    if not R['all_gates_pass']:raise SystemExit(1)
if __name__=='__main__':main()
