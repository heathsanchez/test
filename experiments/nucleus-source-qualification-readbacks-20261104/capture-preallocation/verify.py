from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.candidate.read_bytes())=='1df7654f16176be8bbd883984640683551c88c3a8d87555c4fb9ad8f65f91f22';assert sha(a.parent.read_bytes())=='a63110abcccf930aa74d18a9dbe895a1d2b00b7d078232e2a90fa882806b7c48';assert sha(a.component.read_bytes())=='914fc30361a4a546553ce27fb104dbfe5c27000dce814938799b681ec1e1ba0c';a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.candidate)as z:
 manifest_raw=z.read('candidate/source-manifest.json');manifest=json.loads(manifest_raw);tar_raw=z.read('candidate/source.tar.gz');report=json.loads(z.read('capture-preallocation.json'));q=json.loads(z.read('qualification.json'))['candidate'];binary=z.read('candidate/nucleus')
 assert report['source_qualified']and not report['qualified']and report['status']=='QUALIFIED_NO_ESTABLISHED_SPEED_WIN';assert sha(binary)==report['binary_sha']=='76db01ef1a701e244f5601aa4b9c10b76bbe8a75ae3707d76a5eae14057e942b'
 with tarfile.open(fileobj=io.BytesIO(tar_raw))as t:t.extractall(a.out/'archive',filter='data')
 patch_raw=z.read('candidate/source.patch');assert sha(patch_raw)==report['source_patch_sha']
with zipfile.ZipFile(a.parent)as z:
 parent=json.loads(z.read('qualification.json'))['candidate'];base_manifest=json.loads(z.read('candidate/source-manifest.json'));base_tar=z.read('candidate/source.tar.gz');assert sha(base_tar)=='1b25f9ea47c1d6f430228a473a547490d2c3fa1cf70867c4f0c02c697ce10e23';assert parent['configuration']==q['configuration']
 with tarfile.open(fileobj=io.BytesIO(base_tar))as t:t.extractall(a.out/'reconstructed',filter='data')
def inventory(root):return{str(p.relative_to(root)):sha(p.read_bytes())for p in root.rglob('*')if p.is_file()}
archive=a.out/'archive/metatron-kernel';reconstructed=a.out/'reconstructed/metatron-kernel';assert inventory(archive)==manifest;assert inventory(reconstructed)==base_manifest
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(a.component.resolve())],cwd=reconstructed,capture_output=True);(a.out/'patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0;assert inventory(reconstructed)==manifest;assert len(manifest)==368
receipt=dict(status='VERIFIED_SOURCE_QUALIFIED_NOT_PROMOTABLE',source_commit='bda54625cb1ff79ca5a89cc4acea8dcf57c6c41a',run_id=41886766725,artifact_id=13354897179,artifact_sha256=sha(a.candidate.read_bytes()),binary_sha256=sha(binary),source_tar_sha256=sha(tar_raw),source_manifest_sha256=sha(manifest_raw),cumulative_patch_sha256=sha(patch_raw),component_sha256=sha(a.component.read_bytes()),archive_files=368,reconstructed_files=368,exact_file_sets=True,configuration_unchanged=True,source_qualified=True,promotable=False,speed_preset_passed=False,median_cpu_ratio=report['timing']['median_cpu_ratio'],complete_mathlib_accept=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
