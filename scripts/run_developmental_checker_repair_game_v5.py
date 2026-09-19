#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-repair-v5'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA','UNFOLD']
DEV_TARGETS={
 'good/tutorial/006_betaReduction.ndjson',
 'good/tutorial/081_And.right.ndjson',
 'good/tutorial/079_listRecReduction.ndjson',
 'good/tutorial/030_peano3.ndjson',
}
BINARY_ORDER=FAMILIES[:]
ABLATION_ORDER={'infer':['INFER_APP','PROJECTION','IOTA','UNFOLD'],'conv':['IOTA','UNFOLD','INFER_APP','PROJECTION']}
MODULE={'INFER_APP':'infer','PROJECTION':'infer','IOTA':'conv','UNFOLD':'conv'}

def run(bin_path,case_path):
    with case_path.open('rb') as f:
        cp=subprocess.run([str(bin_path),str(bin_path.parent.parent.parent/'config.json')],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    return cp.returncode,cp.stderr.decode('utf-8','replace')
def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')
def events(stderr):
    xs=[]
    for line in stderr.splitlines():
        if not line.startswith('[MGTRACE] '): continue
        d={}
        for tok in line[len('[MGTRACE] '):].split():
            if '=' in tok:
                k,v=tok.split('=',1); d[k]=v
        xs.append(d)
    return xs

def supports_family(ev,f):
    for e in ev:
        k=e.get('kind',''); s=e.get('site','')
        if f=='INFER_APP' and k=='defeq' and s=='infer.app_arg': return True
        if f=='PROJECTION' and (k=='projection' or s=='infer.proj'): return True
        if f=='IOTA' and (k=='iota' or s in ('conv.recursor','conv.quot')): return True
        if f=='UNFOLD' and (k=='unfold' or s=='conv.unfold_pair'): return True
    return False

def route_full(ev):
    sites=[e.get('site','') for e in ev]
    if any(s=='infer.app_arg' for s in sites): return 'INFER_APP'
    if any(s=='infer.proj' for s in sites): return 'PROJECTION'
    if any(s=='conv.recursor' for s in sites): return 'IOTA'
    if any(s=='conv.unfold_pair' for s in sites): return 'UNFOLD'
    return None

def route_nearest_semantic(ev):
    semantic=[]
    for e in ev:
        kind=e.get('kind',''); site=e.get('site','')
        if kind=='panic': continue
        if kind=='projection' or site=='infer.proj': semantic.append('PROJECTION'); continue
        if kind=='iota' or site in ('conv.recursor','conv.quot'): semantic.append('IOTA'); continue
        if kind=='unfold' or site=='conv.unfold_pair': semantic.append('UNFOLD'); continue
        if kind=='defeq' and site=='infer.app_arg': semantic.append('INFER_APP'); continue
    return semantic[-1] if semantic else None

def inject_fault(src,family):
    if family=='INFER_APP':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'; r=a+'\n                    panic!("MGFAULT_INFER_APP");'
    elif family=='PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'; r=a+'\n        panic!("MGFAULT_PROJECTION");'
    elif family=='IOTA':
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; r=a+'\n                panic!("MGFAULT_IOTA");'
    elif family=='UNFOLD':
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);'; r=a+'\n                        panic!("MGFAULT_UNFOLD");'
    else: raise ValueError(family)
    if a not in s: raise RuntimeError(f'fault anchor missing {family}')
    p.write_text(s.replace(a,r,1))

baseline_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
# Full frozen semantic baseline gate.
fail=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for case in sorted((ARENA/kind).rglob('*.ndjson')):
        rc,_=run(baseline_bin,case)
        if status(rc)!=expected: fail.append({'case':str(case.relative_to(ARENA)),'expected':expected,'got':status(rc)})
if fail:
    (out/'summary.json').write_text(json.dumps({'status':'BASELINE_GATE_FAIL','failures':fail},indent=2)); raise SystemExit('baseline gate failed')

# Prospective deterministic source-distinct selection rule:
# among good cases (excluding V4 development targets) that naturally exercise the family,
# choose the two lowest SHA256(relative_path). No repair outcomes participate in selection.
qualified={f:[] for f in FAMILIES}
trace_cache={}
for case in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(case.relative_to(ARENA))
    if rel in DEV_TARGETS: continue
    rc,err=run(trace_bin,case)
    if status(rc)!='accept': continue
    ev=events(err); trace_cache[rel]=ev
    h=hashlib.sha256(rel.encode()).hexdigest()
    for f in FAMILIES:
        if supports_family(ev,f): qualified[f].append((h,rel))
selected={}
for f in FAMILIES:
    q=sorted(qualified[f])
    if len(q)<2: raise SystemExit(f'not enough source-distinct cases for {f}: {len(q)}')
    selected[f]=[rel for _,rel in q[:2]]

# Build one independently faulted checker per family.
fault_bins={}
for f in FAMILIES:
    work=root/f'fault-v5-{f.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_fault(work,f); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**__import__('os').environ,'RUSTFLAGS':'-C target-cpu=native'})
    fault_bins[f]=work/'target/release/sokonanoda'

rows=[]
for f in FAMILIES:
    for j,rel in enumerate(selected[f],1):
        target=ARENA/rel; faulty=fault_bins[f]
        brc,_=run(trace_bin,target); frc,ferr=run(faulty,target); ev=events(ferr)
        if status(brc)!='accept' or status(frc)!='reject': raise SystemExit(f'fault discriminator failed {f} {rel}')
        full=route_full(ev); nearest=route_nearest_semantic(ev); module=MODULE[f]
        policies={
          'BINARY':BINARY_ORDER,
          'FULL_HISTORY':([full]+[x for x in FAMILIES if x!=full]) if full else BINARY_ORDER,
          'NEAREST_SEMANTIC':([nearest]+[x for x in FAMILIES if x!=nearest]) if nearest else BINARY_ORDER,
          'TRACE_ABLATION':ABLATION_ORDER[module],
        }
        arms={}
        for arm,order in policies.items():
            attempts=[]
            for i,cand in enumerate(order,1):
                checker=trace_bin if cand==f else faulty
                rc,_=run(checker,target); attempts.append({'candidate':cand,'verdict':status(rc)})
                if status(rc)=='accept': arms[arm]={'verifier_calls':i,'solved':True,'attempts':attempts}; break
            else: arms[arm]={'verifier_calls':len(order),'solved':False,'attempts':attempts}
        rows.append({'id':f'H{FAMILIES.index(f)+1}.{j}','family':f,'target':rel,'full_route':full,'nearest_semantic_route':nearest,'events':ev[-32:],'arms':arms})

summary={'status':'LIVE_SOURCE_DISTINCT_TRANSFER_V5','selection_rule':'two lowest SHA256 paths per family among naturally exercising good cases, excluding V4 development targets','selected':selected,'baseline_full_corpus_gate_pass':True,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','FULL_HISTORY','NEAREST_SEMANTIC','TRACE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['nearest_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['nearest_semantic']['mean_verifier_calls']
summary['nearest_vs_full_history_factor']=summary['full_history']['mean_verifier_calls']/summary['nearest_semantic']['mean_verifier_calls']
summary['nearest_vs_ablation_factor']=summary['trace_ablation']['mean_verifier_calls']/summary['nearest_semantic']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if any(summary[a.lower()]['repair_rate']!=1.0 for a in ['BINARY','FULL_HISTORY','NEAREST_SEMANTIC','TRACE_ABLATION']): raise SystemExit('repair rate gate failed')
