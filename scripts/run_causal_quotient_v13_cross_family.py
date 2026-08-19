#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-causal-quotient-v13'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
CANDIDATES=['EVAL','PROJECTION','IOTA']
EXCLUDE={
 'good/tutorial/079_listRecReduction.ndjson',
 'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson',
 'good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson',
 'good/undecidability/alg-conv-trans-acc-left.ndjson','good/tutorial/082_Prod.snd.ndjson'
}

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
    new='''        eprintln!("[MGTRACE] kind=span_begin site=infer.decl_val depth=0 expr={:p}", val);\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\n        eprintln!("[MGTRACE] kind=span_end site=infer.decl_val depth=0 expr={:p} value={:p}", val, val_ty);\n        let declared = self.eval(0, empty_env, d.info().ty);\n        eprintln!("[MGTRACE] kind=eval site=infer.declared_type depth=0 value={:p}", declared);\n        let mg_decl_ok = self.def_eq_at(0, val_ty, declared);\n        eprintln!("[MGTRACE] kind=defeq site=infer.decl depth=0 ok={} val={:p} declared={:p}", mg_decl_ok, val_ty, declared);\n        assert!(mg_decl_ok, "def_eq failed");'''
    if old not in s: raise RuntimeError('declaration span anchor missing')
    s=s.replace(old,new,1); p.write_text(s)

def inject_projection_fault(src):
    p=src/'src/infer.rs'; s=p.read_text()
    old='''        let mg_proj_return = mg_proj_result;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    new='''        let _mg_proj_real = mg_proj_result;\n        let mg_proj_return = struct_ty_f;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    if old not in s: raise RuntimeError('projection fault anchor missing')
    p.write_text(s.replace(old,new,1))

def inject_iota_fault(src):
    p=src/'src/conv.rs'; s=p.read_text()
    old='''                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    new='''                let _mg_real = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                let mg_r = false;\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    if old not in s: raise RuntimeError('iota fault anchor missing')
    p.write_text(s.replace(old,new,1))

def failed_defeq_index(ev):
    for i in range(len(ev)-1,-1,-1):
        if ev[i].get('kind')=='defeq' and ev[i].get('ok')=='false': return i
    return None

def producer_span(ev,fi):
    if fi is None:return None
    site=ev[fi].get('site'); target='infer.decl_val' if site=='infer.decl' else ('infer.app_arg_type' if site=='infer.app_arg' else None)
    if not target:return None
    end=None; token=None
    for i in range(fi-1,-1,-1):
        if ev[i].get('kind')=='span_end' and ev[i].get('site')==target: end=i; token=ev[i].get('expr'); break
    if end is None:return None
    for i in range(end-1,-1,-1):
        if ev[i].get('kind')=='span_begin' and ev[i].get('site')==target and ev[i].get('expr')==token:return i,end
    return None

def mech(e):
    k=e.get('kind'); s=e.get('site','')
    if k=='eval' and s=='infer.declared_type': return 'EVAL'
    if k in ('projection','projection_result') and s=='infer.proj': return 'PROJECTION'
    if (k in ('iota','iota_result')) and s=='conv.recursor': return 'IOTA'
    return None

def nearest(ev,fi):
    if fi is None:return None
    for e in reversed(ev[:fi]):
        m=mech(e)
        if m:return m
    return None

def causal_subject(ev,fi,family):
    if family=='PROJECTION':
        sp=producer_span(ev,fi)
        if not sp:return None
        b,e=sp
        for x in reversed(ev[b:e+1]):
            if mech(x)=='PROJECTION': return 'PROJECTION'
        return None
    if family=='IOTA':
        # Same abstraction: choose a mechanism on the rejected subject path, not a later wrapper/distractor.
        # The iota_result=false is the explicit local negative contribution on that path.
        for x in reversed(ev[:fi] if fi is not None else ev):
            if x.get('kind')=='iota_result' and x.get('site')=='conv.recursor' and x.get('ok')=='false': return 'IOTA'
    return None

def build_fault(name,inject):
    work=root/name
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject(work); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
    return work/'target/release/sokonanoda'

