import os,json,subprocess,shutil,hashlib,re
from pathlib import Path
out=Path('/tmp/range-closed-reference');source=Path('/tmp/arena-reference/checkers/official/.lake/build/bin/kernel');bundle=out/'bundle';lib=bundle/'lib';lib.mkdir(parents=True,exist_ok=True);shutil.copy2(source,bundle/'kernel')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ldd=subprocess.run(['ldd',str(source)],capture_output=True,text=True);assert ldd.returncode==0;(out/'ldd.txt').write_text(ldd.stdout);assert 'not found'not in ldd.stdout
for path in re.findall(r'=> (/\S+)',ldd.stdout):
 p=Path(path)
 if not any(p.name.startswith(x)for x in ['libc.so','libm.so','libpthread.so','libdl.so','librt.so']):
  target=lib/p.name
  if target.exists():assert sha(target)==sha(p)
  else:shutil.copy2(p,target)
env=dict(os.environ,LD_LIBRARY_PATH=str(lib));rows=[]
for case in json.loads((out/'inputs/inputs.json').read_text()):
 p=out/'inputs'/case['file'];assert sha(p)==case['sha256']
 for mode,args,expected in [('parse',['--parse-only',str(p)],0),('kernel',[str(p)],case['expected_rc'])]:
  r=subprocess.run([str(bundle/'kernel'),*args],capture_output=True,env=env,timeout=180);(out/(case['case']+'-'+mode+'.stdout')).write_bytes(r.stdout);(out/(case['case']+'-'+mode+'.stderr')).write_bytes(r.stderr)
  row=dict(case=case['case'],mode=mode,rc=r.returncode,expected=expected,input_sha=sha(p));rows.append(row);print(json.dumps(row),flush=True)
  (out/'results.json').write_text(json.dumps(dict(rows=rows,reference_source='cd2dd0244b9ed5e704463a26fbbe5fc67ba16108',lean='4.34.1',binary_sha=sha(bundle/'kernel'),dependencies=[dict(file=p.name,sha256=sha(p))for p in lib.iterdir()]),indent=2)+'\n');assert r.returncode==expected,row
(bundle/'run').write_text('#!/bin/sh\nset -eu\nbundle_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexport LD_LIBRARY_PATH="$bundle_root/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\nexec "$bundle_root/kernel" "$@"\n');(bundle/'run').chmod(0o755)
r=subprocess.run([str(bundle/'run'),str(out/'inputs/constraint.ndjson')],capture_output=True,timeout=180);assert r.returncode==0
(out/'bundle-validated.json').write_text(json.dumps(dict(binary_sha=sha(bundle/'kernel'),relocatable_bundle_validated=True,source_pin='cd2dd0244b9ed5e704463a26fbbe5fc67ba16108',lean='4.34.1'),indent=2)+'\n')
