#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-repair-v6'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['IOTA','UNFOLD']
EXCLUDE={
 'good/tutorial/079_listRecReduction.ndjson','good/tutorial/030_peano3.ndjson',
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

def natural_family(ev):
    kinds={e.get('kind') for e in ev}
    sites={e.get('site') for e in ev}
    if 'iota' in kinds and 'conv.recursor' in sites: return 'IOTA'
    if 'unfold' in kinds and 'conv.unfold_pair' in sites: return 'UNFOLD'
    return None

def route_nearest(ev):
    # V4 rule: nearest semantic event before terminal panic.
    for e in reversed(ev):
        k=e.get('kind'); s=e.get('site','')
        if k=='panic': continue
        if s=='infer.app_arg': return 'IOTA'  # no family identity; frozen binary tie-break for displaced symptom
        if s=='conv.recursor' or k in ('iota','iota_result'): return 'IOTA'
        if s=='conv.unfold_pair' or k in ('unfold','unfold_result'): return 'UNFOLD'
    return None

def route_last_negative(ev):
    # New hypothesis frozen before V6 outcomes: route from the most recent semantic operation
    # that itself returned a negative result, ignoring later wrapper assertions.
    for e in reversed(ev):
        if e.get('ok')!='false': continue
        if e.get('kind')=='iota_result' or e.get('site')=='conv.recursor': return 'IOTA'
        if e.get('kind')=='unfold_result' or e.get('site')=='conv.unfold_pair': return 'UNFOLD'
    return None

def inject_displaced_fault(src,fam):
    if fam=='IOTA':
        p=src/'src/conv.rs'; s=p.read_text()
        old='''                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
        new='''                let _mg_real = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                let mg_r = false;\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    elif fam=='UNFOLD':
        p=src/'src/conv.rs'; s=p.read_text()
        old='''                        eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);\n                        return self.unfold_pair(depth, t, t2);'''
        new='''                        eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);\n                        let _mg_real = self.unfold_pair(depth, t, t2);\n                        let mg_r = false;\n                        eprintln!("[MGTRACE] kind=unfold_result site=conv.unfold_pair depth={} ok={}", depth, mg_r);\n                        return mg_r;'''
    else: raise ValueError(fam)
    if old not in s: raise RuntimeError(f'displacement anchor missing for {fam}')
    p.write_text(s.replace(old,new,1))

base_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
# Full semantic baseline gate.
errs=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        rc,_=run(base_bin,c)
        if status(rc)!=expected: errs.append([str(c.relative_to(ARENA)),expected,status(rc)])
if errs: raise SystemExit(f'baseline gate failed: {errs[:3]}')

# Deterministic source-distinct selection from naturally exercising good cases.
pools={f:[] for f in FAMILIES}
for c in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(c.relative_to(ARENA))
    if rel in EXCLUDE: continue
    rc,err=run(trace_bin,c)
    if status(rc)!='accept': continue
    fam=natural_family(events(err))
    if fam in pools:
        pools[fam].append((hashlib.sha256(rel.encode()).hexdigest(),rel))
selected={f:[r for _,r in sorted(pools[f])[:2]] for f in FAMILIES}
if any(len(v)<2 for v in selected.values()): raise SystemExit(f'insufficient natural cases: {selected}')

rows=[]
for fam in FAMILIES:
    work=root/f'displaced-{fam.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_displaced_fault(work,fam); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
    faulty=work/'target/release/sokonanoda'
    for rel in selected[fam]:
        case=ARENA/rel
        brc,_=run(trace_bin,case); frc,ferr=run(faulty,case); ev=events(ferr)
        if status(brc)!='accept' or status(frc)!='reject':
            raise SystemExit(f'displaced discriminator failed {fam} {rel}: {status(brc)}->{status(frc)}')
        nearest=route_nearest(ev); negative=route_last_negative(ev)
        policies={
          'BINARY':FAMILIES[:],
          'NEAREST_SEMANTIC':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else FAMILIES[:],
          'LAST_NEGATIVE':([negative]+[x for x in FAMILIES if x!=negative]) if negative else FAMILIES[:],
          'TRACE_ABLATION':FAMILIES[:],
        }
        arms={}
        for arm,order in policies.items():
            attempts=[]
            for cand in order:
                checker=trace_bin if cand==fam else faulty
                rc,_=run(checker,case); ok=status(rc)=='accept'
                attempts.append({'candidate':cand,'verdict':status(rc)})
                if ok: break
            arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
        rows.append({'family':fam,'case':rel,'nearest_route':nearest,'last_negative_route':negative,'events_tail':ev[-24:],'arms':arms})

summary={'status':'LIVE_DISPLACED_FAULT_V6','baseline_full_corpus_gate_pass':True,'selected':selected,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','NEAREST_SEMANTIC','LAST_NEGATIVE','TRACE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['last_negative_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['last_negative']['mean_verifier_calls']
summary['last_negative_vs_nearest_factor']=summary['nearest_semantic']['mean_verifier_calls']/summary['last_negative']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
if any(summary[a]['repair_rate']!=1.0 for a in ['binary','nearest_semantic','last_negative','trace_ablation']): raise SystemExit('repair gate failed')
