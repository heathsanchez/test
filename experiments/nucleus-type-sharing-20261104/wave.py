#!/usr/bin/env python3
"""Test whether cached inferred types accidentally duplicate large trees."""
import argparse,difflib,json,os,re,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-conversion-allocation-20261104'))
import tournament as t
from patch import conversion_patch
ARMS=[('baseline',False,False),('pi-sharing','rc',False),('pi-hash-sharing','cached',False),('both','cached',True)]
def materialize(out,pi,context):
 k=t.materialize(Path.cwd(),out)
 files=list((k/'src').glob('*.rs'))+list((k/'tests').glob('*.rs'))
 old={p:p.read_text() for p in files}
 if context:
  p=k/'src/convert.rs';p.write_text(conversion_patch(p.read_text(),shared=True))
 if pi:
  for p in files:
   s=p.read_text()
   # These field constructors exclusively belong to TypeValue::Pi in this kernel.
   s=re.sub(r'\b(domain|body)\s*:\s*Box::new',lambda m:m.group(1)+(': crate::typecheck::SharedType::new' if pi=='cached' else ': std::rc::Rc::new'),s)
   target='SharedType' if pi=='cached' else 'Rc<TypeValue>'
   s=s.replace('domain: Box<TypeValue>','domain: '+target).replace('body: Box<TypeValue>','body: '+target)
   s=s.replace('Some((*domain, PiBody::Fixed(binder, *body)))','Some(((*domain).clone(), PiBody::Fixed(binder, (*body).clone())))')
   s=s.replace('work.push((*left_domain, *right_domain, depth, local_context));','work.push(((*left_domain).clone(), (*right_domain).clone(), depth, local_context));')
   p.write_text(s)
  if pi=='cached':
   p=k/'src/typecheck.rs';p.write_text(p.read_text()+'\n'+(Path(__file__).resolve().parent/'shared_type.rs').read_text())
 with (out/'source.patch').open('a') as f:
  for p,s in old.items():f.write(''.join(difflib.unified_diff(s.splitlines(True),p.read_text().splitlines(True),fromfile='a/metatron-kernel/'+str(p.relative_to(k)),tofile='b/metatron-kernel/'+str(p.relative_to(k)))))
 return k

def main(args):
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True);root=Path(args.inputs);manifest=json.loads((root/'inputs-manifest.json').read_text());env=t.run_env()
 if args.phase=='spike':
  state={}
  for name,pi,ctx in ARMS:
   arm=out/name;k=materialize(arm,pi,ctx);binary,benv=t.build(k,arm)
   state[name]=dict(built=binary is not None,source_patch_sha=t.digest(arm/'source.patch'))
   t.write_json(out/'state.json',state)
   if binary is None:raise RuntimeError('build failed: '+name)
  cohort=[r for r in manifest if r['case'] in {'init-prelude','perf/app-lam','perf/beta-ladder','perf/let-ladder'}];assert len(cohort)==4
  perf=t.probe_perf(out);rows=[]
  for roundno in range(3):
   arms=ARMS if roundno%2==0 else list(reversed(ARMS))
   for name,_,_ in arms:
    for r in cohort:
     p=root/'inputs'/r['relative_path'];assert t.digest(p)==r['sha256'];assert r['expected']==0
     d=out/name/f"spike-{roundno}-{r['case'].replace('/','__')}"
     m=t.measure(out/name/'nucleus',p,env,d,timeout=240,perf=perf)
     rows.append(dict(arm=name,case=r['case'],round=roundno,**m));t.write_json(out/'spike.json',rows)
     if m['rc']!=0:raise RuntimeError('accepted-input control failed')
  baseline={(r['case'],r['round']):r for r in rows if r['arm']=='baseline'};summary={}
  for name,_,_ in ARMS:
   rs=[r for r in rows if r['arm']==name]
   summary[name]=dict(wall_ratio=t.geometric([r['wall_observed']/baseline[r['case'],r['round']]['wall_observed'] for r in rs]),per_case={case:dict(wall_ratio=t.geometric([r['wall_observed']/baseline[r['case'],r['round']]['wall_observed'] for r in rs if r['case']==case]),rss_kb=max(r['rss_kb'] for r in rs if r['case']==case)) for case in {r['case'] for r in rs}})
  t.write_json(out/'summary.json',dict(arms=summary,qualification='CANDIDATE_MICROBENCHMARK_PENDING_NATIVE_AND_208',base=t.BASE,harness=os.environ.get('GITHUB_SHA')))
 else:
  state=json.loads((out/'state.json').read_text());native=None;baseline=None
  for name,_,_ in ARMS:
   arm=out/name;k=arm/'metatron-kernel';benv=dict(os.environ,CARGO_TARGET_DIR=str(arm/'target'))|env
   nr=t.native_suite(k,benv,arm)
   rows=t.replay(arm/'nucleus',manifest,root,env,arm/'verdicts.json')
   if name=='baseline':t.validate_baseline(rows);baseline=rows;native=nr
   diff=[a['case'] for a,b in zip(baseline,rows) if a['rc']!=b['rc']]
   state[name].update(native_targets=nr,native_parity=t.native_reports_match(nr,native),parity=not diff,differences=diff,counts={str(rc):sum(r['rc']==rc for r in rows) for rc in (0,1,2)})
   t.write_json(out/'state.json',state);print(name,json.dumps(state[name]),flush=True);shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['spike','qualify']);p.add_argument('--out',required=True);p.add_argument('--inputs',required=True);main(p.parse_args())
