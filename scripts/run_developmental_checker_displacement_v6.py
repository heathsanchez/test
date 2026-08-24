#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, subprocess

root=Path.cwd(); out=root/'results/developmental-checker-repair-v6'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'
CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
# V6A preserves the V6 negative: no source-distinct natural UNFOLD cases existed.
# The supported prospective displacement test therefore freezes IOTA as the fault family,
# while retaining four plausible repair families as distractors.
CANDIDATES=['INFER_APP','PROJECTION','IOTA','UNFOLD']
EXCLUDE={'good/tutorial/079_listRecReduction.ndjson'}

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

def exercises_iota(ev):
    return any(e.get('kind')=='iota' and e.get('site')=='conv.recursor' for e in ev)

def route_nearest(ev):
    # Frozen V4-style rule: nearest semantic event before terminal panic.
    for e in reversed(ev):
        if e.get('kind')=='panic': continue
        s=e.get('site',''); k=e.get('kind')
        if s=='infer.app_arg': return 'INFER_APP'
        if s=='infer.proj': return 'PROJECTION'
        if s=='conv.recursor' or k in ('iota','iota_result'): return 'IOTA'
        if s=='conv.unfold_pair' or k in ('unfold','unfold_result'): return 'UNFOLD'
    return None

def route_last_mechanism_negative(ev):
    # Precommitted V6 hypothesis: ignore downstream wrapper failures and recover the
    # latest mechanism-level operation that itself returned false.
    for e in reversed(ev):
        if e.get('ok')!='false': continue
        if e.get('kind')=='iota_result' and e.get('site')=='conv.recursor': return 'IOTA'
        if e.get('kind')=='unfold_result' and e.get('site')=='conv.unfold_pair': return 'UNFOLD'
    return None

def inject_displaced_iota(src):
    p=src/'src/conv.rs'; s=p.read_text()
    old='''                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    new='''                let _mg_real = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                let mg_r = false;\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
    if old not in s: raise RuntimeError('displaced iota anchor missing')
    p.write_text(s.replace(old,new,1))

base_bin=BASE/'target/release/sokonanoda'; trace_bin=TRACE/'target/release/sokonanoda'
# Hard full-corpus semantic baseline gate.
errs=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for c in sorted((ARENA/kind).rglob('*.ndjson')):
        rc,_=run(base_bin,c)
        if status(rc)!=expected: errs.append([str(c.relative_to(ARENA)),expected,status(rc)])
if errs: raise SystemExit(f'baseline gate failed: {errs[:3]}')

# Deterministic source-distinct selection before fault outcomes.
pool=[]
for c in sorted((ARENA/'good').rglob('*.ndjson')):
    rel=str(c.relative_to(ARENA))
    if rel in EXCLUDE: continue
    rc,err=run(trace_bin,c)
    if status(rc)=='accept' and exercises_iota(events(err)):
        pool.append((hashlib.sha256(rel.encode()).hexdigest(),rel))
selected=[r for _,r in sorted(pool)[:2]]
if len(selected)<2: raise SystemExit(f'insufficient source-distinct IOTA cases: {selected}')

work=root/'displaced-iota'
if work.exists(): shutil.rmtree(work)
shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target'))
inject_displaced_iota(work); (work/'config.json').write_text(CFG)
subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
faulty=work/'target/release/sokonanoda'

rows=[]
for rel in selected:
    case=ARENA/rel
    brc,_=run(trace_bin,case); frc,ferr=run(faulty,case); ev=events(ferr)
    if status(brc)!='accept' or status(frc)!='reject':
        raise SystemExit(f'displaced discriminator failed {rel}: {status(brc)}->{status(frc)}')
    nearest=route_nearest(ev); causal=route_last_mechanism_negative(ev)
    policies={
      'BINARY':CANDIDATES[:],
      'NEAREST_SEMANTIC':([nearest]+[x for x in CANDIDATES if x!=nearest]) if nearest else CANDIDATES[:],
      'LAST_MECHANISM_NEGATIVE':([causal]+[x for x in CANDIDATES if x!=causal]) if causal else CANDIDATES[:],
      # Ablation preserves terminal symptom/location but removes mechanism-level negative result.
      'CAUSAL_ABLATION':([nearest]+[x for x in CANDIDATES if x!=nearest]) if nearest else CANDIDATES[:],
    }
    arms={}
    for arm,order in policies.items():
        attempts=[]
        for cand in order:
            checker=trace_bin if cand=='IOTA' else faulty
            rc,_=run(checker,case); attempts.append({'candidate':cand,'verdict':status(rc)})
            if status(rc)=='accept': break
        arms[arm]={'verifier_calls':len(attempts),'solved':attempts[-1]['verdict']=='accept','attempts':attempts}
    rows.append({'family':'IOTA','case':rel,'nearest_route':nearest,'causal_route':causal,'events_tail':ev[-32:],'arms':arms})

summary={'status':'LIVE_DISPLACED_IOTA_V6A','baseline_full_corpus_gate_pass':True,'v6_observability_residual':'No source-distinct natural UNFOLD cases under frozen trace vocabulary','selected':selected,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','NEAREST_SEMANTIC','LAST_MECHANISM_NEGATIVE','CAUSAL_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['causal_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['last_mechanism_negative']['mean_verifier_calls']
summary['causal_vs_nearest_factor']=summary['nearest_semantic']['mean_verifier_calls']/summary['last_mechanism_negative']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if any(summary[a]['repair_rate']!=1.0 for a in ['binary','nearest_semantic','last_mechanism_negative','causal_ablation']): raise SystemExit('repair gate failed')
