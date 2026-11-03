#!/usr/bin/env python3
"""Test whether cached inferred types accidentally duplicate large trees."""
import argparse,difflib,json,os,re,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))

import tournament as t

ARMS=[('baseline',False,False),('prefix-sharing',True,False),('dense-parser',False,True),('stack',True,True)]
def materialize(out,pi,context):
 from patch import prefix_patch
 k=t.materialize(Path.cwd(),out)
 if context:
  for relative in ['src/id.rs','src/parser.rs']:
   p=k/relative;old=p.read_text()
   if relative=='src/id.rs':new=t.hybrid_table(old)
   else:new=t.replace_once(old,'pub fn parse<R: BufRead>','#[cfg(test)]\nfn parse_reference<R: BufRead>')+'\n'+(Path(__file__).resolve().parents[1]/'nucleus-structural-import-20261104/hot_parser.rs').read_text()
   p.write_text(new)
   with (out/'source.patch').open('a') as f:f.write(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/metatron-kernel/'+relative,tofile='b/metatron-kernel/'+relative)))
 if pi:
  p=k/'src/typecheck.rs';old=p.read_text();new=prefix_patch(old);p.write_text(new)
  with (out/'source.patch').open('a') as f:f.write(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/metatron-kernel/src/typecheck.rs',tofile='b/metatron-kernel/src/typecheck.rs')))
 return k

def main(args):
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True);root=Path(args.inputs);manifest=json.loads((root/'inputs-manifest.json').read_text());env=t.run_env()
 if args.phase=='spike':
  state={}
  for name,pi,ctx in ARMS:
   arm=out/name;k=materialize(arm,pi,ctx);binary,benv=t.build(k,arm)
   state[name]=dict(built=binary is not None,source_patch_sha=t.digest(arm/'source.patch'))
   t.write_json(out/'state.json',state)
   if binary is None and name=='baseline':raise RuntimeError('baseline build failed')
  cohort=[r for r in manifest if r['case'] in {'init-prelude','perf/app-lam','perf/beta-ladder','perf/let-ladder'}];assert len(cohort)==4
  perf=t.probe_perf(out);rows=[]
  for roundno in range(3):
   viable=[a for a in ARMS if state[a[0]]['built']]
   arms=viable if roundno%2==0 else list(reversed(viable))
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
   if not rs:continue
   summary[name]=dict(wall_ratio=t.geometric([r['wall_observed']/baseline[r['case'],r['round']]['wall_observed'] for r in rs]),per_case={case:dict(wall_ratio=t.geometric([r['wall_observed']/baseline[r['case'],r['round']]['wall_observed'] for r in rs if r['case']==case]),rss_kb=max(r['rss_kb'] for r in rs if r['case']==case)) for case in {r['case'] for r in rs}})
  t.write_json(out/'summary.json',dict(arms=summary,qualification='CANDIDATE_MICROBENCHMARK_PENDING_NATIVE_AND_208',base=t.BASE,harness=os.environ.get('GITHUB_SHA')))
 else:
  state=json.loads((out/'state.json').read_text());native=None;baseline=None
  for name,_,_ in ARMS:
   if not state[name]['built']:continue
   arm=out/name;k=arm/'metatron-kernel';benv=dict(os.environ,CARGO_TARGET_DIR=str(arm/'target'))|env
   benv['NUCLEUS_FROZEN196']=str(root/'inputs')
   state[name]['external_native_fixture_boundary']='current208 artifact13126161718; archived196 is unavailable'
   nr=t.native_suite(k,benv,arm)
   rows=t.replay(arm/'nucleus',manifest,root,env,arm/'verdicts.json')
   if name=='baseline':t.validate_baseline(rows);baseline=rows;native=nr
   diff=[a['case'] for a,b in zip(baseline,rows) if a['rc']!=b['rc']]
   state[name].update(native_targets=nr,native_parity=t.native_reports_match(nr,native),parity=not diff,differences=diff,counts={str(rc):sum(r['rc']==rc for r in rows) for rc in (0,1,2)})
   t.write_json(out/'state.json',state);print(name,json.dumps(state[name]),flush=True);shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['spike','qualify']);p.add_argument('--out',required=True);p.add_argument('--inputs',required=True);main(p.parse_args())
