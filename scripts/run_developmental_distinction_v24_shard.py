#!/usr/bin/env python3
# V24 sharded evaluator: one immutable Mathlib module per worker.
from pathlib import Path
from collections import deque
import hashlib,json,os,shutil,subprocess,sys,tempfile,time

ROOT=Path.cwd(); OUT=ROOT/'results'/'v24-shards'; OUT.mkdir(parents=True,exist_ok=True)
FAMILIES=['INFER_APP','PROJECTION','IOTA']; FIXED_ORDER=FAMILIES[:]
SITES={'INFER_APP':'infer.app_arg','PROJECTION':'infer.proj','IOTA':'conv.recursor'}
RULE={'NONE':'INFER_APP','U':'PROJECTION','F':'IOTA'}; GOLD_PER_FAMILY=5
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'

def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else ('timeout' if rc==124 else 'reject'))

def _trace_dict(line):
    if not line.startswith('[MGTRACE] '): return None
    d={}
    for tok in line[10:].split():
        if '=' in tok:
            k,v=tok.split('=',1); d[k]=v
    return d

def compress_stderr(path):
    """Keep only the trace facts consumed downstream, never the full telemetry stream."""
    site_lines={}; depth_tail=deque(maxlen=2); panic_line=None; other_tail=deque(maxlen=50)
    with Path(path).open('r',encoding='utf-8',errors='replace') as f:
        for raw in f:
            line=raw.rstrip('\n')
            d=_trace_dict(line)
            if d is None:
                other_tail.append(line); continue
            site=d.get('site')
            if site and site not in site_lines: site_lines[site]=line
            if d.get('kind')=='panic': panic_line=line
            elif 'depth' in d: depth_tail.append(line)
    kept=list(site_lines.values())+list(depth_tail)
    if panic_line is not None: kept.append(panic_line)
    kept.extend(other_tail)
    # De-duplicate without disturbing chronology needed only inside depth_tail.
    out=[]
    for line in kept:
        if line not in out: out.append(line)
    return '\n'.join(out)

def run(bin_path,case,timeout=1200):
    cfg=bin_path.parent.parent.parent/'config.json'; t=time.time()
    fd,tmp=tempfile.mkstemp(prefix='mgtrace-',suffix='.stderr'); os.close(fd)
    try:
        with case.open('rb') as f, open(tmp,'wb') as ef:
            try:
                cp=subprocess.run([str(bin_path),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=ef,timeout=timeout)
                return cp.returncode,compress_stderr(tmp),time.time()-t
            except subprocess.TimeoutExpired:
                return 124,compress_stderr(tmp),time.time()-t
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

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

def exercises(ev,fam): return any(e.get('site')==SITES[fam] for e in ev)
def final_depth_step(stderr):
    ds=[]
    for e in events(stderr):
        if e.get('kind')=='panic' or 'depth' not in e: continue
        try: ds.append(int(e['depth']))
        except Exception: pass
    if len(ds)<2:return 'NONE'
    if ds[-1]>ds[-2]:return 'U'
    if ds[-1]<ds[-2]:return 'D'
    return 'F'
def native_fault_location(stderr):
    xs=[e.get('site') for e in events(stderr) if e.get('kind')=='panic' and e.get('site')]
    return xs[-1] if xs else None

def case_for_idx(idx):
    p=ROOT/'arena-tests'/'good'/f'v24_mathlib_{idx}.ndjson'
    if not p.exists(): raise SystemExit(f'missing frozen module {p}')
    return p

def reconstruct_pair():
    if (ROOT/'base').exists(): shutil.rmtree(ROOT/'base')
    if (ROOT/'trace').exists(): shutil.rmtree(ROOT/'trace')
    subprocess.run(['git','clone','--depth','1','https://github.com/metalogiclabs/mathgraph-lean-kernel.git','base'],check=True)
    shutil.copytree(ROOT/'base',ROOT/'trace')
    subprocess.run(['python3','scripts/patch_developmental_checker_trace.py'],check=True)
    (ROOT/'base'/'config.json').write_text(CFG); (ROOT/'trace'/'config.json').write_text(CFG)
    for d in ['base','trace']:
        subprocess.run(['cargo','build','--release'],cwd=ROOT/d,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})

def add_common_trap(src):
    p=src/'src/tc.rs'; s=p.read_text(); anchor='const CHUNK_SIZE: usize = 64;'
    helper='''\n\n#[inline(never)]\npub(crate) fn mg_fault_trap() {\n    eprintln!("[MGTRACE] kind=panic site=src/tc.rs:mg_fault_trap");\n    panic!("MGFAULT");\n}\n'''
    if 'fn mg_fault_trap()' not in s:
        if anchor not in s: raise RuntimeError('trap anchor missing')
        p.write_text(s.replace(anchor,anchor+helper,1))
def inject_fault(src,fam):
    add_common_trap(src)
    if fam=='INFER_APP':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'; r=a+'\n                    crate::tc::mg_fault_trap();'
    elif fam=='PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'; r=a+'\n        crate::tc::mg_fault_trap();'
    else:
        p=src/'src/conv.rs'; s=p.read_text(); a='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; r=a+'\n                crate::tc::mg_fault_trap();'
    if a not in s: raise RuntimeError(f'fault anchor missing {fam}')
    p.write_text(s.replace(a,r,1))

def observe():
    idx=os.environ['V24_IDX']; case=case_for_idx(idx)
    reconstruct_pair()
    base=ROOT/'base/target/release/sokonanoda'; trace=ROOT/'trace/target/release/sokonanoda'
    br,_,bs=run(base,case); tr,te,ts=run(trace,case); ev=events(te)
    row={'idx':idx,'case':f'good/{case.name}','baseline':status(br),'trace':status(tr),'baseline_seconds':bs,'trace_seconds':ts,'families_exercised':[f for f in FAMILIES if exercises(ev,f)]}
    (OUT/f'observe-{idx}.json').write_text(json.dumps(row,indent=2,sort_keys=True)); print(json.dumps(row,sort_keys=True))
    if row['baseline']!=row['trace']: raise SystemExit('semantic preservation failure')

