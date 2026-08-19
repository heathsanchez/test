#!/usr/bin/env python3
from pathlib import Path
import json,os,shutil,subprocess
root=Path.cwd(); out=root/'results/developmental-checker-compact-repair-v8'; out.mkdir(parents=True,exist_ok=True)
BASE=root/'base'; TRACE=root/'trace'; ARENA=root/'arena-tests'; CFG='{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'
FAMILIES=['INFER_APP','PROJECTION','IOTA','UNFOLD']
SELECTED={
 'INFER_APP':['good/tutorial/016_levelParams.ndjson','good/tutorial/037_andType.ndjson'],
 'PROJECTION':['good/perf/grind-ring-5.ndjson','good/tutorial/084_PSigma.snd.ndjson'],
 'IOTA':['good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson'],
 'UNFOLD':['good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson'],
}
def run(bin,case):
 cfg=bin.parent.parent.parent/'config.json'
 with case.open('rb') as f: cp=subprocess.run([str(bin),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 return cp.returncode,cp.stderr.decode('utf-8','replace')
def st(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')
def events(err):
 xs=[]
 for line in err.splitlines():
  if not line.startswith('[MGTRACE] '): continue
  d={}
  for tok in line[10:].split():
   if '=' in tok:
    k,v=tok.split('=',1); d[k]=v
  xs.append(d)
 return xs
def route_compact(ev):
 # Preserve semantic failures/mechanisms; source-location fallback only if no semantic event survives.
 for e in reversed(ev):
  k=e.get('kind'); s=e.get('site','')
  if k=='panic': continue
  if s=='infer.proj' or k=='projection': return 'PROJECTION'
  if s=='conv.recursor' or k in ('iota','iota_result'): return 'IOTA'
  if s=='conv.unfold_pair' or k in ('unfold','unfold_result'): return 'UNFOLD'
  if s=='infer.app_arg' and e.get('ok')=='false': return 'INFER_APP'
 for e in reversed(ev):
  if e.get('kind')=='panic' and 'src/infer.rs' in e.get('site',''): return 'INFER_APP'
 return None
def inject(src,fam):
 if fam=='INFER_APP':
  p=src/'src/infer.rs'; s=p.read_text(); anchor='                    assert!(mg_ok, "app arg def_eq failed");'; repl='                    panic!("MGFAULT_INFER_APP");\n'+anchor
 elif fam=='PROJECTION':
  p=src/'src/infer.rs'; s=p.read_text(); anchor='        eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'; repl=anchor+'\n        panic!("MGFAULT_PROJECTION");'
 elif fam=='IOTA':
  p=src/'src/conv.rs'; s=p.read_text(); anchor='                eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'; repl=anchor+'\n                panic!("MGFAULT_IOTA");'
 elif fam=='UNFOLD':
  p=src/'src/conv.rs'; s=p.read_text(); anchor='                        eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);'; repl=anchor+'\n                        panic!("MGFAULT_UNFOLD");'
 else: raise ValueError(fam)
 if anchor not in s: raise RuntimeError(f'anchor missing {fam}')
 p.write_text(s.replace(anchor,repl,1))
base=BASE/'target/release/sokonanoda'; trace=TRACE/'target/release/sokonanoda'
# Semantic identity gate on frozen Arena corpus.
for kind,expected in [('good','accept'),('bad','reject')]:
 for c in sorted((ARENA/kind).rglob('*.ndjson')):
  rb,_=run(base,c); rt,_=run(trace,c)
  if st(rb)!=expected or st(rt)!=expected or st(rb)!=st(rt): raise SystemExit(f'semantic gate failed {c}')
rows=[]
for fam in FAMILIES:
 work=root/f'fault-{fam.lower()}'
 if work.exists(): shutil.rmtree(work)
 shutil.copytree(TRACE,work,ignore=shutil.ignore_patterns('target')); inject(work,fam); (work/'config.json').write_text(CFG)
 subprocess.run(['cargo','build','--release'],cwd=work,check=True,env={**os.environ,'RUSTFLAGS':'-C target-cpu=native'})
 faulty=work/'target/release/sokonanoda'
 for rel in SELECTED[fam]:
  case=ARENA/rel; br,_=run(trace,case); fr,err=run(faulty,case); ev=events(err); route=route_compact(ev)
  if st(br)!='accept' or st(fr)!='reject': raise SystemExit(f'discriminator failed {fam} {rel}')
  policies={'BINARY':FAMILIES[:],'COMPACT_CAUSAL':([route]+[x for x in FAMILIES if x!=route]) if route else FAMILIES[:]}
  arms={}
  for arm,order in policies.items():
   at=[]
   for cand in order:
    checker=trace if cand==fam else faulty; rc,_=run(checker,case); at.append({'candidate':cand,'verdict':st(rc)})
    if st(rc)=='accept': break
   arms[arm]={'verifier_calls':len(at),'solved':at[-1]['verdict']=='accept','attempts':at}
  rows.append({'family':fam,'case':rel,'route':route,'event_count':len(ev),'events_tail':ev[-16:],'arms':arms})
summary={'status':'LIVE_COMPACT_REPAIR_V8','semantic_identity_gate_pass':True,'episodes':len(rows),'rows':rows}
for arm in ['BINARY','COMPACT_CAUSAL']:
 vals=[r['arms'][arm]['verifier_calls'] for r in rows]; summary[arm.lower()]={'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),'mean_verifier_calls':sum(vals)/len(vals),'calls':vals}
summary['compact_vs_binary_factor']=summary['binary']['mean_verifier_calls']/summary['compact_causal']['mean_verifier_calls']
out.joinpath('summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if summary['compact_causal']['repair_rate']!=1.0: raise SystemExit('compact repair gate failed')
