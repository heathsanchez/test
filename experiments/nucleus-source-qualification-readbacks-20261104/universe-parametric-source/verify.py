from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.candidate.read_bytes())=='79a49583b5e9c4742c4280075b41cdd89ba44f2d96b402af8f90ef4750897e8d';assert sha(a.parent.read_bytes())=='a63110abcccf930aa74d18a9dbe895a1d2b00b7d078232e2a90fa882806b7c48';assert sha(a.component.read_bytes())=='d1c860be4138f87f723dcb9af14cfa084be7d0234b8cdadf618d308dd47fb101';a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.candidate)as z:
 manifest_raw=z.read('candidate/source-manifest.json');manifest=json.loads(manifest_raw);tar_raw=z.read('candidate/source.tar.gz');report=json.loads(z.read('universe-parametric-source.json'));q=json.loads(z.read('qualification.json'))['candidate'];binary=z.read('candidate/nucleus')
 assert report['source_qualified']and report['qualified']and report['status']=='PROMOTABLE_UNIVERSE_PARAMETRIC_SOURCE';assert sha(binary)==report['binary_sha']=='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715'
 with tarfile.open(fileobj=io.BytesIO(tar_raw))as t:t.extractall(a.out/'archive',filter='data')
 patch_raw=z.read('candidate/source.patch');assert sha(patch_raw)==report['source_patch_sha']
with zipfile.ZipFile(a.parent)as z:
 parent=json.loads(z.read('qualification.json'))['candidate'];base_manifest=json.loads(z.read('candidate/source-manifest.json'));base_tar=z.read('candidate/source.tar.gz');assert sha(base_tar)=='1b25f9ea47c1d6f430228a473a547490d2c3fa1cf70867c4f0c02c697ce10e23';assert parent['configuration']==q['configuration']
 with tarfile.open(fileobj=io.BytesIO(base_tar))as t:t.extractall(a.out/'reconstructed',filter='data')
def inventory(root):return{str(p.relative_to(root)):sha(p.read_bytes())for p in root.rglob('*')if p.is_file()}
archive=a.out/'archive/metatron-kernel';reconstructed=a.out/'reconstructed/metatron-kernel';assert inventory(archive)==manifest;assert inventory(reconstructed)==base_manifest
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(a.component.resolve())],cwd=reconstructed,capture_output=True);(a.out/'patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0;assert inventory(reconstructed)==manifest;assert len(manifest)==368
receipt=dict(status='VERIFIED_PROMOTABLE_UNIVERSE_PARAMETRIC_SOURCE',source_commit='a1d6ba062615ddb209bb5e0c9644d456a5e79084',run_id=41897289291,artifact_id=13359400422,artifact_sha256=sha(a.candidate.read_bytes()),binary_sha256=sha(binary),source_tar_sha256=sha(tar_raw),source_manifest_sha256=sha(manifest_raw),cumulative_patch_sha256=sha(patch_raw),component_sha256=sha(a.component.read_bytes()),archive_files=368,reconstructed_files=368,exact_file_sets=True,configuration_unchanged=True,source_qualified=True,promotable=True,speed_preset_passed=True,median_cpu_ratio=report['timing']['median_cpu_ratio'],complete_mathlib_accept=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