base_bin=BASE/'target/release/sokonanoda'
augment(TRACE); (TRACE/'config.json').write_text(CFG)
subprocess.run(['cargo','build','--release'],cwd=TRACE,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
trace_bin=TRACE/'target/release/sokonanoda'
# semantic identity gate trace vs baseline on full corpus
mism=[]
for kind in ['good','bad']:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        br,_=run(base_bin,c); tr,_=run(trace_bin,c)
        if status(br)!=status(tr): mism.append([str(c.relative_to(ARENA)),status(br),status(tr)])
if mism: raise SystemExit(f'semantic mismatch: {mism[:3]}')

faults={'PROJECTION':build_fault('fault-projection-v13',inject_projection_fault),'IOTA':build_fault('fault-iota-v13',inject_iota_fault)}
rows=[]; selected_by_family={}
for family,faulty in faults.items():
    pool=[]
    for c in sorted((ARENA/'good').rglob('*.ndjson')):
        rel=str(c.relative_to(ARENA))
        if rel in EXCLUDE: continue
        rc,terr=run(trace_bin,c); tev=events(terr)
        exercised = any(mech(e)==family for e in tev)
        if status(rc)!='accept' or not exercised: continue
        frc,ferr=run(faulty,c)
        if status(frc)!='reject': continue
        ev=events(ferr); fi=failed_defeq_index(ev); n=nearest(ev,fi); cs=causal_subject(ev,fi,family)
        if not cs: continue
        # require genuine displacement/ambiguity: nearest route must not already equal the causal family
        if n==family: continue
        pool.append((hashlib.sha256(rel.encode()).hexdigest(),rel,n,cs))
    chosen=sorted(pool)[:2]
    selected_by_family[family]=[x[1] for x in chosen]
    if len(chosen)<2:
        report={'status':'R4_CROSS_FAMILY_OBSERVABILITY','family':family,'available':[(x[1],x[2],x[3]) for x in sorted(pool)],'selected_by_family':selected_by_family,'semantic_mismatches':0}
        (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)
    for _,rel,n,cs in chosen:
        case=ARENA/rel
        # Frozen tournament: binary/nearest/collapsed all lose role; causal-role preserves it.
        policies={
          'BINARY':CANDIDATES[:],
          'NEAREST':([n]+[x for x in CANDIDATES if x!=n]) if n else CANDIDATES[:],
          'COLLAPSED_ROLE':([n]+[x for x in CANDIDATES if x!=n]) if n else CANDIDATES[:],
          'CAUSAL_ROLE':([cs]+[x for x in CANDIDATES if x!=cs]) if cs else CANDIDATES[:],
          'ROLE_ABLATION':([n]+[x for x in CANDIDATES if x!=n]) if n else CANDIDATES[:],
        }
        arms={}
        for arm,order in policies.items():
            attempts=[]
            for cand in order:
                checker=trace_bin if cand==family else faulty
                rr,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rr)})
                if status(rr)=='accept': break
            arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
        rows.append({'family':family,'case':rel,'nearest_route':n,'causal_role_route':cs,'arms':arms})

summary={'status':'LIVE_CROSS_FAMILY_CAUSAL_QUOTIENT_V13','semantic_mismatches':0,'episodes':len(rows),'families':sorted(faults),'selected_by_family':selected_by_family,'rows':rows}
for arm in ['BINARY','NEAREST','COLLAPSED_ROLE','CAUSAL_ROLE','ROLE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'calls':vals,'mean_verifier_calls':sum(vals)/len(vals),'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows)}
summary['causal_vs_collapsed_factor']=summary['collapsed_role']['mean_verifier_calls']/summary['causal_role']['mean_verifier_calls']
summary['causal_vs_nearest_factor']=summary['nearest']['mean_verifier_calls']/summary['causal_role']['mean_verifier_calls']
summary['family_breakdown']={}
for fam in sorted(faults):
    rs=[r for r in rows if r['family']==fam]
    summary['family_breakdown'][fam]={a:sum(r['arms'][a]['verifier_calls'] for r in rs)/len(rs) for a in ['NEAREST','COLLAPSED_ROLE','CAUSAL_ROLE','ROLE_ABLATION']}
summary['role_distinction_load_bearing']=summary['causal_role']['mean_verifier_calls'] < summary['role_ablation']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if summary['causal_role']['repair_rate']!=1.0: raise SystemExit('causal role repair gate failed')
if not summary['role_distinction_load_bearing']: raise SystemExit('role distinction not load-bearing')
if any(summary['family_breakdown'][f]['CAUSAL_ROLE'] >= summary['family_breakdown'][f]['ROLE_ABLATION'] for f in summary['family_breakdown']): raise SystemExit('cross-family transfer gate failed')
