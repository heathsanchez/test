#!/usr/bin/env python3
from pathlib import Path
import re

p=Path('scripts/run_developmental_checker_span_v10.py')
s=p.read_text()
s=s.replace('results/developmental-checker-lineage-v10','results/developmental-checker-causal-quotient-v12')
s=s.replace("'LIVE_PROPAGATED_LINEAGE_V10'","'LIVE_OPERAND_CAUSAL_QUOTIENT_V12'")

# Add one explicit causal distinction at the final failed comparison: which operand-building
# computation an event belongs to. This is trace-only and semantics-inert.
old='''        eprintln!(\"[MGTRACE] kind=span_begin site=infer.decl_val depth=0\");\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\n        eprintln!(\"[MGTRACE] kind=span_end site=infer.decl_val depth=0 value={:p}\", val_ty);\n        let declared = self.eval(0, empty_env, d.info().ty);\n        eprintln!(\"[MGTRACE] kind=eval site=infer.declared_type depth=0 value={:p}\", declared);'''
new='''        eprintln!(\"[MGTRACE] kind=role_begin role=subject site=infer.decl\");\n        eprintln!(\"[MGTRACE] kind=span_begin site=infer.decl_val depth=0\");\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\n        eprintln!(\"[MGTRACE] kind=span_end site=infer.decl_val depth=0 value={:p}\", val_ty);\n        eprintln!(\"[MGTRACE] kind=role_end role=subject site=infer.decl\");\n        eprintln!(\"[MGTRACE] kind=role_begin role=reference site=infer.decl\");\n        let declared = self.eval(0, empty_env, d.info().ty);\n        eprintln!(\"[MGTRACE] kind=eval site=infer.declared_type depth=0 value={:p}\", declared);\n        eprintln!(\"[MGTRACE] kind=role_end role=reference site=infer.decl\");'''
if old not in s: raise SystemExit('V12 declaration-role anchor missing')
s=s.replace(old,new,1)

marker="base_bin=BASE/'target/release/sokonanoda'\n"
helpers=r'''def role_range(ev, fail_idx, role):
    if fail_idx is None: return None
    end=None
    for i in range(fail_idx-1,-1,-1):
        if ev[i].get('kind')=='role_end' and ev[i].get('role')==role:
            end=i; break
    if end is None: return None
    begin=None
    for i in range(end-1,-1,-1):
        if ev[i].get('kind')=='role_begin' and ev[i].get('role')==role:
            begin=i; break
    return (begin,end) if begin is not None else None

def route_role(ev, fail_idx, role):
    rr=role_range(ev,fail_idx,role)
    if not rr: return None
    b,e=rr
    for x in reversed(ev[b:e+1]):
        m=mechanism(x)
        if m: return m
    return None

def route_shared_inputs(ev, fail_idx):
    a=role_range(ev,fail_idx,'subject'); b=role_range(ev,fail_idx,'reference')
    if not a or not b: return None
    lo=min(a[0],b[0]); hi=max(a[1],b[1])
    for x in reversed(ev[lo:hi+1]):
        m=mechanism(x)
        if m: return m
    return None

'''
if marker not in s: raise SystemExit('V12 helper insertion anchor missing')
s=s.replace(marker,helpers+marker,1)

