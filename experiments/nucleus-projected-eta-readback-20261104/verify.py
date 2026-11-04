from pathlib import Path,PurePosixPath
import hashlib,json,tarfile,zipfile,subprocess
ROOT=Path('/tmp/nucleus-eta-readback');ROOT.mkdir(exist_ok=True)
ZIP=Path('/tmp/nucleus-eta-qualified.zip')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(ZIP)=='69c5c4bb1d2351655745a0a8e8378e980ab8710d347e3a2552426eb1b34e86f9'
with zipfile.ZipFile(ZIP)as z:
 for n in z.namelist():
  p=PurePosixPath(n);assert not p.is_absolute()and '..'not in p.parts
 z.extractall(ROOT/'artifact')
A=ROOT/'artifact';C=A/'candidate';q=json.loads((A/'qualification.json').read_text())['candidate']
report=json.loads((A/'projected-function-eta.json').read_text());full=json.loads((A/'full.json').read_text())
assert q['qualified']and report['qualified']and q['controls_unchanged']and q['extra_unchanged']and not q['verdict_changes']
assert q['binary_sha']==report['binary_sha']==full['binary_sha']=='c43b174abbad341e5b308d93cd66a28e42db9d9425796ed33b16c644e142ae8e'
assert digest(C/'nucleus')==q['binary_sha']
assert digest(C/'source.patch')==q['source_patch_sha']=='c62dc3823971c76d14db6861b7a5ab795fad6bc4b366c60f8e9226f2e604b86c'
manifest=json.loads((C/'source-manifest.json').read_text())
assert len(manifest)==368
with tarfile.open(C/'source.tar.gz')as t:t.extractall(ROOT/'archived',filter='data')
archived=ROOT/'archived/metatron-kernel'
paths={str(p.relative_to(archived))for p in archived.rglob('*')if p.is_file()}
assert paths==set(manifest)
for n,sha in manifest.items():
 p=PurePosixPath(n);assert not p.is_absolute()and '..'not in p.parts
 assert digest(archived/n)==sha,n
reconstructed=ROOT/'reconstructed';reconstructed.mkdir()
with (ROOT/'base.tar').open('wb')as f:subprocess.run(['git','archive','a2578e77079719ff2064f910bd82fd01d8e120b6','metatron-kernel'],stdout=f,check=True)
with tarfile.open(ROOT/'base.tar')as t:t.extractall(reconstructed,filter='data')
patch=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(C/'source.patch')],cwd=reconstructed,capture_output=True)
(ROOT/'patch.log').write_bytes(patch.stdout+patch.stderr);assert patch.returncode==0
source=reconstructed/'metatron-kernel'
assert {str(p.relative_to(source))for p in source.rglob('*')if p.is_file()}==set(manifest)
for n,sha in manifest.items():assert digest(source/n)==sha,n
assert len(q['native']['targets'])==42 and all(r['complete']for r in q['native']['targets'].values())
counts=[sum(r['counts'][i]for r in q['native']['targets'].values())for i in range(5)]
assert counts==[486,1,0,0,0]and report['source_controls']==113 and report['protected_controls']==61
assert len(json.loads((C/'verdicts.json').read_text()))==208
assert full['source_sha']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'and full['result']['rc']==2
assert full['next_frontier']['sha256']=='13ea49b22c1d367dbe44a6301a4d4c71dd623e40afa8ab4b8e5728e5f1659d26'
assert full['frontier_official_reference']['parse_rc']==full['frontier_official_reference']['rc']==0
frontier=ROOT/'frontier.ndjson'
subprocess.run(['zstd','-dq',str(A/'next-frontier.ndjson.zst'),'-o',str(frontier)],check=True)
assert digest(frontier)==full['next_frontier']['sha256']
verified=dict(status='VERIFIED_ARCHIVE_AND_SOURCE_RECONSTRUCTION',source_commit='3d64f88e3f7194b495428e10cd9536a0aac2f745',source_base='a2578e77079719ff2064f910bd82fd01d8e120b6',qualification_run=41830566061,artifact=13325481741,zip_sha=digest(ZIP),binary_sha=q['binary_sha'],patch_sha=q['source_patch_sha'],source_tar_sha=digest(C/'source.tar.gz'),source_manifest_sha=digest(C/'source-manifest.json'),source_files=len(manifest),all_archived_files_match=True,all_reconstructed_files_match=True,source_controls=113,protected_controls=61,native_targets=42,native_counts=counts,frozen_cases=208,frozen_changes=q['verdict_changes'],extra_unchanged=q['extra_unchanged'],full=full,no_official_rank_claim=True)
(ROOT/'verified-readback.json').write_text(json.dumps(verified,indent=2))
print('VERIFIED_READBACK '+json.dumps(verified),flush=True)
