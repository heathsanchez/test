from pathlib import Path
import argparse,zipfile,tarfile,io,json,hashlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--normalized-component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();ROOT=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.parent.read_bytes())=='79a49583b5e9c4742c4280075b41cdd89ba44f2d96b402af8f90ef4750897e8d';assert sha(a.normalized_component.read_bytes())=='1e7da434d8732ed2b0957454fa97679fd7289600896b36e2ac54cc610c73a6bb';a.out.mkdir(exist_ok=False)
with zipfile.ZipFile(a.parent)as z:base=z.read('candidate/source.tar.gz');assert sha(base)=='4203d0e41e00b52ec8ff4acc7182407b6658b4b9d556c8056000228e208f2318'
rows=[]
for arm in ['generic-envelope','alpha','normalized','normalized-reserved']:
 local=ROOT/arm;D=a.out/arm
 with tarfile.open(fileobj=io.BytesIO(base))as t:t.extractall(D,filter='data')
 S=D/'metatron-kernel';patches=([a.normalized_component]if arm.startswith('normalized')else[])+[local/'counterfactual.patch']
 for patch in patches:
  r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch.resolve())],cwd=S,capture_output=True);assert r.returncode==0,(arm,(r.stdout+r.stderr).decode())
 expected=json.loads((local/'source-manifest.json').read_text());actual={str(p.relative_to(S)):sha(p.read_bytes())for p in S.rglob('*')if p.is_file()};assert len(actual)==368 and actual==expected,arm
 report=json.loads((local/'report.json').read_text());assert report['input_sha256']=='1022e5dc308231b91a2d8833a26006d1d082339785d61a09fc7427b30d8c0bdf';assert 'NUCLEUS_DOWNSTREAM:name=AddMonoidAlgebra.nonUnitalNonAssocSemiring._proof_1:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type' in report['observations'];assert report['rc']==2 and report['not_promotable'] and report['no_promotion'];rows.append(dict(arm=arm,files=368,exact_file_sets=True,counterfactual_patch_sha256=sha((local/'counterfactual.patch').read_bytes()),source_manifest_sha256=sha((local/'source-manifest.json').read_bytes()),binary_sha256=report['binary_sha256'],input_sha256=report['input_sha256'],rc=2,not_promotable=True,unchanged_first_unknown=True,additional_unpaid_construction=True))
receipt=dict(status='VERIFIED_COUNTERFACTUAL_SOURCES_UNCHANGED_FIRST_UNKNOWN',parent_commit='a1d6ba062615ddb209bb5e0c9644d456a5e79084',parent_artifact_id=13359400422,parent_artifact_sha256=sha(a.parent.read_bytes()),normalized_component_sha256=sha(a.normalized_component.read_bytes()),arms=rows,no_speed_claim=True,no_rank_claim=True,complete_mathlib_accept=False)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
