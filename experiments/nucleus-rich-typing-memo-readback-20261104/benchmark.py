from pathlib import Path
import json,os,subprocess,resource,time,hashlib,statistics
R=Path(__file__).resolve().parent
parent=R.parent/'receipts/quotient-result-projection/candidate/nucleus';candidate=R/'target/release/metatron-kernel'
q=json.loads((R.parent/'receipts/quotient-result-projection/qualification.json').read_text())['candidate'];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(q['configuration'])
input=R/'hot/next-frontier.ndjson';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(input)=='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1';assert sha(parent)==q['binary_sha'];parent.chmod(0o755)
rows=[];out=R/'timing';out.mkdir(exist_ok=True)
for i,arm in enumerate(['candidate','parent','parent','candidate']):
 binary=candidate if arm=='candidate'else parent;before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
 with input.open('rb')as stream,(out/f'{i}-{arm}.stdout').open('wb')as stdout,(out/f'{i}-{arm}.stderr').open('wb')as stderr:r=subprocess.run([str(binary)],stdin=stream,stdout=stdout,stderr=stderr,env=env,timeout=900)
 after=resource.getrusage(resource.RUSAGE_CHILDREN);row=dict(arm=arm,rc=r.returncode,cpu=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),wall=time.monotonic()-start,binary_sha=sha(binary),input_sha=sha(input));rows.append(row);print(json.dumps(row),flush=True)
 report=dict(status='RUNNING',source_boundary='Original Mathlib prefix through AddMonoidAlgebra.instAddCommMonoid._proof_1',rows=rows);(out/'report.json').write_text(json.dumps(report,indent=2))
 if r.returncode!=0:raise SystemExit('EARLY_VERDICT_REGRESSION_OR_APPARATUS_FAILURE')
a=[r['cpu']for r in rows if r['arm']=='parent'];b=[r['cpu']for r in rows if r['arm']=='candidate'];report.update(status='COMPLETE',gate='all candidate CPU samples beat all parent CPU samples by more than 1 percent',speed_win=max(b)<min(a)*.99,median_cpu_ratio=statistics.median(b)/statistics.median(a),no_rank_claim=True);(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
