#!/usr/bin/env python3
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, os, re, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-distinction-discovery-v15'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA']
FIXED_ORDER=FAMILIES[:]
SITES={'INFER_APP':'infer.app_arg','PROJECTION':'infer.proj','IOTA':'conv.recursor'}
DEV_PER_FAMILY=2
HOLDOUT_PER_FAMILY=1
# Frozen before outcomes. V15 deliberately destroys V14's event-count shortcut by exposing
# one constant value for event_count_bucket while retaining raw count only for audit.
FEATURES=['event_count_bucket','has_false_result','last_depth_bucket','last_kind','last_module','last_site','semantic_site_count']


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

def semantic_events(ev): return [e for e in ev if e.get('kind')!='panic']
def exercises(ev,fam): return any(e.get('site')==SITES[fam] for e in ev)

def add_common_trap(src):
    p=src/'src/tc.rs'; s=p.read_text(); anchor='const CHUNK_SIZE: usize = 64;'
    helper='''\n\n#[inline(never)]\npub(crate) fn mg_fault_trap() {\n    panic!("MGFAULT");\n}\n'''
    if 'fn mg_fault_trap()' not in s:
        if anchor not in s: raise RuntimeError('common trap anchor missing')
        p.write_text(s.replace(anchor,anchor+helper,1))

def inject_fault(src,fam):
    add_common_trap(src)
    if fam=='INFER_APP':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'; r=a+'\n                    crate::tc::mg_fault_trap();'
    elif fam=='PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'; r=a+'\n        crate::tc::mg_fault_trap();'
    elif fam=='IOTA':
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; r=a+'\n                crate::tc::mg_fault_trap();'
    else: raise ValueError(fam)
    if a not in s: raise RuntimeError(f'fault anchor missing for {fam}')
    p.write_text(s.replace(a,r,1))

def native_fault_location(stderr):
    xs=re.findall(r'panicked at (src/[^:\n]+\.rs:\d+:\d+)',stderr)
    return next((x for x in reversed(xs) if 'src/tc.rs' in x),None)

def bucket_count(n):
    if n<8:return 'lt8'
    if n<32:return '8_31'
    if n<128:return '32_127'
    return 'ge128'

def feature_row(stderr):
    ev=semantic_events(events(stderr)); last=ev[-1] if ev else {}; sites=sorted({e.get('site','') for e in ev if e.get('site')})
    depth=last.get('depth')
    try: d=int(depth) if depth is not None else -1
    except: d=-1
    return {
      # Intervention: V14's winning feature is now identically valued for all examples.
      'event_count_bucket':'MATCHED',
      'raw_event_count':len(ev),
      'raw_event_count_bucket':bucket_count(len(ev)),
      'has_false_result':any(e.get('ok')=='false' for e in ev),
      'last_depth_bucket':'neg' if d<0 else ('0' if d==0 else ('1_3' if d<=3 else 'ge4')),
      'last_kind':last.get('kind','NONE'),
      'last_module':last.get('site','NONE').split('.',1)[0] if last.get('site') else 'NONE',
      'last_site':last.get('site','NONE'),
      'semantic_site_count':str(len(sites)),
    }

def key(row,features): return tuple(row['features'][f] for f in features)
def fit_map(rows,features):
    groups=defaultdict(list)
    for r in rows: groups[key(r,features)].append(r['family'])
    mapping={k:Counter(v).most_common(1)[0][0] for k,v in groups.items()}; global_majority=Counter(r['family'] for r in rows).most_common(1)[0][0]
    return mapping,global_majority

def predict(rows,train,features):
    mp,glob=fit_map(train,features); return [mp.get(key(r,features),glob) for r in rows]
def error(rows,train,features):
    ps=predict(rows,train,features); return sum(p!=r['family'] for p,r in zip(ps,rows))/len(rows)
def learn_minimal(train):
    selected=[]; history=[]; cur=error(train,train,selected)
    while cur>0:
        cands=[]
        for f in FEATURES:
            if f in selected: continue
            e=error(train,train,selected+[f]); cands.append((e,f))
        if not cands: break
        best_e,best_f=min(cands,key=lambda x:(x[0],x[1])); history.append({'phase':'split','before_error':cur,'feature':best_f,'after_error':best_e})
        if best_e>=cur: break
        selected.append(best_f); cur=best_e
    changed=True
    while changed:
        changed=False
        for f in list(selected):
            trial=[x for x in selected if x!=f]; e=error(train,train,trial); history.append({'phase':'quotient_probe','feature':f,'error_without':e})
            if e==0: selected=trial; changed=True; break
    return selected,history,error(train,train,selected)

def verifier_calls_for_prediction(fault_bin,trace_bin,case,family,pred):
    order=[pred]+[x for x in FIXED_ORDER if x!=pred] if pred in FIXED_ORDER else FIXED_ORDER[:]; attempts=[]
    for cand in order:
        checker=trace_bin if cand==family else fault_bin; rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
        if status(rc)=='accept': break
    return attempts

base_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
mism=[]
for kind in ['good','bad']:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        br,_=run(base_bin,c); tr,_=run(trace_bin,c)
        if status(br)!=status(tr): mism.append([str(c.relative_to(ARENA)),status(br),status(tr)])
if mism:
    (out/'summary.json').write_text(json.dumps({'status':'SEMANTIC_GATE_FAIL','mismatches':mism[:20]},indent=2)); raise SystemExit('semantic gate failed')

