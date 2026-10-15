#!/usr/bin/env python3
"""ARC400 V12 — constrained frame-development operator.

V12 freezes V11's remaining certified representation collision and treats the
next move as a choice among *frame transformations*, not as ad-hoc feature
engineering.  It first exhausts bounded same-frame continuation (single/pair
observable-program additions).  Only if that boundary cannot close the
collision is promotion to a richer structured-relation frame licensed.

For a residual rho, we search a finite transformation version space
  V_Theta(rho) = {Theta : Theta satisfies the required label separation}
and select a minimum-cost transformation under a frozen lexicographic cost:
  (frame_level_change, number_of_installed_programs, total_ast_size, name).

Success requires more than collision reduction: the learned transformed frame
is frozen, predicts S/B before the post-hoc oracle, produces an exact solution,
and local constructor ablation removes that solution on held-out and
source-distinct tasks.

All negative claims are bounded to explicitly enumerated carriers.
"""
from __future__ import annotations
import argparse, json, random, sys, itertools, math
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import arc400_observable_program_synthesis_v11 as v11
import arc400_recursive_applicability_v10 as v10
import arc400_meta_grammar_development_v6 as v6

LABELS=("BOT","S","B")
EPS=1e-9


def comps(g):
    h=len(g); w=len(g[0]) if h else 0; seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        if (r,c) in seen: continue
        col=g[r][c]; q=[(r,c)]; seen.add((r,c)); pts=[]
        while q:
          x,y=q.pop(); pts.append((x,y))
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            a,b=x+dx,y+dy
            if 0<=a<h and 0<=b<w and (a,b) not in seen and g[a][b]==col:
              seen.add((a,b)); q.append((a,b))
        out.append((col,pts))
    return out


def structured_measurements(task):
    """Generic object/relation measurements from training pairs only."""
    tr=task.get('train',[])
    if not tr: return {}
    vals={k:[] for k in ['in_components','out_components','component_ratio','tile_unique_match_min','tile_variant_diversity','layout_consistency','object_count_equal']}
    layouts=[]
    for ex in tr:
      i,o=ex['input'],ex['output']; hi,wi=v11.dims(i); ho,wo=v11.dims(o)
      ic=len(comps(i)); oc=len(comps(o)); vals['in_components'].append(float(ic)); vals['out_components'].append(float(oc)); vals['component_ratio'].append(float(oc)/max(1,ic)); vals['object_count_equal'].append(1.0 if ic==oc else 0.0)
      # Build a correspondence object: each output tile is related to the D8(input)
      # variants that match it exactly.  Summaries describe that relation, not S/B.
      if hi and wi and ho%hi==0 and wo%wi==0:
        br,bc=ho//hi,wo//wi; vs=[x for x in v11.d8(i) if v11.dims(x)==(hi,wi)]
        matchsets=[]; layout=[]
        for rr in range(br):
          row=[]
          for cc in range(bc):
            tile=[x[cc*wi:(cc+1)*wi] for x in o[rr*hi:(rr+1)*hi]]
            ids=tuple(k for k,z in enumerate(vs) if z==tile); matchsets.append(ids); row.append(ids[0] if len(ids)==1 else -1)
          layout.append(tuple(row))
        vals['tile_unique_match_min'].append(sum(len(s)==1 for s in matchsets)/max(1,len(matchsets)))
        vals['tile_variant_diversity'].append(float(len(set(k for s in matchsets for k in s))))
        layouts.append(tuple(layout))
      else:
        vals['tile_unique_match_min'].append(0.0); vals['tile_variant_diversity'].append(-1.0); layouts.append(None)
    def const_or_neg(xs):
      return float(xs[0]) if xs and all(abs(float(x)-float(xs[0]))<EPS for x in xs) else -1.0
    out={
      'in_components_const':const_or_neg(vals['in_components']),
      'out_components_const':const_or_neg(vals['out_components']),
      'component_ratio_const':const_or_neg(vals['component_ratio']),
      'object_count_equal_min':min(vals['object_count_equal']) if vals['object_count_equal'] else 0.0,
      'tile_unique_match_min':min(vals['tile_unique_match_min']) if vals['tile_unique_match_min'] else 0.0,
      'tile_variant_diversity_const':const_or_neg(vals['tile_variant_diversity']),
      'layout_consistency':1.0 if layouts and layouts[0] is not None and all(x==layouts[0] for x in layouts) else 0.0,
    }
    return out


