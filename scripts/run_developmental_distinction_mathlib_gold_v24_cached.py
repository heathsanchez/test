#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess, time

root=Path.cwd()
out=root/'results/developmental-distinction-mathlib-gold-v24-reset'/'evaluator'
out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA']; FIXED_ORDER=FAMILIES[:]
SITES={'INFER_APP':'infer.app_arg','PROJECTION':'infer.proj','IOTA':'conv.recursor'}
FROZEN_RULE={'NONE':'INFER_APP','U':'PROJECTION','F':'IOTA'}
GOLD_PER_FAMILY=5

def checkpoint(name,obj):
    p=out/f'{name}.json'; p.write_text(json.dumps(obj,indent=2,sort_keys=True)); print(f'CHECKPOINT {name}: {p}',flush=True)

def run(bin_path,case,timeout=900):
    cfg=bin_path.parent.parent.parent/'config.json'; t=time.time()
    with case.open('rb') as f:
        try:
            cp=subprocess.run([str(bin_path),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=timeout)
            return cp.returncode,cp.stderr.decode('utf-8','replace'),time.time()-t
        except subprocess.TimeoutExpired as e:
            err=(e.stderr or b'').decode('utf-8','replace') if isinstance(e.stderr,(bytes,bytearray)) else str(e.stderr or '')
            return 124,err,time.time()-t

def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else ('timeout' if rc==124 else 'reject'))

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
def native_fault_location(stderr):
    ps=[e.get('site') for e in events(stderr) if e.get('kind')=='panic' and e.get('site')]
    return ps[-1] if ps else None

def final_depth_step(stderr):
    depths=[]
    for e in semantic_events(events(stderr)):
        if 'depth' not in e: continue
        try: depths.append(int(e['depth']))
        except Exception: pass
    if len(depths)<2:return 'NONE'
    if depths[-1]>depths[-2]:return 'U'
    if depths[-1]<depths[-2]:return 'D'
    return 'F'

def add_common_trap(src):
    p=src/'src/tc.rs'; s=p.read_text(); anchor='const CHUNK_SIZE: usize = 64;'
    helper='''\n\n#[inline(never)]\npub(crate) fn mg_fault_trap() {\n    eprintln!("[MGTRACE] kind=panic site=src/tc.rs:mg_fault_trap");\n    panic!("MGFAULT");\n}\n'''
    if 'fn mg_fault_trap()' not in s:
        if anchor not in s: raise RuntimeError('common trap anchor missing')
        p.write_text(s.replace(anchor,anchor+helper,1))

def inject_fault(src,fam):
    add_common_trap(src)
    if fam=='INFER_APP':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'; r=a+'\n                    crate::tc::mg_fault_trap();'
    elif fam=='PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'; r=a+'\n        crate::tc::mg_fault_trap();'
    else:
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; r=a+'\n                crate::tc::mg_fault_trap();'
    if a not in s: raise RuntimeError(f'fault anchor missing for {fam}')
    p.write_text(s.replace(a,r,1))

def verifier_calls(fault_bin,trace_bin,case,family,pred):
    order=[pred]+[x for x in FIXED_ORDER if x!=pred] if pred in FIXED_ORDER else FIXED_ORDER[:]
    attempts=[]
    for cand in order:
        checker=trace_bin if cand==family else fault_bin
        rc,_,sec=run(checker,case)
        attempts.append({'candidate':cand,'verdict':status(rc),'seconds':sec})
        if status(rc)=='accept':break
    return attempts

base_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
cases=sorted((ARENA/'good').glob('*.ndjson'))
print(f'V24 cases={len(cases)}',flush=True)

# One baseline + one trace run per module. This is the only pre-feature observation stage.
obs={}; mism=[]
for i,c in enumerate(cases,1):
    br,be,bs=run(base_bin,c); tr,te,ts=run(trace_bin,c)
    rel=str(c.relative_to(ARENA)); ev=events(te)
    obs[rel]={'baseline':status(br),'trace':status(tr),'baseline_seconds':bs,'trace_seconds':ts,'families_exercised':[f for f in FAMILIES if exercises(ev,f)]}
    if status(br)!=status(tr):mism.append([rel,status(br),status(tr)])
    checkpoint('pre_feature_observations',obs)
    print(f'OBS {i}/{len(cases)} {rel} base={status(br)} trace={status(tr)} fam={obs[rel]["families_exercised"]}',flush=True)
if mism:
    checkpoint('summary',{'status':'SEMANTIC_GATE_FAIL','mismatches':mism}); raise SystemExit('semantic gate failed')

