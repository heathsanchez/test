from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile,statistics
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.candidate.read_bytes())=='0fd8a4cd86dcb233b532f59ea8dc853d22480b6ba62ff864049224250613e517';assert sha(a.parent.read_bytes())=='79a49583b5e9c4742c4280075b41cdd89ba44f2d96b402af8f90ef4750897e8d';assert sha(a.component.read_bytes())=='77efb609a00f2cfe0a2265c2515ae06c483c348b3e262a8beb431847c66ed4c6';a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.candidate)as z:
 manifest_raw=z.read('candidate/source-manifest.json');manifest=json.loads(manifest_raw);tar_raw=z.read('candidate/source.tar.gz');r=json.loads(z.read('substitution-certificate.json'));q=json.loads(z.read('qualification.json'))['candidate'];binary=z.read('candidate/nucleus');patch=z.read('candidate/source.patch');frozen=json.loads(z.read('candidate/verdicts.json'));matched=json.loads(z.read('matched-regressions.json'))
 assert r['qualified']and r['source_qualified']and r['coverage_win']and r['status']=='PROMOTABLE_SUBSTITUTION_CERTIFICATE_COVERAGE'
 assert sha(binary)==r['binary_sha']==q['binary_sha']=='2003c831c32a8249e8524349bc169f3e491e9c84fb71b5fc8db9bce2a8583d01'
 assert sha(patch)==r['source_patch_sha']=='a151dea2d61ac005f20c75f47aa42f7b1757592ef2143721e1a6c584c128c2a6'
 assert r['native_counts']==[552,1,0,0,0]and r['native_targets']==42 and r['source_controls']==119 and r['protected_controls']==61
 assert r['known_native_failures']=={'residual_closure|test':['all_seven_complete_positive_exports_accept']}
 assert q['qualified']and q['verdict_changes']==[]and q['extra_unchanged']and q['controls_unchanged']and q['native_nonregression_to_promotion_parent']
 assert b'246 passed; 0 failed; 0 ignored;'in z.read('native-completion-tests.stdout')
 assert matched['status']=='COMPLETE'and len(matched['rows'])==2
 assert{row['input_sha']for row in matched['rows']}=={'ca6ba58a99ca074dc45d975ab982fd119193fa05a6d12e20f08c53cb7dd786f2','ef5df79ed54b93ec8597131304c9ed76358dd4a60c5bf7275fb0033a9fe9e431'}
 assert all(row['red']['rc']==2 and row['green']['rc']==0 and row['parent_binary']=='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715'and row['candidate_binary']==sha(binary)for row in matched['rows'])
 with tarfile.open(fileobj=io.BytesIO(tar_raw))as t:t.extractall(a.out/'archive',filter='data')
 for name in ['qualification.json','substitution-certificate.json','timing.json','matched-regressions.json','full.json','native-completion-tests.stdout']:(a.out/name).write_bytes(z.read(name))
with zipfile.ZipFile(a.parent)as z:
 parent=json.loads(z.read('qualification.json'))['candidate'];base_manifest=json.loads(z.read('candidate/source-manifest.json'));base_tar=z.read('candidate/source.tar.gz');old_frozen=json.loads(z.read('candidate/verdicts.json'))
 assert parent['qualified']and parent['binary_sha']==r['parent_binary']=='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715'
 assert parent['configuration']==q['configuration']
 assert sha(base_tar)=='4203d0e41e00b52ec8ff4acc7182407b6658b4b9d556c8056000228e208f2318'
 with tarfile.open(fileobj=io.BytesIO(base_tar))as t:t.extractall(a.out/'reconstructed',filter='data')
assert set(parent['native']['targets'])==set(q['native']['targets'])and len(q['native']['targets'])==42
for name,old in parent['native']['targets'].items():
 new=q['native']['targets'][name];assert old['complete']and new['complete'];assert new['counts'][0]>=old['counts'][0]and new['counts'][1:]==old['counts'][1:]and sorted(new['failures'])==sorted(old['failures'])
signature=lambda rows:[(row['case'],row['expected'],row['rc'],row['sha256'])for row in rows]
assert len(frozen)==len(old_frozen)==208 and signature(frozen)==signature(old_frozen)
def inventory(root):return{str(p.relative_to(root)):sha(p.read_bytes())for p in root.rglob('*')if p.is_file()}
archive=a.out/'archive/metatron-kernel';reconstructed=a.out/'reconstructed/metatron-kernel';assert inventory(archive)==manifest;assert inventory(reconstructed)==base_manifest
patched=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(a.component.resolve())],cwd=reconstructed,capture_output=True);(a.out/'component-application.log').write_bytes(patched.stdout+patched.stderr);assert patched.returncode==0;assert inventory(reconstructed)==manifest and len(manifest)==368
full=r['full'];assert full['source_sha']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'and full['result']['rc']==2 and not full['complete_mathlib_accept'];assert full['next_frontier']['record']==303563 and full['next_frontier']['sha256']=='61b130d9e864c99afd4111b662f884827be98a87f27277c42a5949b025fc0d6b';assert full['frontier_official_reference']['parse_rc']==full['frontier_official_reference']['rc']==0
rows=r['timing']['rows'];assert r['timing']['status']=='COMPLETE'and [row['arm']for row in rows]==['candidate','parent','parent','candidate'];assert all(row['rc']==0 and row['input_sha']=='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'for row in rows)
old=[row['user']+row['system']for row in rows if row['arm']=='parent'];new=[row['user']+row['system']for row in rows if row['arm']=='candidate'];ratio=statistics.median(new)/statistics.median(old);assert max(new)<min(old)*.99 and r['timing']['speed_win']and ratio==r['timing']['median_cpu_ratio'];rss=statistics.median(row['rss_kb']for row in rows if row['arm']=='candidate')/statistics.median(row['rss_kb']for row in rows if row['arm']=='parent')
(a.out/'nucleus').write_bytes(binary);(a.out/'nucleus').chmod(0o755)
receipt=dict(status='VERIFIED_PROMOTABLE_SUBSTITUTION_CERTIFICATE',source_commit='be214a436a84c12b71b852106d73f6c39a3a5d8d',run_id=41928340975,artifact_id=13370874970,artifact_sha256=sha(a.candidate.read_bytes()),binary_sha256=sha(binary),source_tar_sha256=sha(tar_raw),source_manifest_sha256=sha(manifest_raw),cumulative_patch_sha256=sha(patch),component_sha256=sha(a.component.read_bytes()),archive_files=368,reconstructed_files=368,exact_file_sets=True,configuration_unchanged=True,frozen208_unchanged=True,native_nonregression_to_actual_default=True,native_counts=r['native_counts'],library_passed=246,source_qualified=True,promotable=True,coverage_win=True,accepted_original_old_frontier=True,new_frontier_record=303563,speed_preset_passed=True,median_cpu_ratio=ratio,median_rss_ratio=rss,complete_mathlib_accept=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
