"""Regenerate previously verified inputs once; seal exact bytes and their receipts."""
from pathlib import Path
import argparse,collections,hashlib,json,os,shutil,subprocess,tarfile,textwrap,types
COMPLETE_ZIP='0167b15caae9b474ae0d6540466ec68ef6fac2786b3eb263554d5e94c055adbb'
INPUT_ZIP='462e31e21379054490570b465b46ece4fff878490d9ad7de6bbc73149d587f4c'
FRONTIER='61b130d9e864c99afd4111b662f884827be98a87f27277c42a5949b025fc0d6b'
BINARY='72ee79b8e1757ff65b06ee37d9321315b9b113f9503cbda635e3ebe1e3b99a41'
REFERENCE='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--completion',type=Path,required=True);p.add_argument('--completion-zip',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--inputs-zip',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert sha(a.completion_zip)==COMPLETE_ZIP and sha(a.inputs_zip)==INPUT_ZIP
 report=load(a.completion/'core-conversion-reuse.json');assert report['qualified']and report['source_qualified']and report['fresh_protected_replay']and report['binary_sha']==BINARY
 assert sha(a.completion/'candidate/nucleus')==BINARY
 archive=a.completion/'candidate/source.tar.gz';assert sha(archive)=='6f68f0ae7e2630e8025820cc922e014a6a318b3b6cef99194a33f1ce0d83bdd3'
 restored=a.out.parent/(a.out.name+'-sealed-source');restored.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive)as source_tar:source_tar.extractall(restored,filter='data')
 source=restored/'metatron-kernel';source_manifest=load(a.completion/'candidate/source-manifest.json');actual={str(f.relative_to(source)):sha(f)for f in source.rglob('*')if f.is_file()};assert actual==source_manifest and len(actual)==368
 frontier=a.completion/'original-frontier.ndjson';assert sha(frontier)==FRONTIER;data=frontier.read_bytes();wanted={r['sha256']:Path(r['path'])for r in load(Path(__file__).with_name('prefixes.json'))};h=hashlib.sha256();offset=0;found={}
 for line in data.splitlines(True):
  h.update(line);offset+=len(line);digest=h.hexdigest()
  if digest in wanted:
   path=wanted[digest];assert path.parent==Path('/tmp')and path.name.endswith('-prefix.ndjson')
   if path.exists():assert sha(path)==digest
   else:path.write_bytes(data[:offset])
   found[digest]=offset
 assert set(found)==set(wanted),'All historical inputs must come from exact verified original prefixes'
 alias=Path('/tmp/mathlib.ndjson')
 if alias.exists():
  with alias.open('rb')as f:assert hashlib.sha256(f.read(len(data))).hexdigest()==FRONTIER
 else:alias.write_bytes(data)
 a.out.mkdir(parents=True,exist_ok=False);generated=a.out/'generated';generated.mkdir();root=a.repo/'experiments/nucleus-core-conversion-reuse-20261105'
 program=(root/'qualify.py').read_text();start=program.index(" source=Path('/tmp/singleton-add-prefix.ndjson')");end=program.index(' def additional(',start)
 # Execute only the unchanged, existing input-generation region, not build,
 # native tests, checker calls or qualification. Every output is rehashed below.
 scope=dict(INT="231655af734415d00fcc7dc83cffe7d96f97406d1d3cd93554ff49aa6de8e521",ROOT=root,OUT=generated,kernel=source,t=types.SimpleNamespace(digest=sha),Path=Path,json=json,shutil=shutil,subprocess=subprocess)
 exec(compile(textwrap.dedent(program[start:end]),str(root/'qualify.py')+':input-generation','exec'),scope)
 generator=a.repo/'experiments/nucleus-k-canonical-20261104/generate.py'
 for input_file,directory,extra in [('std-prefix.ndjson','differential-inputs',[]),('std-prefix.ndjson','differential-inputs/closed',['--closed']),('ac-prefix.ndjson','ac-inputs',['--record']),('information-prefix.ndjson','carrier-inputs',['--information']),('evaluation-prefix.ndjson','universe-inputs',['--evaluation'])]:
  subprocess.run(['python3',str(generator),'--source','/tmp/'+input_file,'--out',str(generated/directory),*extra],check=True)
 bundle=a.out/'corpus';(bundle/'inputs').mkdir(parents=True);(bundle/'receipts').mkdir();entries=[];unique={}
 def add(path,group,case,digest,metadata,authority_run):
  path=Path(path);assert sha(path)==digest,(group,case,path);target=bundle/'inputs'/(digest+'.ndjson')
  if not target.exists():shutil.copyfile(path,target)
  unique[digest]=path.stat().st_size;entries.append(dict(group=group,case=case,sha256=digest,bytes=path.stat().st_size,metadata=metadata,authority_run=authority_run,candidate_binary_sha256=BINARY))
 registry=load(a.completion/'input-registry.json');assert len(registry)==119
 old_root='/tmp/nucleus-core-conversion-reuse/'
 for entry in registry:
  row=entry['row'];directory=entry['directory']
  if directory.startswith(old_root):directory=generated/directory[len(old_root):]
  else:
   assert '/experiments/'in directory;directory=a.repo/'experiments'/directory.split('/experiments/',1)[1]
  gate=load(a.completion/entry['group']);assert gate['reference_binary']==REFERENCE and gate['candidate_binary']==BINARY
  matches=[r for r in gate['rows']if r['case']==row['case']and r['sha256']==row['sha256']];assert len(matches)==1 and matches[0]['pass_']
  add(directory/row['file'],'source119/'+entry['group'],row['case'],row['sha256'],matches[0],41947915219)
  shutil.copyfile(a.completion/entry['group'],bundle/'receipts'/entry['group'])
 controls=report['controls'];assert len(controls)==61
 for row in controls:
  assert row['results']==dict(parent=row['expected_rc'],candidate=row['expected_rc'])
  path=source/row['source_path']if not row['source_path'].startswith('original-frontier-prefix/')else a.completion/'protected-prefixes'/(row['sha256']+'.ndjson')
  add(path,'protected61',row['case'],row['sha256'],row,41954263475)
 manifest=load(a.inputs/'inputs-manifest.json');verdicts={r['case']:r for r in load(a.completion/'candidate/verdicts.json')};assert len(manifest)==len(verdicts)==208
 for row in manifest:
  old=verdicts[row['case']];assert old['sha256']==row['sha256']and old['expected']==row['expected']
  add(a.inputs/'inputs'/row['relative_path'],'frozen208',row['case'],row['sha256'],old,41947915219)
 shutil.copyfile(a.completion/'candidate/verdicts.json',bundle/'receipts/frozen208-verdicts.json')
 for name in ['core-conversion-reuse.json','verified-receipts.json','qualification.json','full.json','timing.json']:
  shutil.copyfile(a.completion/name,bundle/'receipts'/name)
 result=dict(schema='nucleus-checked-inputs-v1',status='SEALED_CHECKED_INPUT_CORPUS',entries=entries,entries_count=len(entries),source_controls=119,protected_controls=61,frozen_controls=208,unique_inputs=len(unique),uncompressed_unique_bytes=sum(unique.values()),prefix_count=len(found),prefixes=found,source_artifact=13381050552,source_artifact_sha256='fa0a06101ca8dda97b9c15f4e106eb24e12b2b46aafb8594a9ffb0f44368cd08',completion_artifact=13381489248,completion_artifact_sha256=COMPLETE_ZIP,frozen_input_artifact=13126161718,frozen_input_artifact_sha256=INPUT_ZIP,candidate_binary_sha256=BINARY,reference_binary_sha256=REFERENCE,configuration=load(a.completion/'qualification.json')['candidate']['configuration'],bootstrap_run=os.environ.get('GITHUB_RUN_ID'),source_checker_tests_reexecuted=False,receipts_reused_only_after_exact_input_hash_match=True,requires_fresh_new_candidate_execution=True,receipt_hashes={p.name:sha(p)for p in sorted((bundle/'receipts').iterdir())if p.is_file()},no_rank_claim=True)
 assert len(entries)==388;write(bundle/'manifest.json',result)
 archive=a.out/'checked-inputs.tar.zst'
 with subprocess.Popen(['zstd','-q','-T1','-6','--long=27','-o',str(archive)],stdin=subprocess.PIPE)as process:
  with tarfile.open(fileobj=process.stdin,mode='w|')as tar:
   for path in sorted(bundle.rglob('*')):
    if path.is_file():
     info=tar.gettarinfo(str(path),arcname='corpus/'+str(path.relative_to(bundle)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
     with path.open('rb')as f:tar.addfile(info,f)
  process.stdin.close();assert process.wait()==0
 summary={k:v for k,v in result.items()if k not in('entries','receipt_hashes')};summary.update(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,manifest_sha256=sha(bundle/'manifest.json'));write(a.out/'checked-inputs.json',summary);print('CHECKED_INPUT_CORPUS',json.dumps(summary),flush=True)
if __name__=='__main__':main()