# Freeze selected paths from path + cached family eligibility only. No feature value is computed here.
selected={}; eligible={}
for fam in FAMILIES:
    pool=[]
    for rel,o in obs.items():
        if o['trace']!='accept' or fam not in o['families_exercised']:continue
        h=hashlib.sha256((fam+'|'+rel).encode()).hexdigest(); pool.append((h,rel))
    pool.sort(); eligible[fam]=[r for _,r in pool]
    if len(pool)<GOLD_PER_FAMILY:
        report={'status':'EXTERNAL_CORPUS_OBSTRUCTION_V24','family':fam,'eligible_count':len(pool),'required':GOLD_PER_FAMILY,'eligible':eligible[fam],'semantic_mismatches':0}
        checkpoint('selected_paths_pre_feature',selected); checkpoint('summary',report); print(json.dumps(report,indent=2)); raise SystemExit(0)
    selected[fam]=[r for _,r in pool[:GOLD_PER_FAMILY]]
checkpoint('selected_paths_pre_feature',selected)

# Build one fault checker per family, checkpointing each build.
fault_bins={}; built=[]
for fam in FAMILIES:
    work=root/f'fault-v24-{fam.lower()}'
    if work.exists():shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_fault(work,fam); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
    fault_bins[fam]=work/'target/release/sokonanoda'; built.append(fam); checkpoint('fault_builds',built)

rows=[]; trap_locations=[]
for fam in FAMILIES:
    for rel in selected[fam]:
        case=ARENA/rel; frc,ferr,sec=run(fault_bins[fam],case)
        if status(frc)!='reject':
            checkpoint('rows_partial',rows); raise SystemExit(f'fault discriminator failed {fam} {rel}: {status(frc)}')
        trap_locations.append(native_fault_location(ferr))
        step=final_depth_step(ferr); pred=FROZEN_RULE.get(step,'INFER_APP')
        row={'family':fam,'case':rel,'final_depth_step':step,'prediction':pred,'fault_seconds':sec}
        rows.append(row); checkpoint('rows_partial',rows)
        print(f'GOLD {len(rows)}/15 {fam} {rel} step={step} pred={pred}',flush=True)
locs=sorted({x for x in trap_locations if x})
if len(locs)!=1 or any(x is None for x in trap_locations):raise SystemExit(f'common boundary gate failed locations={locs}')

learned=[]; binary=[]; detailed=[]
for i,r in enumerate(rows,1):
    case=ARENA/r['case']; fam=r['family']; pred=r['prediction']
    la=verifier_calls(fault_bins[fam],trace_bin,case,fam,pred); ba=verifier_calls(fault_bins[fam],trace_bin,case,fam,FIXED_ORDER[0])
    learned.append(len(la)); binary.append(len(ba)); detailed.append({**r,'learned_calls':len(la),'binary_calls':len(ba),'learned_attempts':la,'binary_attempts':ba})
    checkpoint('routing_partial',detailed); print(f'ROUTE {i}/{len(rows)} learned={len(la)} binary={len(ba)}',flush=True)

acc=sum(r['prediction']==r['family'] for r in rows)/len(rows)
per_family={f:{'n':sum(r['family']==f for r in rows),'accuracy':sum(r['family']==f and r['prediction']==f for r in rows)/sum(r['family']==f for r in rows)} for f in FAMILIES}
ml=sum(learned)/len(learned); mb=sum(binary)/len(binary)
summary={'status':'MATHLIB_ZERO_SHOT_GOLD_V24','semantic_mismatches':0,'common_native_boundary':locs[0],'frozen_feature':'final_depth_step','frozen_rule':FROZEN_RULE,'gold_cases_per_family':GOLD_PER_FAMILY,'gold_episodes':len(rows),'gold_accuracy':acc,'per_family':per_family,'learned_mean_verifier_calls':ml,'binary_mean_verifier_calls':mb,'call_reduction_factor':mb/ml,'selected_cases':selected,'eligible_counts':{k:len(v) for k,v in eligible.items()},'rows':detailed}
checkpoint('summary',summary); print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
if acc!=1.0:raise SystemExit('frozen V21 quotient failed Mathlib zero-shot gold transfer')
if any(v['accuracy']!=1.0 for v in per_family.values()):raise SystemExit('frozen V21 quotient failed a Mathlib gold family')
if ml>=mb:raise SystemExit('frozen V21 quotient did not reduce verifier search on Mathlib gold')
