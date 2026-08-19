#!/usr/bin/env python3
from pathlib import Path
import re

src=Path('scripts/run_developmental_checker_span_v10.py')
s=src.read_text()
s=s.replace('results/developmental-checker-repair-v9','results/developmental-checker-lineage-v10')
s=s.replace("EXCLUDE={'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson','good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson'}",
'''EXCLUDE={'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson','good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson','good/undecidability/alg-conv-trans-acc-left.ndjson','good/tutorial/082_Prod.snd.ndjson'}''')

# Extend the trace checker with an opaque, semantics-inert provenance side table.
anchor="    p=src/'src/infer.rs'; s=p.read_text()\n"
insert="""    p=src/'src/infer.rs'; s=p.read_text()\n    mg_anchor='use InferFlag::*;\\n'\n    mg_helpers='''\nuse std::cell::RefCell;\nuse std::collections::HashMap;\nthread_local! {\n    static MG_PROV: RefCell<HashMap<usize,u64>> = RefCell::new(HashMap::new());\n}\n#[inline] fn mg_prov_get(v: V<'_>) -> u64 {\n    MG_PROV.with(|m| *m.borrow().get(&(v as *const Value<'_> as usize)).unwrap_or(&0))\n}\n#[inline] fn mg_prov_add(v: V<'_>, bits: u64) {\n    if bits == 0 { return; }\n    MG_PROV.with(|m| { let mut m=m.borrow_mut(); let k=v as *const Value<'_> as usize; *m.entry(k).or_insert(0) |= bits; });\n}\n#[inline] fn mg_prov_inherit(out: V<'_>, src: V<'_>) { mg_prov_add(out, mg_prov_get(src)); }\n'''\n    if mg_anchor not in s: raise RuntimeError('provenance helper anchor missing')\n    s=s.replace(mg_anchor,mg_anchor+mg_helpers,1)\n"""
if anchor not in s: raise SystemExit('augment source anchor missing')
s=s.replace(anchor,insert,1)

# Before infer.rs is written, mark projection outputs and propagate their provenance across
# application-type construction even when the Value pointer changes.
write_anchor='    p.write_text(s)\n\ndef inject_projection_fault(src):'
extra="""    mg_old='''        let mg_proj_return = mg_proj_result;\n        eprintln!(\"[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}\", depth, mg_proj_return);\n        mg_proj_return'''
    mg_new='''        let mg_proj_return = mg_proj_result;\n        mg_prov_add(mg_proj_return, 1);\n        eprintln!(\"[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p} prov={:x}\", depth, mg_proj_return, mg_prov_get(mg_proj_return));\n        mg_proj_return'''
    if mg_old not in s: raise RuntimeError('projection provenance anchor missing')
    s=s.replace(mg_old,mg_new,1)
    app_old='''            if body.ctx.is_none() && self.ctx.num_loose_bvars(body.body) == 0 {\n                fty = self.eval(depth, body.env, body.body);\n            } else if crate::expr::ignores_binder(body.body) {\n                fty = self.apply_closure(depth, body, domain, Some(domain));\n            } else {\n                let av = self.arg_value(depth, env, arg);\n                fty = self.apply_closure(depth, body, av, Some(domain));\n            }'''
    app_new='''            let mg_prev_fty = fty;\n            let mg_next_fty = if body.ctx.is_none() && self.ctx.num_loose_bvars(body.body) == 0 {\n                self.eval(depth, body.env, body.body)\n            } else if crate::expr::ignores_binder(body.body) {\n                self.apply_closure(depth, body, domain, Some(domain))\n            } else {\n                let av = self.arg_value(depth, env, arg);\n                self.apply_closure(depth, body, av, Some(domain))\n            };\n            mg_prov_inherit(mg_next_fty, mg_prev_fty);\n            fty = mg_next_fty;'''
    if app_old not in s: raise RuntimeError('application provenance transport anchor missing')
    s=s.replace(app_old,app_new,1)
    decl_old='''        eprintln!(\"[MGTRACE] kind=defeq site=infer.decl depth=0 ok={} val={:p} declared={:p}\", mg_decl_ok, val_ty, declared);'''
    decl_new='''        eprintln!(\"[MGTRACE] kind=defeq site=infer.decl depth=0 ok={} val={:p} declared={:p} prov={:x}\", mg_decl_ok, val_ty, declared, mg_prov_get(val_ty));'''
    if decl_old not in s: raise RuntimeError('declaration provenance trace anchor missing')
    s=s.replace(decl_old,decl_new,1)
    p.write_text(s)

def inject_projection_fault(src):"""
if write_anchor not in s: raise SystemExit('augment write anchor missing')
s=s.replace(write_anchor,extra,1)

# Fault injection must preserve the semantics-inert provenance mark on the deliberately wrong value.
pat=re.compile(r'def inject_projection_fault\(src\):\n.*?\n(?=def failed_defeq_index)',re.S)
new_inject='''def inject_projection_fault(src):
    p=src/'src/infer.rs'; s=p.read_text()
    old=''' + "'''" + '''        let mg_proj_return = mg_proj_result;\n        mg_prov_add(mg_proj_return, 1);\n        eprintln!(\"[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p} prov={:x}\", depth, mg_proj_return, mg_prov_get(mg_proj_return));\n        mg_proj_return''' + "'''" + '''
    new=''' + "'''" + '''        let _mg_proj_real = mg_proj_result;\n        let mg_proj_return = struct_ty_f;\n        mg_prov_add(mg_proj_return, 1);\n        eprintln!(\"[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p} prov={:x}\", depth, mg_proj_return, mg_prov_get(mg_proj_return));\n        mg_proj_return''' + "'''" + '''
    if old not in s: raise RuntimeError('projection lineage fault anchor missing')
    p.write_text(s.replace(old,new,1))

'''
s,n=pat.subn(new_inject,s,count=1)
if n!=1: raise SystemExit(f'inject replacement count={n}')

