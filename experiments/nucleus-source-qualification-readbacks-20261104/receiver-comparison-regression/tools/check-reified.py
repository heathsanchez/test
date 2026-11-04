from pathlib import Path
import json,hashlib,subprocess,os,time
R=Path(__file__).resolve().parent;K=Path('/tmp/nucleus-frontier-investigation/reference/kernel');assert hashlib.sha256(K.read_bytes()).hexdigest()=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94';config=json.loads(Path('/tmp/nucleus-universe-full-pair/B/qualification.json').read_text())['candidate']['configuration'];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config|dict(NUCLEUS_TRACE_DOWNSTREAM='1');results=[]
for D in sorted((R/'reified').glob('pair-*')):
 if not(D/'goal.ndjson').exists():continue
 I=D/'goal.ndjson';row=dict(input_sha256=hashlib.sha256(I.read_bytes()).hexdigest(),rows=[],complete_mathlib_accept=False,no_rank_claim=True,signature_environment_only=True)
 arms=[('reference-parse',[str(K),'--parse-only',str(I)],None),('reference',[str(K),str(I)],None),('qualified-alpha',['/tmp/nucleus-universe-full-pair/B/candidate/nucleus'],I),('nested-normalized',['/tmp/nucleus-nested-projection-normalized/nucleus'],I)]
 for arm,args,stdin in arms:
  start=time.monotonic()
  with(D/(arm+'.stdout')).open('wb')as o,(D/(arm+'.stderr')).open('wb')as e:
   if stdin:
    with stdin.open('rb')as f:r=subprocess.run(args,stdin=f,stdout=o,stderr=e,env=env,timeout=600)
   else:r=subprocess.run(args,stdout=o,stderr=e,timeout=600)
  result=dict(arm=arm,rc=r.returncode,wall=time.monotonic()-start,binary_sha256=hashlib.sha256(Path(args[0]).read_bytes()).hexdigest(),terminal=(D/(arm+'.stderr')).read_text()[-1800:]);row['rows'].append(result);(D/'verification.json').write_text(json.dumps(row,indent=2));print(json.dumps(result),flush=True)
  if arm in('reference-parse','reference')and r.returncode!=0:break
 results.append(row)
(R/'reified-verification.json').write_text(json.dumps(results,indent=2))
