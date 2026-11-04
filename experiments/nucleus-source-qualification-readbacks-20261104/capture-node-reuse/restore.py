from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.artifact.read_bytes())=='a63110abcccf930aa74d18a9dbe895a1d2b00b7d078232e2a90fa882806b7c48'
a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.artifact)as z:
 raw=z.read('candidate/source.tar.gz');assert sha(raw)=='1b25f9ea47c1d6f430228a473a547490d2c3fa1cf70867c4f0c02c697ce10e23'
 with tarfile.open(fileobj=io.BytesIO(raw))as t:t.extractall(a.out,filter='data')
 before=json.loads(z.read('candidate/source-manifest.json'))
k=a.out/'metatron-kernel';actual=lambda:{str(p.relative_to(k)):sha(p.read_bytes())for p in k.rglob('*')if p.is_file()};assert actual()==before
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(root/'reviewed.patch')],cwd=k,check=True)
expected=json.loads((root/'reviewed-source-manifest.json').read_text());assert actual()==expected
print(json.dumps(dict(status='VERIFIED_EXACT_SOURCE_RESTORATION',files=len(expected),patch_sha256=sha((root/'reviewed.patch').read_bytes()),source_qualified=False,no_binary_qualification_transfer=True)))
