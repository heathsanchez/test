from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.candidate.read_bytes())=='c610d42a78786019f2d9faa4318a444f1694dccaa64330a2125694ffc96f31bf';assert sha(a.parent.read_bytes())=='79a49583b5e9c4742c4280075b41cdd89ba44f2d96b402af8f90ef4750897e8d';assert sha(a.component.read_bytes())=='ac59d1ec617b70cf9ede36607f3dd5e1c38108d347a36a4280f6594938abe70f';a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.candidate)as z:
 manifest_raw=z.read('candidate/source-manifest.json');manifest=json.loads(manifest_raw);tar_raw=z.read('candidate/source.tar.gz');report=json.loads(z.read('parametric-proof-reuse.json'));q=json.loads(z.read('qualification.json'))['candidate'];binary=z.read('candidate/nucleus')
 assert report['source_qualified']and not report['qualified']and report['status']=='QUALIFIED_NO_ESTABLISHED_SPEED_WIN';assert sha(binary)==report['binary_sha']=='cb2b25d43417e18339a43469071dc88849091920719eb5775da5ad99bcd8c4e8'
 with tarfile.open(fileobj=io.BytesIO(tar_raw))as t:t.extractall(a.out/'archive',filter='data')
 patch_raw=z.read('candidate/source.patch');assert sha(patch_raw)==report['source_patch_sha']
with zipfile.ZipFile(a.parent)as z:
 parent=json.loads(z.read('qualification.json'))['candidate'];base_manifest=json.loads(z.read('candidate/source-manifest.json'));base_tar=z.read('candidate/source.tar.gz');assert sha(base_tar)=='4203d0e41e00b52ec8ff4acc7182407b6658b4b9d556c8056000228e208f2318';assert parent['configuration']==q['configuration']
 with tarfile.open(fileobj=io.BytesIO(base_tar))as t:t.extractall(a.out/'reconstructed',filter='data')
def inventory(root):return{str(p.relative_to(root)):sha(p.read_bytes())for p in root.rglob('*')if p.is_file()}
archive=a.out/'archive/metatron-kernel';reconstructed=a.out/'reconstructed/metatron-kernel';assert inventory(archive)==manifest;assert inventory(reconstructed)==base_manifest
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(a.component.resolve())],cwd=reconstructed,capture_output=True);(a.out/'patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0;assert inventory(reconstructed)==manifest;assert len(manifest)==368
receipt=dict(status='VERIFIED_SOURCE_QUALIFIED_NOT_PROMOTABLE',source_commit='77f2973e51796fcb3a99a85ef56bb73f522d4cb0',run_id=41904577745,artifact_id=13361227715,artifact_sha256=sha(a.candidate.read_bytes()),binary_sha256=sha(binary),source_tar_sha256=sha(tar_raw),source_manifest_sha256=sha(manifest_raw),cumulative_patch_sha256=sha(patch_raw),component_sha256=sha(a.component.read_bytes()),archive_files=368,reconstructed_files=368,exact_file_sets=True,configuration_unchanged=True,source_qualified=True,promotable=False,speed_preset_passed=False,median_cpu_ratio=report['timing']['median_cpu_ratio'],complete_mathlib_accept=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
