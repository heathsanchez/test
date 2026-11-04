from pathlib import Path
import hashlib,json,tarfile,subprocess,shutil
R=Path(__file__).resolve().parent;P=R.parent/'receipts/quotient-result-projection';out=R/'readback';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path('/tmp/quotient-result-qualified.zip'))=='9d0ffa1d7ef5c09121477e7543c5abf1b35ec56391dd53fc89d755d737e43e73'
q=json.loads((P/'quotient-result-projection.json').read_text());assert q['qualified']and q['binary_sha']=='173ff543e6fe368d501fe2c0682e98673fd4b259a6ddc1745fcbee76ff99fb1e';assert sha(P/'candidate/nucleus')==q['binary_sha'];assert q['source_controls']==119 and q['protected_controls']==61 and q['native_targets']==42 and q['native_counts']==[489,1,0,0,0]
manifest=json.loads((P/'candidate/source-manifest.json').read_text());assert len(manifest)==368
with tarfile.open(P/'candidate/source.tar.gz')as t:t.extractall(out/'archive',filter='data')
parent=R.parent/'projected-function-eta/source/metatron-kernel';base_manifest=json.loads((R.parent/'receipts/projected-function-eta/candidate/source-manifest.json').read_text())
for n,h in base_manifest.items():assert sha(parent/n)==h,n
shutil.copytree(parent,out/'reconstructed/metatron-kernel')
patch=R/'quotient-result-projection.patch';assert sha(patch)=='7fe08412e93652d60bdba0dc3fc499cebb34e7f344fe3d8db254c1cf8775d650'
with (out/'patch.log').open('wb')as log:subprocess.run(['patch','--fuzz=0','-p1','-i',str(patch.resolve())],cwd=out/'reconstructed',stdout=log,stderr=subprocess.STDOUT,check=True)
for n,h in manifest.items():
 assert sha(out/'archive/metatron-kernel'/n)==h,('archive',n)
 assert sha(out/'reconstructed/metatron-kernel'/n)==h,('reconstructed',n)
assert q['full']['source_sha']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'and q['full']['result']['rc']==2
assert q['full']['next_frontier']['sha256']=='ca6ba58a99ca074dc45d975ab982fd119193fa05a6d12e20f08c53cb7dd786f2'
assert q['full']['frontier_official_reference']['parse_rc']==q['full']['frontier_official_reference']['rc']==0
f=out/'next-frontier.ndjson';subprocess.run(['zstd','-dq',str(P/'next-frontier.ndjson.zst'),'-o',str(f)],check=True);assert sha(f)==q['full']['next_frontier']['sha256']
checks=json.loads((P/'qualification.json').read_text())['candidate'];assert checks['qualified']and not checks['verdict_changes']
native=json.loads((P/'candidate/native-targets.json').read_text());oracle=(P/'frontier-oracle/reference.stdout').read_text()if(P/'frontier-oracle/reference.stdout').exists()else''
report=dict(status='VERIFIED_SEALED_QUALIFICATION_AND_COMPLETE_TRANSITIVE_SOURCE_RECONSTRUCTION',source_commit='59cc9234dc6d1a35820debc5d4ce264df58a3e08',run_id=41841710394,artifact_id=13332531103,zip_sha=sha(Path('/tmp/quotient-result-qualified.zip')),binary_sha=sha(P/'candidate/nucleus'),source_tar_sha=sha(P/'candidate/source.tar.gz'),source_manifest_sha=sha(P/'candidate/source-manifest.json'),cumulative_patch_sha=sha(P/'candidate/source.patch'),parent_canonical_recipe_commit='3bf4268285f40b50cb183d0f31989dd7932e5a8a',parent_manifest_sha=sha(R.parent/'receipts/projected-function-eta/candidate/source-manifest.json'),component_patch_sha=sha(patch),archive_source_matches=len(manifest),reconstructed_source_matches=len(manifest),source_controls=119,protected_controls=61,native_targets=42,native_counts=q['native_counts'],verdict_changes=checks['verdict_changes'],full=q['full'],no_speed_ratio_different_frontiers=True,no_rank_claim=True)
(out/'verified-readback.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
