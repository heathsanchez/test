#!/usr/bin/env python3
"""Independent source-derived final-proof congruence qualification."""
import argparse,difflib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[0]/'nucleus-reuse-20261104'))
import tournament as t
sys.path.insert(0,str(ROOT.parents[0]/'nucleus-prefix-sharing-20261104'))
from patch import prefix_patch
PREFIX_SHA='856050129c6f620672154aab7df37c2ba73d777034d583739ebcb78a231cfd61'

def materialize(out,semantic=True):
 k=t.materialize(Path.cwd(),out,table=True)
 for relative in ['src/parser.rs','src/typecheck.rs']:
  p=k/relative;old=p.read_text()
  if relative.endswith('parser.rs'):
   new=t.replace_once(old,'pub fn parse<R: BufRead>','#[cfg(test)]\nfn parse_reference<R: BufRead>')+'\n'+(ROOT.parents[0]/'nucleus-structural-import-20261104/hot_parser.rs').read_text()
  else:new=prefix_patch(old)
  p.write_text(new)
  with (out/'source.patch').open('a') as f:f.write(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/metatron-kernel/'+relative,tofile='b/metatron-kernel/'+relative)))
 if semantic:
  r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'semantic.patch')],cwd=out,capture_output=True,timeout=30)
  (out/'patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write((ROOT/'semantic.patch').read_text())
 # Guard tests run against both arms and cannot supply a production assumption.
 with(k/'src/typecheck.rs').open('a')as f:f.write('\n'+(ROOT/'final_proof_guard_tests.rs').read_text())
 (k/'tests/final_proof_spine.rs').write_text((ROOT/'final_proof_spine.rs').read_text())
 fixture=k/'tests/fixtures/final-proof';fixture.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'controls').glob('*.ndjson'):shutil.copy2(p,fixture/p.name)
 subprocess.run(['zstd','-d','-f',str(ROOT/'fixtures/recOnSwap-prefix.ndjson.zst'),'-o',str(fixture/'recOnSwap-prefix.ndjson')],check=True,capture_output=True)
 assert t.digest(fixture/'recOnSwap-prefix.ndjson')==PREFIX_SHA
 return k

def native_nonregression(a,b):
 if not(a['compiled']and b['compiled'])or set(a['targets'])!=set(b['targets']):return False
 for name,x in a['targets'].items():
  y=b['targets'][name]
  if not(x['complete']and y['complete'])or not set(x['failures']).issubset(y['failures']):return False
  if sum(x['counts'][:4])<sum(y['counts'][:4]):return False
 return True

def qualify(out):
 inputs=Path('/tmp/current208');manifest=json.loads((inputs/'inputs-manifest.json').read_text());state={};baseline=None;nr0=None
 for name,semantic in [('baseline',False),('candidate',True)]:
  arm=out/name;k=materialize(arm,semantic);binary,env=t.build(k,arm);assert binary is not None
  env|=t.run_env();env['NUCLEUS_FROZEN196']=str(inputs/'inputs')
  nr=t.native_suite(k,env,arm);rows=t.replay(binary,manifest,inputs,t.run_env(),arm/'verdicts.json')
  if not semantic:t.validate_baseline(rows);baseline=rows;nr0=nr
  regress=[dict(case=a['case'],before=a['rc'],after=b['rc'])for a,b in zip(baseline,rows)if(b['rc']not in(b['expected'],2)or(a['rc']!=2 and a['rc']!=b['rc']))]
  info=dict(built=True,source_sha=t.digest(arm/'source.patch'),binary_sha=t.digest(binary),native=nr,native_nonregression=native_nonregression(nr,nr0),regressions=regress,counts={str(rc):sum(x['rc']==rc for x in rows)for rc in(0,1,2)})
  if semantic:
   controls=[]
   for p in sorted((ROOT/'controls').glob('*.ndjson')):
    with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=t.run_env(),timeout=30)
    good=p.stem in {'same','proof_last','dependent_proof_last','long_prefix_valid'}
    controls.append(dict(case=p.stem,rc=r.returncode,pass_=(r.returncode==0 if good else r.returncode in(1,2))))
   info['controls']=controls
   info['qualified']=not regress and info['native_nonregression']and all(c['pass_']for c in controls)
  state[name]=info;t.write_json(out/'qualification.json',state);shutil.rmtree(arm/'target',ignore_errors=True)
 assert state['candidate']['qualified'],state['candidate']

def extract_frontier(source,out,name):
 parts=name.split('.');matched={0:0};found=None
 with source.open('rb')as src,out.open('wb')as dst:
  for line_no,line in enumerate(src,1):
   dst.write(line);r=json.loads(line)
   if 'in'in r:
    n=r.get('str')or r.get('num')
    if n:
     parent=matched.get(n.get('pre'));component=str(n.get('str',n.get('i')))
     if parent is not None and parent<len(parts)and component==parts[parent]:matched[r['in']]=parent+1
   for tag in['thm','def','opaque']:
    if tag in r and matched.get(r[tag].get('name'))==len(parts):found=dict(name=name,record=line_no,tag=tag,name_id=r[tag]['name']);break
   if found:break
 if not found:out.unlink();return None
 found.update(sha=t.digest(out),bytes=out.stat().st_size);subprocess.run(['zstd','-T0','-3',str(out)],check=True,capture_output=True);out.unlink();return found

def full(out):
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA
 k=materialize(out/'candidate',True);binary,env=t.build(k,out/'candidate');assert binary is not None
 env=t.run_env();env['NUCLEUS_TRACE_DOWNSTREAM']='1'
 perf=t.probe_perf(out);result=t.measure(binary,source,env,out/'full-input',timeout=5400,perf=perf)
 stderr=(out/'full-input/stderr').read_text();terminal=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',stderr)
 next_fixture=extract_frontier(source,out/'next-frontier.ndjson',terminal[-1]) if terminal and not terminal[-1].startswith('<')else None
 summary=dict(base=t.BASE,harness=os.environ.get('GITHUB_SHA'),source_patch_sha=t.digest(out/'candidate/source.patch'),binary_sha=t.digest(binary),input_sha=t.INPUT_SHA,result=result,complete_mathlib_accept=result['rc']==0,perf_available=perf,next_frontier=next_fixture,configuration={k:v for k,v in env.items()if k.startswith('NUCLEUS_')})
 t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['qualify','full']);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);(qualify if a.phase=='qualify'else full)(out)