selected={}; eligible={}
for fam in FAMILIES:
    pool=[]
    for c in sorted((ARENA/'good').rglob('*.ndjson')):
        rc,err=run(trace_bin,c)
        if status(rc)!='accept' or not exercises(events(err),fam): continue
        rel=str(c.relative_to(ARENA)); pool.append((hashlib.sha256((fam+'|'+rel).encode()).hexdigest(),rel))
    pool=sorted(pool); eligible[fam]=[r for _,r in pool]; need=DEV_PER_FAMILY+HOLDOUT_PER_FAMILY
    if len(pool)<need:
        report={'status':'R4_DISCOVERY_OBSERVABILITY','family':fam,'eligible_count':len(pool),'eligible':eligible[fam],'semantic_mismatches':0}
        (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)
    selected[fam]=[r for _,r in pool[:need]]

fault_bins={}; rows=[]; trap_locations=[]
for fam in FAMILIES:
    work=root/f'fault-v15-{fam.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target')); inject_fault(work,fam); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'}); fault_bins[fam]=work/'target/release/sokonanoda'
    for j,rel in enumerate(selected[fam]):
        case=ARENA/rel; frc,ferr=run(fault_bins[fam],case)
        if status(frc)!='reject': raise SystemExit(f'fault discriminator failed {fam} {rel}: {status(frc)}')
        trap_locations.append(native_fault_location(ferr)); rows.append({'family':fam,'case':rel,'split':'dev' if j<DEV_PER_FAMILY else 'holdout','features':feature_row(ferr)})

locs=sorted({x for x in trap_locations if x})
if len(locs)!=1 or any(x is None for x in trap_locations): raise SystemExit(f'common boundary gate failed locations={locs} missing={sum(x is None for x in trap_locations)}')
# Hard shortcut-destruction gate: the feature exposed to the learner must be constant, while raw morphology remains audited.
if {r['features']['event_count_bucket'] for r in rows}!={'MATCHED'}: raise SystemExit('event-count matching intervention failed')

dev=[r for r in rows if r['split']=='dev']; hold=[r for r in rows if r['split']=='holdout']
selected_features,history,train_error=learn_minimal(dev); hold_preds=predict(hold,dev,selected_features); hold_acc=sum(p==r['family'] for p,r in zip(hold_preds,hold))/len(hold); coarse_error=error(dev,dev,[])
heldout_rows=[]
for r,pred in zip(hold,hold_preds):
    case=ARENA/r['case']; fam=r['family']; learned_attempts=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,pred); binary_attempts=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,FIXED_ORDER[0])
    heldout_rows.append({**r,'prediction':pred,'learned_calls':len(learned_attempts),'binary_calls':len(binary_attempts),'learned_attempts':learned_attempts,'binary_attempts':binary_attempts})
ablations=[]
for f in selected_features:
    trial=[x for x in selected_features if x!=f]; ps=predict(hold,dev,trial); calls=[]
    for r,p in zip(hold,ps): calls.append(len(verifier_calls_for_prediction(fault_bins[r['family']],trace_bin,ARENA/r['case'],r['family'],p)))
    ablations.append({'removed':f,'train_error':error(dev,dev,trial),'holdout_accuracy':sum(p==r['family'] for p,r in zip(ps,hold))/len(hold),'mean_verifier_calls':sum(calls)/len(calls),'calls':calls})
learned_calls=[r['learned_calls'] for r in heldout_rows]; binary_calls=[r['binary_calls'] for r in heldout_rows]
summary={'status':'LIVE_SHORTCUT_DESTROYED_DISTINCTION_V15','semantic_mismatches':0,'common_native_boundary':locs[0],'families':FAMILIES,'frozen_candidate_features':FEATURES,'destroyed_shortcut':'event_count_bucket','raw_event_count_buckets':sorted({r['features']['raw_event_count_bucket'] for r in rows}),'selected_cases':selected,'dev_episodes':len(dev),'holdout_episodes':len(hold),'coarse_train_error':coarse_error,'selected_features':selected_features,'learning_history':history,'minimal_train_error':train_error,'holdout_accuracy':hold_acc,'learned_mean_verifier_calls':sum(learned_calls)/len(learned_calls),'binary_mean_verifier_calls':sum(binary_calls)/len(binary_calls),'call_reduction_factor':(sum(binary_calls)/len(binary_calls))/(sum(learned_calls)/len(learned_calls)),'heldout_rows':heldout_rows,'ablations':ablations,'rows':rows}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if coarse_error==0: raise SystemExit('coarse representation unexpectedly sufficient')
if 'event_count_bucket' in selected_features: raise SystemExit('destroyed shortcut was selected')
if train_error!=0: raise SystemExit('split phase failed after shortcut destruction')
if hold_acc!=1.0: raise SystemExit('learned quotient failed source-distinct transfer after shortcut destruction')
if summary['learned_mean_verifier_calls']>=summary['binary_mean_verifier_calls']: raise SystemExit('learned quotient did not reduce verifier search')
if not selected_features: raise SystemExit('no deeper distinction discovered')
if any(a['train_error']==0 and a['mean_verifier_calls']<=summary['learned_mean_verifier_calls'] for a in ablations): raise SystemExit('retained distinction not deletion-load-bearing')
