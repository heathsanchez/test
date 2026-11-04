from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,zipfile
p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--arm',required=True);a=p.parse_args();R=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();rows=json.loads((R/'source-digests.json').read_text());assert a.arm in rows
assert sha(a.artifact.read_bytes())=='a63110abcccf930aa74d18a9dbe895a1d2b00b7d078232e2a90fa882806b7c48';a.out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.artifact)as z:
 raw=z.read('candidate/source.tar.gz');assert sha(raw)=='1b25f9ea47c1d6f430228a473a547490d2c3fa1cf70867c4f0c02c697ce10e23'
 with tarfile.open(fileobj=io.BytesIO(raw))as t:t.extractall(a.out,filter='data')
 expected=json.loads(z.read('candidate/source-manifest.json'))
k=a.out/'metatron-kernel';actual=lambda:{str(p.relative_to(k)):sha(p.read_bytes())for p in k.rglob('*')if p.is_file()};assert actual()==expected
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/(a.arm+'.patch'))],cwd=k,check=True)
expected.update(rows[a.arm]['changed_files']);assert actual()==expected;assert len(expected)==rows[a.arm]['file_count']
print(json.dumps(dict(status='VERIFIED_EXACT_DIAGNOSTIC_RESTORATION',arm=a.arm,files=len(expected),diagnostic_only=True,no_source_or_binary_qualification_transfer=True)))
