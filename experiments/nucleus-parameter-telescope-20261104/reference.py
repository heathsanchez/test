#!/usr/bin/env python3
"""Independent pinned Lean kernel replay; parse errors are not refutations."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--checker',required=True);p.add_argument('--fixtures',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(a.fixtures);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
report=dict(checker_sha=hashlib.sha256(Path(a.checker).read_bytes()).hexdigest(),reference_commit='cd2dd0244b9ed5e704463a26fbbe5fc67ba16108',rows=[])
for row in json.loads((root/'manifest.json').read_text()):
 if row['file'] in {'excessive-depth.ndjson','expanded-dag.ndjson'}:continue
 source=root/row['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
 entry=dict(row)
 for label,args in [('parse',['--parse-only']),('kernel',[])]:
  r=subprocess.run([a.checker,*args,str(source)],capture_output=True,timeout=240);entry[label]=dict(rc=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'));(out/(row['file']+'.'+label+'.stdout')).write_bytes(r.stdout);(out/(row['file']+'.'+label+'.stderr')).write_bytes(r.stderr)
 report['rows'].append(entry);(out/'reference.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)

assert all(e['parse']['rc']==0 and e['kernel']['rc']==e['expected'] for e in report['rows']), report
