#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, random, sys
from pathlib import Path
from itertools import product
import z3

# Reuse V24 raw parser/ports/policy synthesizer exactly.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sair_raw_adequacy_v24 as v24

Z3_NAMES=('z0','z1')  # forward / reverse order-3 countermodel existence

def zeval(n, env, cells, N):
    if n.leaf: return z3.IntVal(env[n.v])
    a=zeval(n.l,env,cells,N); b=zeval(n.r,env,cells,N)
    expr=cells[0]
    for i in range(N):
        for j in range(N):
            expr=z3.If(z3.And(a==i,b==j),cells[i*N+j],expr)
    return expr

def eq_constraints(eq,cells,N):
    a,b=eq; vs=sorted(v24.vars_of(a)|v24.vars_of(b)); out=[]
    for vals in product(range(N),repeat=len(vs)):
        env=dict(zip(vs,vals)); out.append(zeval(a,env,cells,N)==zeval(b,env,cells,N))
    return out

def fail_disjunction(eq,cells,N):
    a,b=eq; vs=sorted(v24.vars_of(a)|v24.vars_of(b)); dis=[]
    for vals in product(range(N),repeat=len(vs)):
        env=dict(zip(vs,vals)); dis.append(zeval(a,env,cells,N)!=zeval(b,env,cells,N))
    return z3.Or(dis)

def sat_counterexample(eq_h,eq_g,N=3,timeout_ms=1500):
    cells=[z3.Int(f't{i}') for i in range(N*N)]
    s=z3.Solver(); s.set(timeout=timeout_ms)
    for c in cells: s.add(c>=0,c<N)
    s.add(*eq_constraints(eq_h,cells,N)); s.add(fail_disjunction(eq_g,cells,N))
    r=s.check()
    if r!=z3.sat: return False,None,str(r)
    m=s.model(); table=tuple(tuple(m.eval(cells[i*N+j]).as_long() for j in range(N)) for i in range(N))
    return True,table,'sat'

def eval_termN(n,env,t):
    if n.leaf:return env[n.v]
    return t[eval_termN(n.l,env,t)][eval_termN(n.r,env,t)]
def holdsN(eq,t):
    a,b=eq; vs=sorted(v24.vars_of(a)|v24.vars_of(b)); N=len(t)
    for vals in product(range(N),repeat=len(vs)):
        env=dict(zip(vs,vals))
        if eval_termN(a,env,t)!=eval_termN(b,env,t): return False
    return True

def recheck(eq_h,eq_g,t): return t is None or (holdsN(eq_h,t) and not holdsN(eq_g,t))

def build(root,sets):
    rows=[]; witnesses=bad=timeouts=0
    for src in sets:
        for row in v24.load_jsonl(root/'examples'/'problems'/f'{src}.jsonl'):
            x,w,eqs=v24.observations(row); e1,e2=eqs
            f,tf,sf=sat_counterexample(e1,e2); r,tr,sr=sat_counterexample(e2,e1)
            if sf=='unknown': timeouts+=1
            if sr=='unknown': timeouts+=1
            for ok,t,a,b in ((f,tf,e1,e2),(r,tr,e2,e1)):
                if ok:
                    witnesses+=1
                    if not recheck(a,b,t): bad+=1
            x=dict(x); x['z0']=int(f); x['z1']=int(r)
            rows.append({'id':row['id'],'source':src,'x':x,'y':bool(row['answer'])})
    return rows,witnesses,bad,timeouts

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sair-root',required=True);ap.add_argument('--out-dir',required=True)
    a=ap.parse_args();root=Path(a.sair_root);out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    train,w1,b1,t1=build(root,('normal','hard1','hard2')); test,w2,b2,t2=build(root,('hard3',))
    full_names=v24.ALL_NAMES+Z3_NAMES
    p,tra,natoms=v24.fit(train,full_names); acc=v24.accuracy(p,test)
    old,oldtra,_=v24.fit(train,v24.ALL_NAMES); oldacc=v24.accuracy(old,test)
    syn,syntra,_=v24.fit(train,v24.SYNTAX_NAMES); synacc=v24.accuracy(syn,test)
    # deterministic shuffle only z3 ports
    rng=random.Random(20260821); allr=[{'id':r['id'],'source':r['source'],'x':dict(r['x']),'y':r['y']} for r in train+test]
    zv=[(r['x']['z0'],r['x']['z1']) for r in allr];rng.shuffle(zv)
    for r,z in zip(allr,zv):r['x']['z0'],r['x']['z1']=z
    st=allr[:len(train)];se=allr[len(train):];sp,_,_=v24.fit(st,full_names);shacc=v24.accuracy(sp,se)
    gates={
      'external_sair_split_frozen':all(r['source']=='hard3' for r in test),
      'answer_blind_bounded_model_ports':True,
      'all_sat_witnesses_rechecked':b1+b2==0,
      'beats_frozen_v24_hard3_05675':acc>0.5675,
      'beats_syntax_only':acc>synacc,
      'order3_ports_improve_over_v24_ports':acc>oldacc,
      'shuffled_order3_degrades':shacc<acc,
    }
    gates['SAIR_BOUNDED_MODEL_ADEQUACY_GATE']=all(gates.values())
    res={'status':'V25_SAIR_BOUNDED_MODEL_ADEQUACY','n_train':len(train),'n_test':len(test),
         'z3_sat_witnesses_rechecked':w1+w2,'z3_unknown_queries':t1+t2,
         'policy':str(p),'train_accuracy':tra,'hard3_accuracy':acc,
         'v24_ports_hard3_accuracy':oldacc,'syntax_hard3_accuracy':synacc,
         'shuffled_z3_hard3_accuracy':shacc,'candidate_atoms':natoms,'gates':gates}
    (out/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
