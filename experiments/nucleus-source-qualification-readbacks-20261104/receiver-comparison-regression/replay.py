from pathlib import Path
import argparse,hashlib,json,lzma,os,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--checker',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();R=Path(__file__).resolve().parent;m=json.loads((R/'fixture.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest();packed=(R/'valid-data-congruence.ndjson.xz').read_bytes();assert sha(packed)==m['compressed_sha256'];raw=lzma.decompress(packed);assert sha(raw)==m['input_sha256']and len(raw)==m['input_bytes'];a.out.mkdir(parents=True,exist_ok=False);I=a.out/'goal.ndjson';I.write_bytes(raw)
rows=[];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|m['configuration'];arms=[]
if a.reference:
 assert sha(a.reference.read_bytes())==m['pinned_reference_binary_sha256'];arms+=[('reference-parse',[str(a.reference.resolve()),'--parse-only',str(I.resolve())],False),('reference',[str(a.reference.resolve()),str(I.resolve())],False)]
arms+=[('checker',[str(a.checker.resolve())],True)]
for label,args,stdin in arms:
 start=time.monotonic()
 with(a.out/(label+'.stdout')).open('wb')as o,(a.out/(label+'.stderr')).open('wb')as e:
  if stdin:
   with I.open('rb')as f:r=subprocess.run(args,stdin=f,stdout=o,stderr=e,env=env,timeout=900)
  else:r=subprocess.run(args,stdout=o,stderr=e,timeout=900)
 rows.append(dict(arm=label,rc=r.returncode,binary_sha256=sha(Path(args[0]).read_bytes()),wall=time.monotonic()-start));report=dict(status=('RUNNING'if len(rows)<len(arms)else('PASS'if all(x['rc']==0 for x in rows)else'FAIL')),input_sha256=m['input_sha256'],rows=rows,reference_status='RUN'if a.reference else'NOT_RUN',source_qualification='NOT_EVALUATED',complete_mathlib_accept=False,no_rank_claim=True,no_speed_claim=True);(a.out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows[-1]),flush=True)
raise SystemExit(0 if all(x['rc']==0 for x in rows)else 1)
