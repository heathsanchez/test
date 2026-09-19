#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-repair-v8'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['IOTA','UNFOLD','PROJECTION']
EXCLUDE={'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson'}

def run(bin_path,case):
    cfg=bin_path.parent.parent.parent/'config.json'
    with case.open('rb') as f:
        cp=subprocess.run([str(bin_path),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    return cp.returncode,cp.stderr.decode('utf-8','replace')
def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')
def events(stderr):
    xs=[]
    for line in stderr.splitlines():
        if not line.startswith('[MGTRACE] '): continue
        d={}
        for tok in line[10:].split():
            if '=' in tok:
                k,v=tok.split('=',1); d[k]=v
        xs.append(d)
    return xs

def augment(src):
    p=src/'src/infer.rs'; s=p.read_text()
    old='''                let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\n                let mg_ok = self.conv_types_at(depth, domain, arg_ty);\n                eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'''
    new='''                eprintln!("[MGTRACE] kind=span_begin site=infer.app_arg_type depth={} expr={:p}", depth, arg);\n                let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\n                eprintln!("[MGTRACE] kind=span_end site=infer.app_arg_type depth={} expr={:p} value={:p}", depth, arg, arg_ty);\n                let mg_ok = self.conv_types_at(depth, domain, arg_ty);\n                eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={} domain={:p} arg={:p}", depth, mg_ok, domain, arg_ty);'''
    if old not in s: raise RuntimeError('app span anchor missing')
    s=s.replace(old,new,1)

    old='''        match self.force_all(depth, cur) {\n            Value::Pi { domain, .. } => {\n                if struct_ty_is_prop && !self.is_prop_type(depth, domain) {\n                    panic!("projection of a non-proof field from a Prop structure")\n                }\n                *domain\n            }\n            _ => panic!("ran out of constructor telescope getting projection field"),\n        }'''
    new='''        let mg_proj_result = match self.force_all(depth, cur) {\n            Value::Pi { domain, .. } => {\n                if struct_ty_is_prop && !self.is_prop_type(depth, domain) {\n                    panic!("projection of a non-proof field from a Prop structure")\n                }\n                *domain\n            }\n            _ => panic!("ran out of constructor telescope getting projection field"),\n        };\n        let mg_proj_return = mg_proj_result;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    if old not in s: raise RuntimeError('projection result anchor missing')
    s=s.replace(old,new,1)

    old='''        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\n        let declared = self.eval(0, empty_env, d.info().ty);\n        assert!(self.def_eq_at(0, val_ty, declared), "def_eq failed");'''
    new='''        eprintln!("[MGTRACE] kind=span_begin site=infer.decl_val depth=0 expr={:p}", val);\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\n        eprintln!("[MGTRACE] kind=span_end site=infer.decl_val depth=0 expr={:p} value={:p}", val, val_ty);\n        let declared = self.eval(0, empty_env, d.info().ty);\n        let mg_decl_ok = self.def_eq_at(0, val_ty, declared);\n        eprintln!("[MGTRACE] kind=defeq site=infer.decl depth=0 ok={} val={:p} declared={:p}", mg_decl_ok, val_ty, declared);\n        assert!(mg_decl_ok, "def_eq failed");'''
    if old not in s: raise RuntimeError('declaration span anchor missing')
    s=s.replace(old,new,1)
    p.write_text(s)

def inject_projection_fault(src):
    p=src/'src/infer.rs'; s=p.read_text()
    old='''        let mg_proj_return = mg_proj_result;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    new='''        let _mg_proj_real = mg_proj_result;\n        let mg_proj_return = struct_ty_f;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    if old not in s: raise RuntimeError('projection fault anchor missing')
    p.write_text(s.replace(old,new,1))

def failed_defeq_index(ev):
    for i in range(len(ev)-1,-1,-1):
        if ev[i].get('kind')=='defeq' and ev[i].get('ok')=='false': return i
    return None

def producer_span(ev, fail_idx):
    if fail_idx is None: return None
    f=ev[fail_idx]; site=f.get('site')
    target='infer.decl_val' if site=='infer.decl' else ('infer.app_arg_type' if site=='infer.app_arg' else None)
    if not target: return None
    # The relevant producer is the latest completed target span before the failed consumer.
    end_idx=None; token=None
    for i in range(fail_idx-1,-1,-1):
        if ev[i].get('kind')=='span_end' and ev[i].get('site')==target:
            end_idx=i; token=ev[i].get('expr'); break
    if end_idx is None: return None
    begin_idx=None
    for i in range(end_idx-1,-1,-1):
        if ev[i].get('kind')=='span_begin' and ev[i].get('site')==target and ev[i].get('expr')==token:
            begin_idx=i; break
    if begin_idx is None: return None
    return begin_idx,end_idx

def mechanism(e):
    k=e.get('kind'); s=e.get('site','')
    if k in ('iota','iota_result') and s=='conv.recursor': return 'IOTA'
    if k=='unfold' and s=='conv.unfold_pair': return 'UNFOLD'
    if k in ('projection','projection_result') and s=='infer.proj': return 'PROJECTION'
    return None

def route_nearest_mechanism(ev, fail_idx):
    if fail_idx is None: return None
    for e in reversed(ev[:fail_idx]):
        m=mechanism(e)
        if m: return m
    return None

def route_producer_span(ev, fail_idx):
    sp=producer_span(ev,fail_idx)
    if not sp: return None
    b,e=sp
    # Prefer the last mechanism inside the computation that produced the rejected input.
    for x in reversed(ev[b:e+1]):
        m=mechanism(x)
        if m: return m
    return None

def distractors_after_span(ev, fail_idx):
    sp=producer_span(ev,fail_idx)
    if not sp: return []
    _,end=sp
    return [m for m in (mechanism(x) for x in ev[end+1:fail_idx]) if m]

base_bin=BASE/'target/release/sokonanoda'
augment(TRACE); (TRACE/'config.json').write_text(CFG)
subprocess.run(['cargo','build','--release'],cwd=TRACE,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
trace_bin=TRACE/'target/release/sokonanoda'

# Full semantic identity gate.
errs=[]; mism=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        brc,_=run(base_bin,c); trc,_=run(trace_bin,c); bs=status(brc); ts=status(trc)
        if bs!=expected: errs.append([str(c.relative_to(ARENA)),expected,bs])
        if bs!=ts: mism.append([str(c.relative_to(ARENA)),bs,ts])
if errs or mism: raise SystemExit(f'semantic gate failed base={errs[:3]} mism={mism[:3]}')

work=root/'fault-projection'
if work.exists(): shutil.rmtree(work)
shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
inject_projection_fault(work); (work/'config.json').write_text(CFG)
subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
faulty=work/'target/release/sokonanoda'

pool=[]; supported=[]
for c in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(c.relative_to(ARENA))
    if rel in EXCLUDE: continue
    trc,terr=run(trace_bin,c)
    if status(trc)!='accept' or not any(e.get('kind')=='projection_result' for e in events(terr)): continue
    frc,ferr=run(faulty,c)
    if status(frc)!='reject': continue
    ev=events(ferr); fi=failed_defeq_index(ev); sp=producer_span(ev,fi)
    if not sp: continue
    ds=distractors_after_span(ev,fi)
    rec={'hash':hashlib.sha256(rel.encode()).hexdigest(),'case':rel,'distractors':ds,'nearest':route_nearest_mechanism(ev,fi),'span':route_producer_span(ev,fi)}
    supported.append(rec)
    if ds: pool.append(rec)

selected=sorted(pool,key=lambda x:x['hash'])[:2]
if len(selected)<2:
    report={'status':'R4_OBSERVABILITY','reason':'fewer than two source-distinct projection faults with post-producer semantic distractors','semantic_mismatches':0,'supported_projection_faults':supported,'distractor_cases':pool}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)

rows=[]
for rec in selected:
    rel=rec['case']; case=ARENA/rel; _,ferr=run(faulty,case); ev=events(ferr); fi=failed_defeq_index(ev)
    nearest=route_nearest_mechanism(ev,fi); span=route_producer_span(ev,fi)
    policies={
      'BINARY':FAMILIES[:],
      'NEAREST_MECHANISM':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
      'PRODUCER_SPAN':([span]+[x for x in FAMILIES if x!=span]) if span else FAMILIES[:],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for cand in order:
            checker=trace_bin if cand=='PROJECTION' else faulty
            rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept': break
        arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
    rows.append({'case':rel,'distractors':distractors_after_span(ev,fi),'nearest_route':nearest,'producer_span_route':span,'events_tail':ev[-48:],'arms':arms})

summary={'status':'LIVE_PRODUCER_SPAN_V8','semantic_mismatches':0,'episodes':len(rows),'selected':[x['case'] for x in selected],'rows':rows}
for arm in ['BINARY','NEAREST_MECHANISM','PRODUCER_SPAN']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['producer_span_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['producer_span']['mean_verifier_calls']
summary['producer_span_vs_nearest_factor']=summary['nearest_mechanism']['mean_verifier_calls']/summary['producer_span']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
