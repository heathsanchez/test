"""Complete missing checks from an immutable, source-qualified partial artifact."""
from pathlib import Path
import argparse,collections,hashlib,json,os,resource,shutil,statistics,subprocess,sys,tarfile,time
from receipt_schema import controls_equal
PARTIAL_ZIP='fa0a06101ca8dda97b9c15f4e106eb24e12b2b46aafb8594a9ffb0f44368cd08'
PARENT_ZIP='0fd8a4cd86dcb233b532f59ea8dc853d22480b6ba62ff864049224250613e517'
CANDIDATE='72ee79b8e1757ff65b06ee37d9321315b9b113f9503cbda635e3ebe1e3b99a41'
PARENT='2003c831c32a8249e8524349bc169f3e491e9c84fb71b5fc8db9bce2a8583d01'
COMPONENT='b509707c86c26b14a06eb5b8bf90f6c157a963b93eaca9c8db69e680b6ce0506'
FRONTIER='61b130d9e864c99afd4111b662f884827be98a87f27277c42a5949b025fc0d6b'
HOT='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'
REFERENCE='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def files(root):return{str(p.relative_to(root)):sha(p)for p in Path(root).rglob('*')if p.is_file()}
def extract(archive,destination):
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive)as t:t.extractall(destination,filter='data')
 return destination/'metatron-kernel'
def source_control_reports(root):
 result={}
 for path in Path(root).glob('*.json'):
  v=load(path)
  if isinstance(v,dict)and v.get('reference_binary')==REFERENCE and isinstance(v.get('rows'),list):result[path.name]=v
 return result

def verify(partial,parent,out,partial_zip,parent_zip):
 assert sha(partial_zip)==PARTIAL_ZIP and sha(parent_zip)==PARENT_ZIP
 q=load(partial/'qualification.json')['candidate'];old=load(parent/'qualification.json')['candidate']
 assert q['qualified']and old['qualified'] and q['binary_sha']==CANDIDATE and old['binary_sha']==PARENT
 assert sha(partial/'candidate/nucleus')==CANDIDATE and sha(parent/'candidate/nucleus')==PARENT
 assert sha(partial/'candidate/source.patch')==COMPONENT and q['source_patch_sha']==COMPONENT
 assert sha(partial/'candidate/source.tar.gz')=='6f68f0ae7e2630e8025820cc922e014a6a318b3b6cef99194a33f1ce0d83bdd3'
 assert sha(partial/'candidate/source-manifest.json')=='d1cfb21fe400d30f9b28278730fcf6d762117ae73a07abc21da2844160f898af'
 assert sha(parent/'candidate/source.tar.gz')=='6cf951197029b596c53ec09c76394204e9bbda90920aa876b9732584c707a1b8'
 assert sha(parent/'candidate/source-manifest.json')=='d229c4cedbedf33fada657711a878763bd051f90be23e3362e9ebf98b42bbb72'
 own=extract(partial/'candidate/source.tar.gz',out/'sealed-source');base=extract(parent/'candidate/source.tar.gz',out/'parent-source');rebuilt=extract(parent/'candidate/source.tar.gz',out/'reconstructed-source')
 actual=files(own);expected=load(partial/'candidate/source-manifest.json');assert actual==expected and len(actual)==368
 assert files(base)==load(parent/'candidate/source-manifest.json')and len(files(base))==368
 process=subprocess.run(['patch','--batch','--no-backup-if-mismatch','--fuzz=0','-p1','-i',str((partial/'candidate/source.patch').resolve())],cwd=rebuilt,capture_output=True);(out/'source-reconstruction.log').write_bytes(process.stdout+process.stderr);assert process.returncode==0
 assert files(rebuilt)==actual,'Exact parent plus component, including file-set identity'
 assert q['configuration']==old['configuration']and len(q['configuration'])==20
 assert set(q['native']['targets'])==set(old['native']['targets'])and len(q['native']['targets'])==42
 for name,prior in old['native']['targets'].items():
  now=q['native']['targets'][name];assert now['complete']and prior['complete']and now['counts'][0]>=prior['counts'][0]and now['counts'][1:]==prior['counts'][1:],name
  assert sorted(now['failures'])==sorted(prior['failures']),name
 assert q['native']['targets']['metatron_kernel|lib']['counts']==[257,0,0,0,0]
 assert controls_equal(q['controls'],old['controls'])and len(q['controls'])==61 and all(r['pass_']for r in q['controls'])
 signature=lambda rows:collections.Counter((r['case'],r['expected'],r['rc'],r['sha256'])for r in rows)
 current=load(partial/'candidate/verdicts.json');before=load(parent/'candidate/verdicts.json');assert len(current)==len(before)==208 and signature(current)==signature(before)
 assert q['controls_unchanged']and q['extra_unchanged']and not q['verdict_changes']
 reports=source_control_reports(partial);prior_reports=source_control_reports(parent);assert sum(len(v['rows'])for v in reports.values())==119
 for name,report in reports.items():
  assert report['candidate_binary']==CANDIDATE and all(r['pass_']for r in report['rows'])
  assert name in prior_reports
  key=lambda rows:collections.Counter((r['case'],r['sha256'],r['expect_reference'],r['reference_parse_rc'],r['reference_rc'],r['nucleus_rc'],r['pass_'])for r in rows)
  assert key(report['rows'])==key(prior_reports[name]['rows']),name
 full=load(partial/'full.json');previous_full=load(parent/'full.json')
 assert full['source_sha']==previous_full['source_sha']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'
 assert full['binary_sha']==CANDIDATE and full['result']['rc']==2 and not full['complete_mathlib_accept']
 assert full['next_frontier']['record']==previous_full['next_frontier']['record']==303563
 assert full['next_frontier']['sha256']==previous_full['next_frontier']['sha256']==FRONTIER
 assert full['next_frontier']['target']=='AddMonoidAlgebra.nonUnitalNonAssocSemiring._proof_2'
 return q,old,own,base,full