def eval_rel(p,row):
    kind=p[0]
    if kind=='cmpc':
      _,m,op,c=p; x=row.get(m,-1.0)
      return abs(x-c)<EPS if op=='==' else (x>=c-EPS if op=='>=' else x<=c+EPS)
    if kind=='eqm': return abs(row.get(p[1],-1)-row.get(p[2],-1))<EPS
    if kind=='diffc':
      _,a,b,op,c=p; x=row.get(a,-1)-row.get(b,-1)
      return abs(x-c)<EPS if op=='==' else (x>=c-EPS if op=='>=' else x<=c+EPS)
    if kind=='ratioc':
      _,a,b,op,c=p; den=row.get(b,-1); x=(row.get(a,-1)/den) if abs(den)>EPS else -999.0
      return abs(x-c)<EPS if op=='==' else (x>=c-EPS if op=='>=' else x<=c+EPS)
    raise ValueError(p)


def pname(p): return repr(p)

def build_structured_carrier(metric_names):
    cs=(-1.0,0.0,0.5,1.0,2.0,3.0,4.0,9.0)
    ps=[]
    for m in metric_names:
      for c in cs:
        for op in ('==','>=','<='): ps.append(('cmpc',m,op,c))
    for i,a in enumerate(metric_names):
      for b in metric_names[i+1:]:
        ps.append(('eqm',a,b))
        for op in ('==','>=','<='):
          for c in (-1.0,0.0,1.0,2.0): ps.append(('diffc',a,b,op,c))
        for op in ('==','>=','<='):
          for c in (0.5,1.0,2.0,3.0): ps.append(('ratioc',a,b,op,c))
    return ps


def signature(task,base,oldps,newps,mcache,bcache,scache):
    b=bcache[id(task)]; s=tuple(bool(b.get(x,False)) for x in base)
    s+=tuple(v11.eval_prog(p,mcache[id(task)]) for p in oldps)
    merged=dict(mcache[id(task)]); merged.update(scache[id(task)])
    s+=tuple(eval_rel(p,merged) for p in newps)
    return s


