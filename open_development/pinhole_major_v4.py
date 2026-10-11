"""Three-world shared closure: functions, relations, and real MDA ledger."""
import itertools,json,tempfile
from pathlib import Path
from .runtime import EvidenceStore
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE,SOURCE_THIRD,NEXT,AFTER,FUTURES,obl

def saturate(seed,ops,universe):
    known=set(seed); rounds=checks=0
    while True:
        rounds+=1; new=set()
        for arity,fn in ops:
            for args in itertools.product(tuple(sorted(known)),repeat=arity):
                checks+=1; v=fn(*args)
                assert v in universe
                new.add(v)
        if new<=known:return known,rounds,checks
        known|=new

def main():
    f=set(itertools.product(range(3),repeat=3))
    fs={(0,1,2),(1,2,0),(0,0,2)}
    fc=lambda a,b:tuple(b[a[i]] for i in range(3))
    funcs,_,_=saturate(fs,[(2,fc)],f)
    assert len(funcs)==24
    def rc(a,b):
        out=0
        for i,j,k in itertools.product(range(2),repeat=3):
            if a>>(2*i+j)&1 and b>>(2*j+k)&1:out|=1<<(2*i+k)
        return out
    rels,_,_=saturate({9,2,4},[(2,rc),(2,lambda a,b:a|b)],set(range(16)))
    assert len(rels)==16
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'ledger.sqlite';store=EvidenceStore(path)
        old=MinimalContinuation(store,ProofCompositionAdapter())
        for t,b in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            assert old.run_minimal(obl(t,b)).outcome=='COMMIT'
        new=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        for t in (NEXT,AFTER):
            assert new.run_minimal(obl(t,1)).outcome=='COMMIT'
        caps=store.state()['capabilities'];assert len(caps)==6
        deps={k:tuple(v['repair']['dependencies']) for k,v in caps.items()}
        ids=tuple(sorted(deps))
        universe={tuple(ids[i] for i in range(len(ids)) if mask>>i&1) for mask in range(1<<len(ids))}
        def operator(blocked=None):
            def apply(known):
                out=set(known)
                for k,parents in deps.items():
                    if k!=blocked and set(parents)<=out:out.add(k)
                return tuple(sorted(out))
            return apply
        reached,rounds,checks=saturate({()},[(1,operator())],universe)
        assert ids in reached
        # Independent topological oracle for the exact dependency graph.
        done=set();todo=set(ids)
        while todo:
            ready={k for k in todo if set(deps[k])<=done}
            assert ready
            done|=ready;todo-=ready
        assert done==set(ids)
        losses={}
        for blocked in ids:
            reduced,_,_=saturate({()},[(1,operator(blocked))],universe)
            best=max(reduced,key=len)
            expected=set(ids)-{blocked}
            while True:
                rem={k for k in expected if any(p not in expected for p in deps[k])}
                if not rem:break
                expected-=rem
            assert set(best)==expected
            losses[blocked]=len(ids)-len(expected)
        store.close();store=EvidenceStore(path)
        replay=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        verdicts=[replay.run_minimal(obl(t,0)) for t in FUTURES]
        assert len(verdicts)==16 and all(v.outcome=='IDENTITY' and v.verdict=='verified' for v in verdicts)
        store.close()
    print(json.dumps({'status':'PASS_EXACT_THREE_WORLD_CLOSURE','function_reach':len(funcs),
      'relation_reach':len(rels),'mda_nodes':len(ids),'mda_edges':sum(map(len,deps.values())),
      'mda_protected':len(verdicts),'mda_closure_rounds':rounds,
      'mda_checks':checks,'ablated_losses':losses,
      'independent_topological_oracle':True,'same_closure_engine':True,
      'domain_semantics_supplied':True,'new_constructor_invention':'NOT_TESTED',
      'whole_plan_optimization':'NOT_TESTED'},indent=2,sort_keys=True))
if __name__=='__main__':main()