def lookup_control(source,row,prefixes=None):
 name=row.get('file',row.get('case'));assert name
 if 'sha256'in row:
  paths=[p for p in source.rglob('*.ndjson')if p.name==Path(name).name and sha(p)==row['sha256']]
  if not paths and prefixes and row['sha256']in prefixes:paths=[prefixes[row['sha256']]]
 else:paths=[source/'tests/fixtures'/group/name for group in ['native-source-replay','final-proof']if(source/'tests/fixtures'/group/name).is_file()]
 assert paths and len({sha(p)for p in paths})==1,('unambiguous canonical control fixture',name,paths)
 return sorted(paths)[0]

def worker(out,index,arm):
 q=load(out/'measurement-inputs.json');path=Path(q['binaries'][arm]);assert sha(path)==q['hashes'][arm];source=out/'hot.ndjson';before=source.stat();assert before.st_size==11654159
 env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration'];directory=out/'timing'/f'{index}-{arm}';directory.mkdir(parents=True,exist_ok=False);start=time.monotonic()
 with source.open('rb')as i,(directory/'stdout').open('wb')as o,(directory/'stderr').open('wb')as e:result=subprocess.run([str(path)],stdin=i,stdout=o,stderr=e,env=env,timeout=900)
 usage=resource.getrusage(resource.RUSAGE_CHILDREN);after=source.stat();assert(before.st_size,before.st_ino,before.st_mtime_ns)==(after.st_size,after.st_ino,after.st_mtime_ns)
 row=dict(arm=arm,order=index,binary_sha256=q['hashes'][arm],input_sha256=HOT,rc=result.returncode,wall=time.monotonic()-start,user=usage.ru_utime,system=usage.ru_stime,cpu=usage.ru_utime+usage.ru_stime,rss_kib=usage.ru_maxrss,stderr=(directory/'stderr').read_text());write(directory/'report.json',row);assert row['rc']==0 and not row['stderr'];print(json.dumps(row),flush=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--partial',type=Path);parser.add_argument('--parent',type=Path);parser.add_argument('--partial-zip',type=Path);parser.add_argument('--parent-zip',type=Path);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--worker',nargs=2);parser.add_argument('--verify-only',action='store_true');a=parser.parse_args()
 if a.worker:worker(a.out,int(a.worker[0]),a.worker[1]);return
 a.out.mkdir(parents=True,exist_ok=False);q,old,own,base,full=verify(a.partial,a.parent,a.out,a.partial_zip,a.parent_zip)
 shutil.copytree(a.partial/'candidate',a.out/'candidate')
 for path in a.partial.glob('*.json'):
  if path.name!='qualification.json':shutil.copyfile(path,a.out/path.name)
 shutil.copyfile(a.partial/'qualification.json',a.out/'reused-qualification.json')
 frontier=a.out/'original-frontier.ndjson';subprocess.run(['zstd','-dq',str(a.partial/'next-frontier.ndjson.zst'),'-o',str(frontier)],check=True);assert sha(frontier)==FRONTIER
 data=frontier.read_bytes();prefixes={}
 for digest,count in [('2833a44b446524b25c8053006a3684d0fdab5779d76ef17695cbd4763ec9a0cd',6119388),('e0034bd4cb29aa1f260a40ced49d03bf4e748a191335bedfd23fce60afa85a48',6133780)]:
  path=a.out/'protected-prefixes'/(digest+'.ndjson');path.parent.mkdir(exist_ok=True);path.write_bytes(data[:count]);assert sha(path)==digest;prefixes[digest]=path
 env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration'];controls=[]
 for index,row in enumerate(q['controls']):
  path=lookup_control(own,row,prefixes);prior=lookup_control(base,row,prefixes);assert sha(path)==sha(prior);name=row.get('file',row.get('case'));results={}
  if not a.verify_only:
   for arm,binary in [('candidate',a.partial/'candidate/nucleus'),('parent',a.parent/'candidate/nucleus')]:
    binary.chmod(0o755);directory=a.out/'fresh-controls'/str(index)/arm;directory.mkdir(parents=True)
    with path.open('rb')as i,(directory/'stdout').open('wb')as o,(directory/'stderr').open('wb')as e:result=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=180)
    assert result.returncode==row['rc'],(name,arm,row['rc'],result.returncode);results[arm]=result.returncode
  controls.append(dict(case=name,source_path=str(path.relative_to(own))if path.is_relative_to(own)else'original-frontier-prefix/'+sha(path)+'.ndjson',sha256=sha(path),expected_rc=row['rc'],prior_recorded_input_hash=row.get('sha256'),results=results))
 receipt=dict(status='VERIFIED_REUSED_SOURCE_QUALIFICATION',source_run=41947915219,source_commit='0b27e4617c0b4fb34f3b49a55755109cfa3d1ae9',source_artifact=13381050552,source_artifact_sha256=PARTIAL_ZIP,parent_artifact_sha256=PARENT_ZIP,source_files=368,component_sha256=COMPONENT,source_tree_matches_archive_and_reconstruction=True,source_controls=119,protected_controls=61,protected_input_hashes_previously_recorded=44,legacy_protected_input_hashes_completed=17,native_targets=42,native_counts=[sum(r['counts'][i]for r in q['native']['targets'].values())for i in range(5)],known_failures={n:r['failures']for n,r in q['native']['targets'].items()if r['failures']},frozen208_unchanged=True,complete_mathlib_accept=False,full_frontier_unchanged=True,controls=controls,fresh_protected_replay=not a.verify_only,qualified=False,promoted=False)
 write(a.out/'verified-receipts.json',receipt)
 if a.verify_only:print(json.dumps({k:v for k,v in receipt.items()if k!='controls'}));return
 (a.out/'hot.ndjson').write_bytes(frontier.read_bytes()[:11654159]);assert sha(a.out/'hot.ndjson')==HOT;(a.out/'hot.ndjson').chmod(0o444)
 # Oracle validity is immutable evidence reused from qualified parent41928340975
 # on exactly this source hash and official binary ae92c625; no new oracle claim.
 write(a.out/'measurement-inputs.json',dict(binaries=dict(candidate=str((a.partial/'candidate/nucleus').resolve()),parent=str((a.parent/'candidate/nucleus').resolve())),hashes=dict(candidate=CANDIDATE,parent=PARENT),configuration=q['configuration'],input_sha256=HOT,oracle_authority_run=41928340975,reference_binary_sha256=REFERENCE))
 rows=[]
 for index,arm in enumerate(['candidate','parent','parent','candidate'],1):
  subprocess.run([sys.executable,str(Path(__file__).resolve()),'--out',str(a.out),'--worker',str(index),arm],check=True);rows.append(load(a.out/'timing'/f'{index}-{arm}/report.json'));write(a.out/'timing.json',dict(status='RUNNING',rows=rows))
 assert sha(a.out/'hot.ndjson')==HOT
 b=[r['cpu']for r in rows if r['arm']=='candidate'];c=[r['cpu']for r in rows if r['arm']=='parent'];br=[r['rss_kib']for r in rows if r['arm']=='candidate'];cr=[r['rss_kib']for r in rows if r['arm']=='parent'];win=max(b)<min(c)*.99
 timing=dict(status='COMPLETE',rows=rows,speed_win=win,median_cpu_ratio=statistics.median(b)/statistics.median(c),median_rss_ratio=statistics.median(br)/statistics.median(cr),accepted_prefix_only=True,preset='Every candidate CPU sample beats every actual parent CPU sample by more than1percent',no_rank_claim=True);write(a.out/'timing.json',timing)
 report=receipt|dict(status='PROMOTABLE_CORE_CONVERSION_REUSE'if win else'SOURCE_QUALIFIED_NO_CPU_WIN',qualified=win,source_qualified=True,binary_sha=CANDIDATE,parent_binary=PARENT,full=full,timing=timing,qualification_completion_run=os.environ.get('GITHUB_RUN_ID'),no_official_rank_claim=True,source_tar_sha256=sha(a.partial/'candidate/source.tar.gz'),source_manifest_sha256=sha(a.partial/'candidate/source-manifest.json'))
 write(a.out/'core-conversion-reuse.json',report);write(a.out/'reused-qualification.json',dict(candidate=q));q.update(status=report['status'],source_qualified=True,promotion_parent=PARENT,native_nonregression_to_promotion_parent=True,native_promotion_parent_binary=PARENT);write(a.out/'qualification.json',dict(candidate=q))
 print('CORE_CONVERSION_REUSE_COMPLETED',json.dumps({k:v for k,v in report.items()if k not in('controls','full')}),flush=True)
if __name__=='__main__':main()
