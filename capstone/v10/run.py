#!/usr/bin/env python3
"""Source-pinned finite simulation synthesis; CSLib Lean checks remain external."""
import hashlib,json,pathlib,sys
BASE=pathlib.Path(__file__).parent
F=json.loads((BASE/'frozen.json').read_text())
def successors(case,s,a):
    return {t for x,b,t in case['edges'] if x==s and b==a}
def good(case,relation,s,t):
    return all(any((u,v) in relation for v in successors(case,t,a))
               for a in range(case['labels']) for u in successors(case,s,a))
def synthesize(case):
    rel={(s,t) for s in range(case['n']) for t in range(case['n'])}
    history=[]
    while True:
        bad={(s,t) for s,t in rel if not good(case,rel,s,t)}
        history.append({'remaining':len(rel),'removed':len(bad)})
        if not bad: break
        rel-=bad
    return rel,history
def independent(case):
    # Separate reference algorithm: descending iteration using explicit per-label
    # successor sets and a full scan; not using the synthesis predicate.
    n=case['n']; matrix=[[True]*n for _ in range(n)]
    for _ in range(n*n+1):
        old=[row[:] for row in matrix]
        for s in range(n):
            for t in range(n):
                for a in range(case['labels']):
                    for u in successors(case,s,a):
                        if not any(old[u][v] for v in successors(case,t,a)):
                            matrix[s][t]=False
        if matrix==old: return {(s,t) for s in range(n) for t in range(n) if matrix[s][t]}
    raise AssertionError('oracle not converged')
def lean(case,rel):
    n=case['n']; edges=case['edges']
    ed=' ∨ '.join(f'(s = {s} ∧ a = {a} ∧ t = {t})' for s,a,t in edges) or 'false'
    pairs=' ∨ '.join(f'(s = {s} ∧ t = {t})' for s,t in sorted(rel)) or 'false'
    start,target=case['seed']
    name='V10_'+case['id']
    return f"""import Cslib.Foundations.Semantics.LTS.Simulation
namespace {name}
open Cslib
def sys : LTS (Fin {n}) (Fin {case['labels']}) where
  Tr := fun s a t => {ed}
def relation (s t : Fin {n}) : Prop := {pairs}
theorem certified : LTS.IsSimulation sys sys relation := by
  intro s₁ s₂ hrel μ s₁' htr
  fin_cases s₁ <;> fin_cases s₂ <;> fin_cases μ <;> fin_cases s₁'
  all_goals simp_all [sys, relation]
theorem seed : relation {start} {target} := by
  unfold relation
  decide
end {name}
"""
def main():
    work=BASE/'generated';work.mkdir(exist_ok=True)
    dev=[]
    for c in F['development']:
        rel,steps=synthesize(c)
        assert rel==independent(c)
        assert tuple(c['seed']) in rel
        dev.append({'id':c['id'],'old_full_relation_sound':all(good(c,{(i,j) for i in range(c['n']) for j in range(c['n'])},i,j) for i in range(c['n']) for j in range(c['n'])),'rounds':len(steps),'relation_size':len(rel)})
    receipt={'source_sha256':hashlib.sha256((BASE/'frozen.json').read_bytes()).hexdigest(),'constructor':'greatest_forward_simulation_by_elimination','development':dev,'holdout_not_used_for_selection':True}
    (work/'pre_holdout_freeze.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    rows=[]
    for split in ('holdout','controls'):
        for c in F[split]:
            rel,steps=synthesize(c)
            oracle=independent(c)
            assert rel==oracle,(c['id'],rel,oracle)
            seed=tuple(c['seed'])
            success=seed in rel
            assert success==c['expect'],c['id']
            if success:
                (work/(c['id']+'.lean')).write_text(lean(c,rel))
            rows.append({'id':c['id'],'split':split,'seed_survives':success,'expected':c['expect'],'fixed_point_rounds':len(steps),'remaining_pairs':len(rel),'universal_relation_sound':all(good(c,{(i,j) for i in range(c['n']) for j in range(c['n'])},i,j) for i in range(c['n']) for j in range(c['n'])),'lean_file':c['id']+'.lean' if success else None})
    out={'status':'CANDIDATE_PENDING_CSLIB_LEAN','upstream_sha':F['upstream_sha'],'upstream_toolchain':F['upstream_toolchain'],'development':dev,'results':rows,'strong_oracle_tie':True,'scope':'finite locally authored LTSs, not external natural CSLib goals'}
    (work/'results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
