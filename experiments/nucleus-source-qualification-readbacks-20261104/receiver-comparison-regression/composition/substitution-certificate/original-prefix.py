from pathlib import Path
import os,json,subprocess,hashlib,time
R=Path(__file__).resolve().parent;binary=R/'nucleus';config=json.loads((R/'report.json').read_text())['configuration'];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config;rows=[]
for name,path,pin in [('original','/tmp/nucleus-frontier-investigation/original.ndjson','ca6ba58a99ca074dc45d975ab982fd119193fa05a6d12e20f08c53cb7dd786f2'),('signature','/tmp/nucleus-receiver-trials/goal/signature-diagnostic.ndjson','1022e5dc308231b91a2d8833a26006d1d082339785d61a09fc7427b30d8c0bdf')]:
 p=Path(path);assert hashlib.sha256(p.read_bytes()).hexdigest()==pin;D=R/name;D.mkdir(exist_ok=True);start=time.monotonic()
 with p.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:r=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=900)
 row=dict(input=name,input_sha256=pin,rc=r.returncode,wall=time.monotonic()-start,stdout_tail=(D/'stdout').read_text()[-2000:],stderr_tail=(D/'stderr').read_text()[-2000:]);rows.append(row);(R/'original-prefix-report.json').write_text(json.dumps(dict(status='COMPLETE'if len(rows)==2 else'RUNNING',binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),configuration=config,rows=rows,no_promotion=True,no_speed_claim=True,complete_mathlib_accept=False,no_rank_claim=True),indent=2));print(json.dumps(row),flush=True)
