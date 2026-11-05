from pathlib import Path
import hashlib,json,os,subprocess,zipfile
R=Path(__file__).resolve().parent;D=R/'frozen208';D.mkdir(exist_ok=True);config=json.loads(Path('/tmp/substitution-certificate-readback/verified/qualification.json').read_text())['candidate']['configuration'];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config
manifest=json.loads(Path('/tmp/current208/inputs-manifest.json').read_text())
with zipfile.ZipFile('/tmp/substitution-certificate-qualified.zip')as z:old={r['case']:r for r in json.loads(z.read('candidate/verdicts.json'))}
rows=[]
for row in manifest:
 p=Path('/tmp/current208/inputs')/row['relative_path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];folder=D/row['relative_path'].removesuffix('.ndjson');folder.mkdir(parents=True,exist_ok=True)
 with p.open('rb')as i,(folder/'stdout').open('wb')as o,(folder/'stderr').open('wb')as e:r=subprocess.run([str(R/'nucleus')],stdin=i,stdout=o,stderr=e,env=env,timeout=180)
 x=dict(case=row['case'],expected=row['expected'],sha256=row['sha256'],rc=r.returncode,parent_rc=old[row['case']]['rc']);rows.append(x)
 result=dict(status='COMPLETE'if len(rows)==208 else'RUNNING',candidate_qualified=False,promoted=False,no_speed_claim=True,rows=rows,changes=[r for r in rows if r['rc']!=r['parent_rc']],wrong=[r for r in rows if r['rc']not in(0,1,2)or(r['expected']==0 and r['rc']==1)or(r['expected']==1 and r['rc']==0)])
 (R/'frozen208.json').write_text(json.dumps(result,indent=2));assert not result['wrong'],x
print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