def select(obsdir):
    rows=[json.loads(p.read_text()) for p in sorted(Path(obsdir).glob('observe-*.json'))]
    if len(rows)!=16: raise SystemExit(f'need 16 observations, got {len(rows)}')
    if any(r['baseline']!=r['trace'] for r in rows): raise SystemExit('semantic mismatch in observations')
    selected={}; eligible={}; matrix=[]
    for fam in FAMILIES:
        pool=[]
        for r in rows:
            if r['trace']!='accept' or fam not in r['families_exercised']: continue
            h=hashlib.sha256((fam+'|'+r['case']).encode()).hexdigest(); pool.append((h,r))
        pool.sort(key=lambda x:x[0]); eligible[fam]=[x[1]['case'] for x in pool]
        if len(pool)<GOLD_PER_FAMILY:
            summary={'status':'EXTERNAL_CORPUS_OBSTRUCTION_V24','family':fam,'eligible_count':len(pool),'required':GOLD_PER_FAMILY,'eligible':eligible[fam]}
            (OUT/'selected.json').write_text(json.dumps({'selected':selected,'eligible':eligible,'summary':summary},indent=2,sort_keys=True)); print(json.dumps(summary)); raise SystemExit(1)
        chosen=[x[1] for x in pool[:GOLD_PER_FAMILY]]; selected[fam]=[x['case'] for x in chosen]
        matrix += [{'family':fam,'idx':x['idx']} for x in chosen]
    doc={'selected':selected,'eligible':eligible,'matrix':matrix}; (OUT/'selected.json').write_text(json.dumps(doc,indent=2,sort_keys=True))
    print('matrix='+json.dumps({'include':matrix},separators=(',',':')))
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('matrix='+json.dumps({'include':matrix},separators=(',',':'))+'\n')

def build_gold():
    fam=os.environ['V24_FAMILY']; reconstruct_pair()
    fault=ROOT/f'fault-{fam.lower()}'
    shutil.copytree(ROOT/'trace',fault,ignore=shutil.ignore_patterns('target'))
    inject_fault(fault,fam); (fault/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'],cwd=fault,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})

def verifier_calls(fault,trace,case,family,pred):
    order=[pred]+[x for x in FIXED_ORDER if x!=pred]
    out=[]
    for cand in order:
        checker=trace if cand==family else fault
        rc,_,sec=run(checker,case); out.append({'candidate':cand,'verdict':status(rc),'seconds':sec})
        if status(rc)=='accept':break
    return out

def gold():
    idx=os.environ['V24_IDX']; fam=os.environ['V24_FAMILY']; case=case_for_idx(idx)
    trace=ROOT/'trace/target/release/sokonanoda'; fault=ROOT/f'fault-{fam.lower()}/target/release/sokonanoda'
    frc,ferr,fsec=run(fault,case)
    if status(frc)!='reject': raise SystemExit(f'fault discriminator {status(frc)}')
    loc=native_fault_location(ferr); step=final_depth_step(ferr); pred=RULE.get(step,'INFER_APP')
    learned=verifier_calls(fault,trace,case,fam,pred); binary=verifier_calls(fault,trace,case,fam,FIXED_ORDER[0])
    row={'idx':idx,'family':fam,'case':f'good/{case.name}','native_boundary':loc,'final_depth_step':step,'prediction':pred,'correct':pred==fam,'fault_seconds':fsec,'learned_calls':len(learned),'binary_calls':len(binary),'learned_attempts':learned,'binary_attempts':binary}
    (OUT/f'gold-{fam}-{idx}.json').write_text(json.dumps(row,indent=2,sort_keys=True)); print(json.dumps(row,sort_keys=True))

def aggregate(golddir):
    rows=[json.loads(p.read_text()) for p in sorted(Path(golddir).glob('gold-*.json'))]
    if len(rows)!=15:
        summary={'status':'INCOMPLETE_V24_SHARDS','completed':len(rows),'required':15,'rows':rows}; (OUT/'final-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary)); raise SystemExit(1)
    locs=sorted({r['native_boundary'] for r in rows if r.get('native_boundary')})
    acc=sum(bool(r['correct']) for r in rows)/15
    per={f:{'n':sum(r['family']==f for r in rows),'accuracy':sum(r['family']==f and r['correct'] for r in rows)/sum(r['family']==f for r in rows)} for f in FAMILIES}
    ml=sum(r['learned_calls'] for r in rows)/15; mb=sum(r['binary_calls'] for r in rows)/15
    summary={'status':'MATHLIB_ZERO_SHOT_GOLD_V24_SHARDED','gold_episodes':15,'gold_accuracy':acc,'per_family':per,'learned_mean_verifier_calls':ml,'binary_mean_verifier_calls':mb,'call_reduction_factor':mb/ml,'common_native_boundaries':locs,'frozen_feature':'final_depth_step','frozen_rule':RULE,'rows':rows}
    (OUT/'final-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
    if len(locs)!=1: raise SystemExit('common boundary gate failed')
    if acc!=1.0: raise SystemExit('frozen V21 quotient failed Mathlib zero-shot gold transfer')
    if ml>=mb: raise SystemExit('frozen quotient did not reduce verifier search')

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='observe':observe()
    elif mode=='select':select(sys.argv[2])
    elif mode=='build':build_gold()
    elif mode=='gold':gold()
    elif mode=='aggregate':aggregate(sys.argv[2])
    else:raise SystemExit(mode)
