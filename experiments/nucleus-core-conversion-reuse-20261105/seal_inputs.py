"""Seal already checked immutable inputs for future SHA-pinned reuse."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tarfile
R=Path('/tmp/nucleus-core-conversion-reuse');D=R/'corpus';D.mkdir(exist_ok=True);(D/'inputs').mkdir(exist_ok=True);(D/'receipts').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];unique={};missing=[]
def add(source,group,case,expected_sha,metadata):
 source=Path(source);assert sha(source)==expected_sha,source
 target=D/'inputs'/(expected_sha+'.ndjson')
 if not target.exists():shutil.copyfile(source,target)
 unique[expected_sha]=source.stat().st_size
 rows.append(dict(group=group,case=case,sha256=expected_sha,bytes=source.stat().st_size,metadata=metadata))
registry=json.loads((R/'input-registry.json').read_text())
for entry in registry:
 row=entry['row'];add(Path(entry['directory'])/row['file'],entry['group'],row.get('case',row['file']),row['sha256'],row)
 gate=R/entry['group']
 if gate.is_file():shutil.copyfile(gate,D/'receipts'/gate.name)
manifest=json.loads(Path('/tmp/current208/inputs-manifest.json').read_text());assert len(manifest)==208
parent=json.loads(Path('/tmp/bounded-default/candidate/verdicts.json').read_text());parent={r['case']:r for r in parent}
for row in manifest:
 assert parent[row['case']]['sha256']==row['sha256'] and parent[row['case']]['expected']==row['expected']
 add(Path('/tmp/current208/inputs')/row['relative_path'],'frozen208',row['case'],row['sha256'],parent[row['case']])
qualification=json.loads((R/'qualification.json').read_text())['candidate'];needed={r['sha256']:r for r in qualification['controls']};names={r['file']for r in needed.values()}
# These protected fixtures usually live in source or experiment inputs. Missing
# optional fixtures are recorded explicitly; this bundle replaces no gate.
for root in [R/'candidate/metatron-kernel',Path.cwd()/'experiments']:
 if root.exists():
  for source in root.rglob('*.ndjson'):
   if source.name in names:
    digest=sha(source)
    if digest in needed:
     row=needed.pop(digest);add(source,'protected61',row['file'],digest,row)
missing=list(needed)
for name in ['qualification.json','core-conversion-reuse.json','timing.json','full.json']:
 if (R/name).is_file():shutil.copyfile(R/name,D/'receipts'/name)
receipt=dict(status='SEALED_CHECKED_INPUT_BUNDLE',replaces_no_qualification_gate=True,source_groups=sorted({r['group']for r in rows if r['group']not in('frozen208','protected61')}),rows=rows,unique_inputs=len(unique),uncompressed_unique_bytes=sum(unique.values()),frozen208_complete=True,protected61_complete=not missing,missing_protected_sha256=missing,authority_run=os.environ.get('GITHUB_RUN_ID'),candidate_binary_sha256=qualification['binary_sha'],candidate_source_manifest_sha256=sha(R/'candidate/source-manifest.json'),receipt_hashes={p.name:sha(p)for p in sorted((D/'receipts').iterdir())if p.is_file()},no_rank_claim=True)
(D/'manifest.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
archive=R/'checked-inputs.tar.zst'
with subprocess.Popen(['zstd','-q','-T1','-6','--long=27','-o',str(archive)],stdin=subprocess.PIPE)as process:
 with tarfile.open(fileobj=process.stdin,mode='w|')as tar:
  for p in sorted(D.rglob('*')):
   if p.is_file():
    info=tar.gettarinfo(str(p),arcname='corpus/'+str(p.relative_to(D)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
    with p.open('rb')as f:tar.addfile(info,f)
 process.stdin.close();assert process.wait()==0
summary={k:receipt[k]for k in ['status','unique_inputs','uncompressed_unique_bytes','frozen208_complete','protected61_complete','missing_protected_sha256','authority_run','candidate_binary_sha256','candidate_source_manifest_sha256','replaces_no_qualification_gate']};summary.update(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,manifest_sha256=sha(D/'manifest.json'));(R/'checked-inputs.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
