#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd()
out=root/'results/developmental-distinction-external-gold-v23'
out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA']
FIXED_ORDER=FAMILIES[:]
SITES={'INFER_APP':'infer.app_arg','PROJECTION':'infer.proj','IOTA':'conv.recursor'}
FROZEN_RULE={'NONE':'INFER_APP','U':'PROJECTION','F':'IOTA'}
GOLD_PER_FAMILY=5
# Predeclared before any V23 feature inspection: every exact path used in the V18-V21 lineage.
CONTAMINATED_CASES={
'good/tutorial/128_quotIndReduction.ndjson',
'good/tutorial/126_quotSoundType.ndjson',
'good/undecidability/alg-conv-trans-acc-left.ndjson',
'good/init-prelude.ndjson',
'good/perf/app-lam.ndjson',
'good/perf/shift-cascade.ndjson',
'good/tutorial/082_Prod.snd.ndjson',
'good/perf/grind-ring-5.ndjson',
'good/tutorial/080_RBTree.id_spec.ndjson',
'good/undecidability/subject-reduction-redex.ndjson',
'good/tutorial/079_listRecReduction.ndjson',
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
    if len(depths)<2: return 'NONE'
    if depths[-1]>depths[-2]: return 'U'
    if depths[-1]<depths[-2]: return 'D'
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
    elif fam=='IOTA':
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; r=a+'\n                crate::tc::mg_fault_trap();'
    else: raise ValueError(fam)
    if a not in s: raise RuntimeError(f'fault anchor missing for {fam}')
    p.write_text(s.replace(a,r,1))

def verifier_calls_for_prediction(fault_bin,trace_bin,case,family,pred):
    order=[pred]+[x for x in FIXED_ORDER if x!=pred] if pred in FIXED_ORDER else FIXED_ORDER[:]
    attempts=[]
    for cand in order:
        checker=trace_bin if cand==family else fault_bin
        rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
        if status(rc)=='accept': break
    return attempts

base_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
# Semantic-preservation gate on the complete external corpus before selection.
mism=[]
for kind in ['good','bad']:
    d=ARENA/kind
    if not d.exists(): continue
    for c in sorted(d.rglob('*.ndjson')):
        br,_=run(base_bin,c); tr,_=run(trace_bin,c)
        if status(br)!=status(tr): mism.append([str(c.relative_to(ARENA)),status(br),status(tr)])
if mism:
    report={'status':'SEMANTIC_GATE_FAIL','mismatches':mism[:20]}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit('semantic gate failed')

# Selection uses only source path + whether the unmodified trace exercises the family.
# final_depth_step is not computed until after all five paths are frozen.
selected={}; eligible={}
for fam in FAMILIES:
    pool=[]
    for c in sorted((ARENA/'good').rglob('*.ndjson')):
        rel=str(c.relative_to(ARENA))
        if rel in CONTAMINATED_CASES: continue
        rc,err=run(trace_bin,c)
        if status(rc)!='accept' or not exercises(events(err),fam): continue
        h=hashlib.sha256((fam+'|'+rel).encode()).hexdigest()
        pool.append((h,rel))
    pool.sort(); eligible[fam]=[r for _,r in pool]
    if len(pool)<GOLD_PER_FAMILY:
        report={'status':'EXTERNAL_CORPUS_OBSTRUCTION_V23','family':fam,'eligible_count':len(pool),'required':GOLD_PER_FAMILY,'eligible':eligible[fam],'contaminated_case_paths_excluded':sorted(CONTAMINATED_CASES),'semantic_mismatches':0}
        (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0)
    selected[fam]=[r for _,r in pool[:GOLD_PER_FAMILY]]

(out/'selected_paths_pre_feature.json').write_text(json.dumps(selected,indent=2,sort_keys=True))

fault_bins={}; rows=[]; trap_locations=[]
for fam in FAMILIES:
    work=root/f'fault-v23-direct-{fam.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
    inject_fault(work,fam); (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
    fault_bins[fam]=work/'target/release/sokonanoda'
    for rel in selected[fam]:
        case=ARENA/rel; frc,ferr=run(fault_bins[fam],case)
        if status(frc)!='reject': raise SystemExit(f'fault discriminator failed {fam} {rel}: {status(frc)}')
        trap_locations.append(native_fault_location(ferr))
        step=final_depth_step(ferr); pred=FROZEN_RULE.get(step,'INFER_APP')
        rows.append({'family':fam,'case':rel,'final_depth_step':step,'prediction':pred})

locs=sorted({x for x in trap_locations if x})
if len(locs)!=1 or any(x is None for x in trap_locations):
    raise SystemExit(f'common boundary gate failed locations={locs} missing={sum(x is None for x in trap_locations)}')

learned_calls=[]; binary_calls=[]; detailed=[]
for r in rows:
    case=ARENA/r['case']; fam=r['family']; pred=r['prediction']
    la=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,pred)
    ba=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,FIXED_ORDER[0])
    learned_calls.append(len(la)); binary_calls.append(len(ba))
    detailed.append({**r,'learned_calls':len(la),'binary_calls':len(ba),'learned_attempts':la,'binary_attempts':ba})

acc=sum(r['prediction']==r['family'] for r in rows)/len(rows)
per_family={fam:{'n':sum(r['family']==fam for r in rows),'accuracy':sum(r['family']==fam and r['prediction']==fam for r in rows)/sum(r['family']==fam for r in rows)} for fam in FAMILIES}
mean_l=sum(learned_calls)/len(learned_calls); mean_b=sum(binary_calls)/len(binary_calls)
summary={
 'status':'EXTERNAL_ZERO_SHOT_GOLD_V23',
 'semantic_mismatches':0,
 'common_native_boundary':locs[0],
 'frozen_feature':'final_depth_step',
 'frozen_rule':FROZEN_RULE,
 'gold_cases_per_family':GOLD_PER_FAMILY,
 'gold_episodes':len(rows),
 'gold_accuracy':acc,
 'per_family':per_family,
 'learned_mean_verifier_calls':mean_l,
 'binary_mean_verifier_calls':mean_b,
 'call_reduction_factor':mean_b/mean_l,
 'contaminated_case_paths_excluded':sorted(CONTAMINATED_CASES),
 'selected_cases':selected,
 'eligible_counts':{k:len(v) for k,v in eligible.items()},
 'rows':detailed,
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if acc!=1.0: raise SystemExit('frozen V21 quotient failed external zero-shot gold transfer')
if any(v['accuracy']!=1.0 for v in per_family.values()): raise SystemExit('frozen V21 quotient failed an external gold family')
if mean_l>=mean_b: raise SystemExit('frozen V21 quotient did not reduce verifier search on external gold')
