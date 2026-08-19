#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('scripts/run_developmental_checker_span_v9.py')
s = p.read_text()
s = s.replace('results/developmental-checker-repair-v9', 'results/developmental-checker-causal-quotient-v12')
s = s.replace("'LIVE_PRODUCER_SPAN_V9'", "'LIVE_OPERAND_CAUSAL_QUOTIENT_V12'")

# V12 adds no Rust instrumentation.  It tests one representation distinction already
# present in the validated V9 trace:
#   subject   = the computation span that produced the rejected left operand
#   reference = the later declared-type EVAL that produced the right operand
# Collapsing these two regions makes the later EVAL win by chronology.
marker = "base_bin=BASE/'target/release/sokonanoda'\n"
helpers = r'''def route_pointer_only(ev, fail_idx):
    if fail_idx is None: return None
    val = ev[fail_idx].get('val')
    if not val: return None
    for e in reversed(ev[:fail_idx]):
        if e.get('kind') == 'projection_result' and e.get('value') == val:
            return 'PROJECTION'
    return None

def route_subject(ev, fail_idx):
    return route_producer_span(ev, fail_idx)

def reference_eval_index(ev, fail_idx):
    sp = producer_span(ev, fail_idx)
    if fail_idx is None or not sp: return None
    _, end = sp
    for i in range(fail_idx - 1, end, -1):
        e = ev[i]
        if e.get('kind') == 'eval' and e.get('site') == 'infer.declared_type':
            return i
    return None

def route_reference(ev, fail_idx):
    return 'EVAL' if reference_eval_index(ev, fail_idx) is not None else None

def route_collapsed_inputs(ev, fail_idx):
    # Quotient away subject/reference role and choose the latest mechanism in the
    # combined operand-building region.  In the displaced morphology this is EVAL.
    sp = producer_span(ev, fail_idx)
    if fail_idx is None or not sp: return None
    begin, _ = sp
    for e in reversed(ev[begin:fail_idx]):
        m = mechanism(e)
        if m: return m
    return None

'''
if marker not in s:
    raise SystemExit('V12 v3 helper insertion anchor missing')
s = s.replace(marker, helpers + marker, 1)

pat = re.compile(r'pool=\[\]; supported=\[\].*\Z', re.S)
new_tail = r'''pool=[]; supported=[]
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
    subject=route_subject(ev,fi)
    reference=route_reference(ev,fi)
    collapsed=route_collapsed_inputs(ev,fi)
    pointer=route_pointer_only(ev,fi)
    prod_ptrs=[e.get('value') for e in ev[:fi] if e.get('kind')=='projection_result' and e.get('value')]
    final_ptr=ev[fi].get('val')
    rec={'hash':hashlib.sha256(rel.encode()).hexdigest(),'case':rel,'nearest':nearest,
         'subject':subject,'reference':reference,'collapsed':collapsed,'pointer':pointer,
         'producer_ptrs':prod_ptrs,'final_ptr':final_ptr}
    supported.append(rec)
    if (nearest=='EVAL' and collapsed=='EVAL' and subject=='PROJECTION' and
        reference=='EVAL' and pointer is None and final_ptr not in prod_ptrs):
        pool.append(rec)

selected=sorted(pool,key=lambda x:x['hash'])[:2]
if len(selected)<2:
    report={'status':'R4_OPERAND_ROLE_OBSERVABILITY',
            'reason':'fewer than two frozen source-distinct projection faults where one subject/reference distinction separates the projection-producing subject from the later reference EVAL',
            'semantic_mismatches':0,'supported_projection_faults':supported,'qualifying_cases':pool}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)

rows=[]
for rec in selected:
    rel=rec['case']; case=ARENA/rel; _,ferr=run(faulty,case); ev=events(ferr); fi=failed_defeq_index(ev)
    nearest=route_nearest_mechanism(ev,fi)
    subject=route_subject(ev,fi)
    reference=route_reference(ev,fi)
    collapsed=route_collapsed_inputs(ev,fi)
    pointer=route_pointer_only(ev,fi)
    policies={
      'BINARY':FAMILIES[:],
      'NEAREST_MECHANISM':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
      'COLLAPSED_INPUTS':([collapsed]+[x for x in FAMILIES if x!=collapsed]) if collapsed else FAMILIES[:],
      'POINTER_ONLY':([pointer]+[x for x in FAMILIES if x!=pointer]) if pointer else FAMILIES[:],
      'SUBJECT_ROLE':([subject]+[x for x in FAMILIES if x!=subject]) if subject else FAMILIES[:],
      'REFERENCE_ROLE_ABLATION':([reference]+[x for x in FAMILIES if x!=reference]) if reference else FAMILIES[:],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for cand in order:
            # PROJECTION is the only repairing intervention in this frozen fault game.
            checker=trace_bin if cand=='PROJECTION' else faulty
            rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept': break
        arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
    rows.append({'case':rel,'nearest_route':nearest,'collapsed_inputs_route':collapsed,
                 'subject_route':subject,'reference_route':reference,'pointer_route':pointer,'arms':arms})

summary={'status':'LIVE_OPERAND_CAUSAL_QUOTIENT_V12','semantic_mismatches':0,'episodes':len(rows),
         'selected':[x['case'] for x in selected],'rows':rows}
for arm in ['BINARY','NEAREST_MECHANISM','COLLAPSED_INPUTS','POINTER_ONLY','SUBJECT_ROLE','REFERENCE_ROLE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),
                          'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['subject_vs_collapsed_factor']=summary['collapsed_inputs']['mean_verifier_calls']/summary['subject_role']['mean_verifier_calls']
summary['subject_vs_nearest_factor']=summary['nearest_mechanism']['mean_verifier_calls']/summary['subject_role']['mean_verifier_calls']
summary['role_bit_load_bearing']=(summary['subject_role']['mean_verifier_calls'] < summary['collapsed_inputs']['mean_verifier_calls'] and
                                  summary['subject_role']['mean_verifier_calls'] < summary['reference_role_ablation']['mean_verifier_calls'])
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if summary['subject_role']['repair_rate']!=1.0 or summary['subject_role']['mean_verifier_calls']!=1.0:
    raise SystemExit('subject-role repair gate failed')
if not summary['role_bit_load_bearing']:
    raise SystemExit('subject/reference distinction was not deletion-load-bearing')
'''
s,n = pat.subn(new_tail,s,count=1)
if n != 1:
    raise SystemExit(f'V12 v3 tail replacement count={n}')

p.write_text(s)
print('patched V12 v3: analysis-only subject/reference causal quotient')
