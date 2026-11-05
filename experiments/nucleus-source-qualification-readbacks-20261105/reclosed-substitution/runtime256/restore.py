from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--metadata',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();m=json.loads(a.metadata.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.parent.read_bytes())==m['parent_artifact_sha256'];assert sha(a.component.read_bytes())==m['component_sha256'];assert sha(a.manifest.read_bytes())==m['source_manifest_sha256'];manifest=json.loads(a.manifest.read_text())
with zipfile.ZipFile(a.parent)as z:
 data=z.read('candidate/source.tar.gz');assert sha(data)==m['parent_source_tar_sha256'];a.out.mkdir(exist_ok=False)
 with tarfile.open(fileobj=io.BytesIO(data))as t:t.extractall(a.out,filter='data')
S=a.out/'metatron-kernel';r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(a.component.resolve())],cwd=S,capture_output=True);(a.out/'patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
actual={str(p.relative_to(S)):sha(p.read_bytes())for p in S.rglob('*')if p.is_file()};assert actual==manifest and len(actual)==m['source_files']==368
receipt=dict(status='VERIFIED_SOURCE_RECONSTRUCTION_ONLY',source_files=368,exact_file_sets=True,parent_artifact_sha256=m['parent_artifact_sha256'],component_sha256=m['component_sha256'],source_manifest_sha256=m['source_manifest_sha256'],source_qualified=False,promoted=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
