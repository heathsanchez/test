from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,tarfile,time,zipfile,difflib
from prepare import prepare
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();R=a.root;R.mkdir(exist_ok=True)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(Path('/tmp/probe-parent.zip'))=='69c5c4bb1d2351655745a0a8e8378e980ab8710d347e3a2552426eb1b34e86f9'
with zipfile.ZipFile('/tmp/probe-parent.zip')as z:z.extractall(R/'parent')
P=R/'parent';q=json.loads((P/'qualification.json').read_text())['candidate'];assert q['qualified']and q['binary_sha']=='c43b174abbad341e5b308d93cd66a28e42db9d9425796ed33b16c644e142ae8e'
with tarfile.open(P/'candidate/source.tar.gz')as t:t.extractall(R/'source',filter='data')
source=R/'source/metatron-kernel';manifest=json.loads((P/'candidate/source-manifest.json').read_text());assert len(manifest)==368
for n,sha in manifest.items():assert digest(source/n)==sha,n
original=R/'parent-frontier.ndjson';subprocess.run(['zstd','-dq',str(P/'next-frontier.ndjson.zst'),'-o',str(original)],check=True);assert digest(original)=='13ea49b22c1d367dbe44a6301a4d4c71dd623e40afa8ab4b8e5728e5f1659d26'
subprocess.run(['python3','experiments/nucleus-contextual-frontier-readback-20261104/frontier.py','--source',str(original),'--out',str(R/'hot'),'--target','AddMonoidAlgebra.instAddCommMonoid._proof_1'],check=True)
input=R/'hot/signature-diagnostic.ndjson';assert digest(input)=='106882a9c3b884d1afa40733c9a6b3856360c44c014996788a33f92b0b433693'
assert digest(Path('/tmp/probe-reference.zip'))=='9dfaff0a6cb272e6950e301aab75cf99e09a440f5ad881e2e1790019b4add1dd'
with zipfile.ZipFile('/tmp/probe-reference.zip')as z:z.extractall(R/'reference')
reference=R/'reference/bundle/kernel';reference.chmod(0o755);assert digest(reference)=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(q['configuration']);env['NUCLEUS_TRACE_DOWNSTREAM']='1'
def run(label,cmd,source_input=None,timeout=900,build_env=None):
 d=R/label;d.mkdir(parents=True,exist_ok=True);start=time.monotonic()
 with(d/'stdout').open('wb')as out,(d/'stderr').open('wb')as err:
  if source_input:
   with source_input.open('rb')as stream:r=subprocess.run(cmd,stdin=stream,stdout=out,stderr=err,env=build_env or env,timeout=timeout)
  else:r=subprocess.run(cmd,stdout=out,stderr=err,env=build_env or env,timeout=timeout)
 return dict(rc=r.returncode,wall=time.monotonic()-start)
assert run('oracle-parse',[str(reference),'--parse-only',str(input)])['rc']==0
assert run('oracle-reference',[str(reference),str(input)])['rc']==0
baseline=P/'candidate/nucleus';baseline.chmod(0o755);assert digest(baseline)==q['binary_sha'];assert run('baseline',[str(baseline)],input)['rc']==0
rows=[]
for mode in ('first-exact','fifo-exact','fifo-semantic'):
 d=R/'arms'/mode;d.mkdir(parents=True);kernel=d/'metatron-kernel';prepare(source,kernel,mode)
 paths=sorted(p for p in kernel.rglob('*')if p.is_file());(d/'source-manifest.json').write_text(json.dumps({str(p.relative_to(kernel)):digest(p)for p in paths},indent=2))
 parts=[]
 for n in ('src/typecheck.rs','src/checker.rs'):
  x=subprocess.run(['diff','-u','--label','a/metatron-kernel/'+n,'--label','b/metatron-kernel/'+n,str(source/n),str(kernel/n)],capture_output=True);assert x.returncode==1;parts.append(x.stdout)
 (d/'diagnostic.patch').write_bytes(b''.join(parts));build_env=os.environ|dict(CARGO_TARGET_DIR=str(d/'target'))
 b=run(mode+'-build',['cargo','build','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--features','diagnostics'],build_env=build_env);assert b['rc']==0
 binary=d/'target/release/metatron-kernel';result=run(mode,[str(binary)],input);assert result['rc']==0,result
 counts=re.findall(r'EXACT_TYPING_REUSE_PROBE:counts=(\[[^\n]+\])',(R/mode/'stderr').read_text());assert len(counts)==1
 counts=json.loads(counts[0]);assert len(counts)==16
 row=dict(mode=mode,binary_sha=digest(binary),diagnostic_patch_sha=digest(d/'diagnostic.patch'),input_sha=digest(input),result=result,counts=counts,eligible=counts[1],positive_hits=sum(counts[2:5]),hit_fraction=sum(counts[2:5])/max(1,counts[1]),capacity_per_checker=8192,results_reused_for_verdicts=False)
 rows.append(row);(R/'report.json').write_text(json.dumps(dict(status='RUNNING',diagnostic_only=True,rows=rows),indent=2));print('TYPING_PROBE_ARM '+json.dumps(row),flush=True)
 (d/'nucleus').write_bytes(binary.read_bytes())
 import shutil;shutil.rmtree(d/'target')
report=dict(status='COMPLETE_TYPING_REUSE_OPPORTUNITY_TOURNAMENT',diagnostic_only=True,no_performance_win_claim=True,no_official_rank_claim=True,memoization_implemented=False,parent_source_commit='3d64f88e3f7194b495428e10cd9536a0aac2f745',parent_binary_sha=q['binary_sha'],input_sha=digest(input),reference_binary_sha=digest(reference),baseline_rc=0,oracle_parse_rc=0,oracle_rc=0,count_schema=['all_calls','eligible_compound_calls','hits_term','hits_pi','hits_sort','misses','stored','hit_recomputed_unknown','context_too_large','context_nonterm','capacity_events','leaf_calls','leaf_const','leaf_bvar','leaf_sort','leaf_other'],rows=rows)
(R/'report.json').write_text(json.dumps(report,indent=2));print('TYPING_REUSE_TOURNAMENT '+json.dumps(report),flush=True)