# Replace V10's selection/evaluation tail. Same frozen fault construction; the only new information
# is a one-bit subject/reference role at the final verifier comparison.
pat=re.compile(r"pool=\[\]; supported=\[\].*\Z",re.S)
new_tail=r'''pool=[]; supported=[]
for c in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(c.relative_to(ARENA))
    if rel in EXCLUDE: continue
    trc,terr=run(trace_bin,c)
    if status(trc)!='accept' or not any(e.get('kind')=='projection_result' for e in events(terr)): continue
    frc,ferr=run(faulty,c)
    if status(frc)!='reject': continue
    ev=events(ferr); fi=failed_defeq_index(ev); sp=producer_span(ev,fi)
    if fi is None or ev[fi].get('site')!='infer.decl' or not sp: continue
    nearest=route_nearest_mechanism(ev,fi)
    span=route_producer_span(ev,fi)
    pointer=route_pointer_only(ev,fi)
    subject=route_role(ev,fi,'subject')
    reference=route_role(ev,fi,'reference')
    shared=route_shared_inputs(ev,fi)
    prod_ptrs=[e.get('value') for e in ev[:fi] if e.get('kind')=='projection_result' and e.get('value')]
    final_ptr=ev[fi].get('val')
    rec={'hash':hashlib.sha256(rel.encode()).hexdigest(),'case':rel,'nearest':nearest,'span':span,'pointer':pointer,'subject':subject,'reference':reference,'shared':shared,'producer_ptrs':prod_ptrs,'final_ptr':final_ptr}
    supported.append(rec)
    # Decisive morphology: chronology/coarse shared-input view is misled by reference EVAL;
    # raw identity is broken; one operand-role bit recovers the projection-producing subject path.
    if nearest=='EVAL' and shared=='EVAL' and span=='PROJECTION' and pointer is None and subject=='PROJECTION' and reference=='EVAL' and final_ptr not in prod_ptrs:
        pool.append(rec)

selected=sorted(pool,key=lambda x:x['hash'])[:2]
if len(selected)<2:
    report={'status':'R4_OPERAND_ROLE_OBSERVABILITY','reason':'fewer than two frozen source-distinct projection faults where subject/reference role separates projection ancestry from later reference eval','semantic_mismatches':0,'supported_projection_faults':supported,'qualifying_cases':pool}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)

rows=[]
for rec in selected:
    rel=rec['case']; case=ARENA/rel; _,ferr=run(faulty,case); ev=events(ferr); fi=failed_defeq_index(ev)
    nearest=route_nearest_mechanism(ev,fi); shared=route_shared_inputs(ev,fi); subject=route_role(ev,fi,'subject'); reference=route_role(ev,fi,'reference'); pointer=route_pointer_only(ev,fi); span=route_producer_span(ev,fi)
    policies={
      'BINARY':FAMILIES[:],
      'NEAREST_MECHANISM':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
      'SHARED_INPUTS':([shared]+[x for x in FAMILIES if x!=shared]) if shared else FAMILIES[:],
      'POINTER_ONLY':([pointer]+[x for x in FAMILIES if x!=pointer]) if pointer else FAMILIES[:],
      'PRODUCER_SPAN':([span]+[x for x in FAMILIES if x!=span]) if span else FAMILIES[:],
      'SUBJECT_ROLE':([subject]+[x for x in FAMILIES if x!=subject]) if subject else FAMILIES[:],
      'REFERENCE_ROLE_ABLATION':([reference]+[x for x in FAMILIES if x!=reference]) if reference else FAMILIES[:],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for cand in order:
            checker=trace_bin if cand=='PROJECTION' else faulty
            rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept': break
        arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
    rows.append({'case':rel,'nearest_route':nearest,'shared_inputs_route':shared,'subject_route':subject,'reference_route':reference,'pointer_route':pointer,'producer_span_route':span,'arms':arms})

summary={'status':'LIVE_OPERAND_CAUSAL_QUOTIENT_V12','semantic_mismatches':0,'episodes':len(rows),'selected':[x['case'] for x in selected],'rows':rows}
for arm in ['BINARY','NEAREST_MECHANISM','SHARED_INPUTS','POINTER_ONLY','PRODUCER_SPAN','SUBJECT_ROLE','REFERENCE_ROLE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['subject_vs_shared_factor']=summary['shared_inputs']['mean_verifier_calls']/summary['subject_role']['mean_verifier_calls']
summary['subject_vs_nearest_factor']=summary['nearest_mechanism']['mean_verifier_calls']/summary['subject_role']['mean_verifier_calls']
summary['role_bit_load_bearing']=summary['subject_role']['mean_verifier_calls'] < summary['shared_inputs']['mean_verifier_calls'] and summary['subject_role']['mean_verifier_calls'] < summary['reference_role_ablation']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if summary['subject_role']['repair_rate']!=1.0 or summary['subject_role']['mean_verifier_calls']!=1.0: raise SystemExit('subject-role repair gate failed')
if not summary['role_bit_load_bearing']: raise SystemExit('operand-role distinction was not deletion-load-bearing')
'''
s,n=pat.subn(new_tail,s,count=1)
if n!=1: raise SystemExit(f'V12 tail replacement count={n}')

p.write_text(s)
print('patched V12 runner for failed-comparison operand causal quotient')
