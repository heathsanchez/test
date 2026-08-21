#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-repair-v7'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['IOTA','PROJECTION']
EXCLUDE={
 'good/tutorial/079_listRecReduction.ndjson',
 'good/tutorial/081_And.right.ndjson',
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

def augment_provenance(src):
    p=src/'src/infer.rs'; s=p.read_text()
    old='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'
    new='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={} domain={:p} arg={:p}", depth, mg_ok, domain, arg_ty);'
    if old not in s: raise RuntimeError('app defeq trace anchor missing')
    s=s.replace(old,new,1)
    old='''        match self.force_all(depth, cur) {\n            Value::Pi { domain, .. } => {\n                if struct_ty_is_prop && !self.is_prop_type(depth, domain) {\n                    panic!("projection of a non-proof field from a Prop structure")\n                }\n                *domain\n            }\n            _ => panic!("ran out of constructor telescope getting projection field"),\n        }'''
    new='''        let mg_proj_result = match self.force_all(depth, cur) {\n            Value::Pi { domain, .. } => {\n                if struct_ty_is_prop && !self.is_prop_type(depth, domain) {\n                    panic!("projection of a non-proof field from a Prop structure")\n                }\n                *domain\n            }\n            _ => panic!("ran out of constructor telescope getting projection field"),\n        };\n        let mg_proj_return = mg_proj_result;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    if old not in s: raise RuntimeError('projection result anchor missing')
    s=s.replace(old,new,1)
    p.write_text(s)

def natural_family(ev):
    kinds={e.get('kind') for e in ev}; sites={e.get('site') for e in ev}
    if 'iota' in kinds and 'conv.recursor' in sites: return 'IOTA'
    if 'projection_result' in kinds and 'infer.proj' in sites: return 'PROJECTION'
    return None

def route_nearest(ev):
    for e in reversed(ev):
        if e.get('kind')=='panic': continue
        s=e.get('site',''); k=e.get('kind','')
        if s=='conv.recursor' or k in ('iota','iota_result'): return 'IOTA'
        if s=='infer.proj' or k in ('projection','projection_result'): return 'PROJECTION'
        if s=='infer.app_arg': return 'IOTA'  # frozen terminal-symptom tie-break
    return None

def route_last_negative(ev):
    for e in reversed(ev):
        if e.get('ok')!='false': continue
        if e.get('kind')=='iota_result' or e.get('site')=='conv.recursor': return 'IOTA'
        # Generic downstream defeq failure has no mechanism identity.
        if e.get('site')=='infer.app_arg': return 'IOTA'
    return None

def route_provenance(ev):
    # Start from the latest failed application-defeq consumer.
    failed=None
    for e in reversed(ev):
        if e.get('site')=='infer.app_arg' and e.get('ok')=='false':
            failed=e; break
    if failed is not None:
        arg=failed.get('arg')
        if arg:
            # Follow opaque value identity back to its producer.
            for e in reversed(ev[:ev.index(failed)]):
                if e.get('kind')=='projection_result' and e.get('value')==arg:
                    return 'PROJECTION'
    # Boolean mechanisms expose their own negative result.
    for e in reversed(ev):
        if e.get('kind')=='iota_result' and e.get('ok')=='false': return 'IOTA'
    return None

def inject_fault(src,fam):
    if fam=='IOTA':
        p=src/'src/conv.rs'; s=p.read_text()
        old='''                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
        new='''                let _mg_real = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                let mg_r = false;\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    elif fam=='PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text()
        old='''        let mg_proj_return = mg_proj_result;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
        new='''        let _mg_proj_real = mg_proj_result;\n        let mg_proj_return = struct_ty_f;\n        eprintln!("[MGTRACE] kind=projection_result site=infer.proj depth={} value={:p}", depth, mg_proj_return);\n        mg_proj_return'''
    else: raise ValueError(fam)
    if old not in s: raise RuntimeError(f'fault anchor missing for {fam}')
    p.write_text(s.replace(old,new,1))

base_bin=BASE/'target/release/sokonanoda'
# Add provenance instrumentation before trace checker compilation.
augment_provenance(TRACE)
(TRACE/'config.json').write_text(CFG)
subprocess.run(['cargo','build','--release'],cwd=TRACE,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
trace_bin=TRACE/'target/release/sokonanoda'

# Hard full-corpus semantic identity gate after provenance instrumentation.
errs=[]; mism=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        brc,_=run(base_bin,c); trc,_=run(trace_bin,c)
        bs=status(brc); ts=status(trc)
        if bs!=expected: errs.append([str(c.relative_to(ARENA)),expected,bs])
        if bs!=ts: mism.append([str(c.relative_to(ARENA)),bs,ts])
if errs or mism: raise SystemExit(f'semantic gate failed base={errs[:3]} mism={mism[:3]}')

# Build one displaced faulted checker per mechanism.
fault_bins={}
for fam in FAMILIES:
    work=root/f'fault-{fam.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_fault(work,fam); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
    fault_bins[fam]=work/'target/release/sokonanoda'

# Prospectively deterministic source-distinct cases: natural mechanism use + fault discriminator.
pools={f:[] for f in FAMILIES}
for c in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(c.relative_to(ARENA))
    if rel in EXCLUDE: continue
    trc,terr=run(trace_bin,c)
    if status(trc)!='accept': continue
    fam=natural_family(events(terr))
    if fam not in pools: continue
    frc,_=run(fault_bins[fam],c)
    if status(frc)!='reject': continue
    pools[fam].append((hashlib.sha256(rel.encode()).hexdigest(),rel))
selected={f:[r for _,r in sorted(pools[f])[:2]] for f in FAMILIES}
if any(len(v)<2 for v in selected.values()):
    (out/'observability.json').write_text(json.dumps({'selected':selected,'pool_sizes':{k:len(v) for k,v in pools.items()}},indent=2))
    raise SystemExit(f'insufficient discriminating source-distinct cases: {selected}')

rows=[]
for fam in FAMILIES:
    for rel in selected[fam]:
        case=ARENA/rel; frc,ferr=run(fault_bins[fam],case); ev=events(ferr)
        nearest=route_nearest(ev); negative=route_last_negative(ev); prov=route_provenance(ev)
        policies={
          'BINARY':FAMILIES[:],
          'NEAREST_SEMANTIC':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
          'LAST_NEGATIVE':([negative]+[x for x in FAMILIES if x!=negative]) if negative else FAMILIES[:],
          'PROVENANCE':([prov]+[x for x in FAMILIES if x!=prov]) if prov else FAMILIES[:],
        }
        arms={}
        for arm,order in policies.items():
            attempts=[]
            for cand in order:
                checker=trace_bin if cand==fam else fault_bins[fam]
                rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
                if status(rc)=='accept': break
            arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
        rows.append({'family':fam,'case':rel,'nearest_route':nearest,'last_negative_route':negative,'provenance_route':prov,'events_tail':ev[-32:],'arms':arms})

summary={'status':'LIVE_PROVENANCE_V7','baseline_full_corpus_gate_pass':True,'semantic_mismatches':0,'selected':selected,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','NEAREST_SEMANTIC','LAST_NEGATIVE','PROVENANCE']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['provenance_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['provenance']['mean_verifier_calls']
summary['provenance_vs_nearest_factor']=summary['nearest_semantic']['mean_verifier_calls']/summary['provenance']['mean_verifier_calls']
summary['provenance_vs_last_negative_factor']=summary['last_negative']['mean_verifier_calls']/summary['provenance']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
if any(summary[a]['repair_rate']!=1.0 for a in ['binary','nearest_semantic','last_negative','provenance']): raise SystemExit('repair gate failed')