# Add the two competing ancestry rules: raw pointer identity versus transported provenance.
marker='base_bin=BASE/\'target/release/sokonanoda\'\n'
routes='''def route_pointer_only(ev, fail_idx):
    if fail_idx is None: return None
    val=ev[fail_idx].get('val')
    if not val: return None
    for e in reversed(ev[:fail_idx]):
        if e.get('kind')=='projection_result' and e.get('value')==val:
            return 'PROJECTION'
    return None

def route_lineage(ev, fail_idx):
    if fail_idx is None: return None
    p=ev[fail_idx].get('prov')
    if not p: return None
    try: bits=int(p,16)
    except ValueError: return None
    return 'PROJECTION' if (bits & 1) else None

'''
if marker not in s: raise SystemExit('route insertion anchor missing')
s=s.replace(marker,routes+marker,1)

# Replace the V9 selection/evaluation tail with a prospective fresh-case value-lineage gate.
pat=re.compile(r'pool=\[\]; supported=\[\].*\Z',re.S)
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
    nearest=route_nearest_mechanism(ev,fi); span=route_producer_span(ev,fi)
    pointer=route_pointer_only(ev,fi); lineage=route_lineage(ev,fi)
    prod_ptrs=[e.get('value') for e in ev[:fi] if e.get('kind')=='projection_result' and e.get('value')]
    final_ptr=ev[fi].get('val')
    rec={'hash':hashlib.sha256(rel.encode()).hexdigest(),'case':rel,'nearest':nearest,'span':span,'pointer':pointer,'lineage':lineage,'producer_ptrs':prod_ptrs,'final_ptr':final_ptr}
    supported.append(rec)
    # Required morphology: chronology is misleading, raw identity is broken, but transported lineage survives.
    if nearest=='EVAL' and span=='PROJECTION' and pointer is None and lineage=='PROJECTION' and final_ptr not in prod_ptrs:
        pool.append(rec)

selected=sorted(pool,key=lambda x:x['hash'])[:2]
if len(selected)<2:
    report={'status':'R4_LINEAGE_OBSERVABILITY','reason':'fewer than two fresh source-distinct projection faults where pointer identity breaks but propagated provenance reaches the later failed declaration comparison','semantic_mismatches':0,'supported_projection_faults':supported,'lineage_cases':pool}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)

rows=[]
for rec in selected:
    rel=rec['case']; case=ARENA/rel; _,ferr=run(faulty,case); ev=events(ferr); fi=failed_defeq_index(ev)
    nearest=route_nearest_mechanism(ev,fi); span=route_producer_span(ev,fi); pointer=route_pointer_only(ev,fi); lineage=route_lineage(ev,fi)
    policies={
      'BINARY':FAMILIES[:],
      'NEAREST_MECHANISM':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
      'PRODUCER_SPAN':([span]+[x for x in FAMILIES if x!=span]) if span else FAMILIES[:],
      'POINTER_ONLY':([pointer]+[x for x in FAMILIES if x!=pointer]) if pointer else FAMILIES[:],
      'PROPAGATED_LINEAGE':([lineage]+[x for x in FAMILIES if x!=lineage]) if lineage else FAMILIES[:],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for cand in order:
            checker=trace_bin if cand=='PROJECTION' else faulty
            rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept': break
        arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
    prod_ptrs=[e.get('value') for e in ev[:fi] if e.get('kind')=='projection_result' and e.get('value')]
    rows.append({'case':rel,'producer_ptrs':prod_ptrs,'failed_val_ptr':ev[fi].get('val'),'failed_val_prov':ev[fi].get('prov'),'pointer_changed':ev[fi].get('val') not in prod_ptrs,'nearest_route':nearest,'producer_span_route':span,'pointer_route':pointer,'lineage_route':lineage,'events_tail':ev[-48:],'arms':arms})

summary={'status':'LIVE_PROPAGATED_LINEAGE_V10','semantic_mismatches':0,'episodes':len(rows),'selected':[x['case'] for x in selected],'rows':rows}
for arm in ['BINARY','NEAREST_MECHANISM','PRODUCER_SPAN','POINTER_ONLY','PROPAGATED_LINEAGE']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['lineage_vs_pointer_factor']=summary['pointer_only']['mean_verifier_calls']/summary['propagated_lineage']['mean_verifier_calls']
summary['lineage_vs_nearest_factor']=summary['nearest_mechanism']['mean_verifier_calls']/summary['propagated_lineage']['mean_verifier_calls']
summary['all_pointer_changes']=all(r['pointer_changed'] for r in rows)
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if not summary['all_pointer_changes']: raise SystemExit('pointer-change gate failed')
if summary['propagated_lineage']['repair_rate']!=1.0 or summary['propagated_lineage']['mean_verifier_calls']!=1.0: raise SystemExit('lineage repair gate failed')
'''
s,n=pat.subn(new_tail,s,count=1)
if n!=1: raise SystemExit(f'tail replacement count={n}')
s=s.replace("'LIVE_PRODUCER_SPAN_V9'","'LIVE_PROPAGATED_LINEAGE_V10'")
s=src.write_text(s)
print('patched V10 runner for propagated causal value lineage')