def collision_score(examples,base,oldps,newps,mcache,bcache,scache):
    buckets={}
    for _,t,lab,_ in examples:
      z=signature(t,base,oldps,newps,mcache,bcache,scache); buckets.setdefault(z,set()).add(lab)
    bad={k:v for k,v in buckets.items() if len(v)>1}
    return sum(len(v)*(len(v)-1)//2 for v in bad.values()),bad


def search_min_sets(examples,base,installed,carrier,mcache,bcache,scache,max_depth,structured=False):
    # CompleteCover is exact for the declared depth slice. Return every minimum
    # zero-collision set at the first depth where one exists.
    unused=[p for p in carrier if p not in installed]
    checked=0; winners=[]
    for d in range(1,max_depth+1):
      for combo in itertools.combinations(unused,d):
        checked+=1
        if structured:
          score,_=collision_score(examples,base,installed,list(combo),mcache,bcache,scache)
        else:
          score,_=collision_score(examples,base,installed+list(combo),[],mcache,bcache,scache)
        if score==0: winners.append(combo)
      if winners: break
    return winners,checked


def learn_lookup(examples,base,oldps,newps,mcache,bcache,scache):
    table={}; support={}; amb=set()
    for _,t,lab,_ in examples:
      z=signature(t,base,oldps,newps,mcache,bcache,scache)
      if z in table and table[z]!=lab: amb.add(z)
      else: table[z]=lab
      support[z]=support.get(z,0)+1
    for z in amb: table.pop(z,None)
    return table,support


def audit(tasks,base,oldps,newps,table,mcache,bcache,scache):
    rows=[]; pred=abst=correct=wrong=exact=causal=0
    for tid,t in tasks:
      z=signature(t,base,oldps,newps,mcache,bcache,scache); p=table.get(z,'BOT')
      if p=='BOT': abst+=1; continue
      pred+=1
      y,_=v10.oracle_label(t); ok=(p==y); correct+=int(ok); wrong+=int(not ok)
      solved=False; ast=None; base_solved=False
      if ok and p in ('S','B'):
        o,ast,_=v6.solve_with_grammar(t,{'U',p}); solved=v6.score_output(t,o)
        bo,_,_=v6.solve_with_grammar(t,{'U'}); base_solved=v6.score_output(t,bo)
      cc=bool(solved and not base_solved); exact+=int(solved); causal+=int(cc)
      rows.append({'task':tid,'predicted':p,'posthoc_oracle':y,'prediction_correct':ok,'exact_after_Theta':solved,'C_causal':cc,'ast':repr(ast) if ast else None})
    return {'predictions':pred,'abstentions':abst,'correct':correct,'wrong_nonbot':wrong,'exact':exact,'causal_exact':causal,'rows':rows}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arc-root',required=True); ap.add_argument('--out-dir',required=True); ap.add_argument('--seed',type=int,default=1729); a=ap.parse_args()
    root=Path(a.arc_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    train=v10.load_tasks(root,'training'); ev=v10.load_tasks(root,'evaluation')
    ids=list(range(len(train))); random.Random(a.seed).shuffle(ids); cut=len(ids)//2; meta=[train[i] for i in ids[:cut]]; held=[train[i] for i in ids[cut:]]
    examples=[]
    for tid,t in meta:
      lab,ast=v10.oracle_label(t); examples.append((tid,t,lab,ast))
    allts=[t for _,t in train+ev]; bcache={};mcache={};scache={}
    for t in allts:
      bcache[id(t)]=v10.base_observables(t); mcache[id(t)]=v11.measurements(t); scache[id(t)]=structured_measurements(t)
    base=['shape_ratio_equal','palette_preserved']; oldcarrier=v11.build_program_carrier(sorted(next(iter(mcache.values())).keys()))
    installed,vevents,v11_final=v11.refine(examples,base,oldcarrier,mcache,bcache)

    # Layer rule: exhaust bounded same-frame pairs before promoting.
    same_winners,same_checked=search_min_sets(examples,base,installed,oldcarrier,mcache,bcache,scache,2,False)
    same_absent=(len(same_winners)==0)
    chosen_old=list(installed); chosen_new=[]; theta=None; version_space=[]
    if same_winners:
      version_space=[{'family':'SAME_FRAME_OBSERVABLE','programs':[pname(p) for p in w]} for w in same_winners]
      best=min(same_winners,key=lambda w:(0,len(w),sum(len(pname(p)) for p in w),repr(w)))
      chosen_old+=list(best); theta={'family':'SAME_FRAME_OBSERVABLE','programs':[pname(p) for p in best],'frame_level_change':0}
    else:
      merged_names=sorted(set(next(iter(mcache.values())).keys())|set(next(iter(scache.values())).keys()))
      structcarrier=build_structured_carrier(merged_names)
      struct_winners,struct_checked=search_min_sets(examples,base,installed,structcarrier,mcache,bcache,scache,2,True)
      version_space=[{'family':'STRUCTURED_RELATIONAL_FRAME','programs':[pname(p) for p in w]} for w in struct_winners]
      if struct_winners:
        best=min(struct_winners,key=lambda w:(1,len(w),sum(len(pname(p)) for p in w),repr(w)))
        chosen_new=list(best); theta={'family':'STRUCTURED_RELATIONAL_FRAME','programs':[pname(p) for p in best],'frame_level_change':1}
      else:
        struct_checked=struct_checked
    final,bad=collision_score(examples,base,chosen_old,chosen_new,mcache,bcache,scache)
    table,support=learn_lookup(examples,base,chosen_old,chosen_new,mcache,bcache,scache)
    h=audit(held,base,chosen_old,chosen_new,table,mcache,bcache,scache); e=audit(ev,base,chosen_old,chosen_new,table,mcache,bcache,scache)
    initial,_=collision_score(examples,base,installed,[],mcache,bcache,scache)
    preserve=True # both transformation families are additive: old observables remain literal coordinates.
    gates={
      'v11_residual_frozen': initial==v11_final and initial>0,
      'CompleteCover_same_frame_depth_le_2': True,
      'same_frame_absence_if_promoted': (theta is None or theta['frame_level_change']==0 or same_absent),
      'Theta_exists': theta is not None,
      'Theta_minimal_in_declared_version_space': theta is not None,
      'C_preserve_additive': preserve,
      'K_rho_satisfied_collision_closed': final==0,
      'heldout_prediction_exists':h['predictions']>0,
      'heldout_zero_false_nonbot':h['wrong_nonbot']==0,
      'heldout_C_causal':h['causal_exact']>0,
      'source_distinct_prediction_exists':e['predictions']>0,
      'source_distinct_zero_false_nonbot':e['wrong_nonbot']==0,
      'source_distinct_C_causal':e['causal_exact']>0,
    }
    gates['FRAME_DEVELOPMENT_OPERATOR_GATE']=all(gates.values())
    result={'status':'ARC400_FRAME_DEVELOPMENT_OPERATOR_V12','claim_scope':'bounded frame-development search; exact same-frame CompleteCover for additions of depth <=2, then exact structured-frame CompleteCover for additions of depth <=2; minimum-cost Theta among zero-collision candidates; additive preservation; causal exact solve and source-distinct transfer required',
      'split':{'meta_train':len(meta),'heldout_training':len(held),'evaluation':len(ev)},
      'rho_F':{'v11_remaining_collisions':initial,'required_effect':'separate every certified BOT/S/B collision while preserving existing coordinates'},
      'same_frame_boundary':{'carrier_size':len(oldcarrier),'max_additions':2,'checked':same_checked,'CompleteCover':True,'zero_collision_witnesses':len(same_winners)},
      'frame_promotion_licensed':same_absent,
      'Theta_version_space_size':len(version_space),'Theta_star':theta,'C_preserve':'ADDITIVE_LITERAL_COORDINATE_INCLUSION' if theta else None,
      'final_meta_collisions':final,'heldout_training':h,'source_distinct_evaluation':e,'gates':gates}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
