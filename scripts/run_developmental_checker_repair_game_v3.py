#!/usr/bin/env python3
from pathlib import Path
import json, shutil, subprocess

root = Path.cwd()
out = root / 'results/developmental-checker-repair-v3'
out.mkdir(parents=True, exist_ok=True)
BASE = root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA','UNFOLD']
EPISODES=[
 {'id':'F1','family':'INFER_APP','target':'good/tutorial/006_betaReduction.ndjson','module':'infer'},
 {'id':'F2','family':'PROJECTION','target':'good/tutorial/081_And.right.ndjson','module':'infer'},
 {'id':'F3','family':'IOTA','target':'good/tutorial/079_listRecReduction.ndjson','module':'conv'},
 {'id':'F4','family':'UNFOLD','target':'good/tutorial/030_peano3.ndjson','module':'conv'},
]
BINARY_ORDER=FAMILIES[:]
ABLATION_ORDER={'infer':['INFER_APP','PROJECTION','IOTA','UNFOLD'],'conv':['IOTA','UNFOLD','INFER_APP','PROJECTION']}

def run(bin_path, case_path):
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

def route_full(ev):
    sites=[e.get('site','') for e in ev]
    if any(s=='infer.app_arg' for s in sites): return 'INFER_APP'
    if any(s=='infer.proj' for s in sites): return 'PROJECTION'
    if any(s=='conv.recursor' for s in sites): return 'IOTA'
    if any(s=='conv.unfold_pair' for s in sites): return 'UNFOLD'
    return None

def route_last_boundary(ev):
    # Frozen causal-proximity rule: scan backwards from terminal rejection and choose
    # the most recent discriminative checker boundary. Ignore generic successful events.
    for e in reversed(ev):
        kind=e.get('kind',''); site=e.get('site','')
        if kind=='projection' or site=='infer.proj': return 'PROJECTION'
        if kind=='iota' or site in ('conv.recursor','conv.quot'): return 'IOTA'
        if kind=='unfold' or site=='conv.unfold_pair': return 'UNFOLD'
        if kind=='defeq' and site=='infer.app_arg' and e.get('ok')=='false': return 'INFER_APP'
        if kind=='panic':
            if 'infer.rs' in site: return 'INFER_APP'
            if 'conv.rs' in site: return 'IOTA'
    return None

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
    if a not in s: raise RuntimeError(f'fault anchor not found {family}')
    p.write_text(s.replace(a,r,1))

baseline_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
# full baseline semantic gate
fail=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for case in sorted((ARENA/kind).rglob('*.ndjson')):
        rc,_=run(baseline_bin,case)
        if status(rc)!=expected: fail.append(str(case.relative_to(ARENA)))
if fail: raise SystemExit(f'baseline gate failed: {fail[:5]}')

rows=[]
for ep in EPISODES:
    work=root/f"fault-v3-{ep['id']}"
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_fault(work,ep['family']); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**__import__('os').environ,'RUSTFLAGS':'-C target-cpu=native'})
    faulty=work/'target/release/sokonanoda'; target=ARENA/ep['target']
    brc,_=run(trace_bin,target); frc,ferr=run(faulty,target); ev=events(ferr)
    if status(brc)!='accept' or status(frc)!='reject': raise SystemExit(f"fault discriminator failed {ep['id']}")
    full=route_full(ev); last=route_last_boundary(ev)
    policies={
      'BINARY':BINARY_ORDER,
      'FULL_HISTORY':([full]+[x for x in FAMILIES if x!=full]) if full else BINARY_ORDER,
      'LAST_BOUNDARY':([last]+[x for x in FAMILIES if x!=last]) if last else BINARY_ORDER,
      'TRACE_ABLATION':ABLATION_ORDER[ep['module']],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for i,cand in enumerate(order,1):
            checker=trace_bin if cand==ep['family'] else faulty
            rc,_=run(checker,target); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept':
                arms[arm]={'verifier_calls':i,'solved':True,'attempts':attempts}; break
        else: arms[arm]={'verifier_calls':len(order),'solved':False,'attempts':attempts}
    rows.append({**ep,'full_route':full,'last_boundary_route':last,'events':ev[-32:],'arms':arms})

summary={'status':'LIVE_CONTROLLED_REPAIR_GAME_V3','baseline_full_corpus_gate_pass':True,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','FULL_HISTORY','LAST_BOUNDARY','TRACE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['last_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['last_boundary']['mean_verifier_calls']
summary['last_vs_full_history_factor']=summary['full_history']['mean_verifier_calls']/summary['last_boundary']['mean_verifier_calls']
summary['last_vs_ablation_factor']=summary['trace_ablation']['mean_verifier_calls']/summary['last_boundary']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
if any(summary[a.lower()]['repair_rate']!=1.0 for a in ['BINARY','FULL_HISTORY','LAST_BOUNDARY','TRACE_ABLATION']): raise SystemExit('repair rate gate failed')
