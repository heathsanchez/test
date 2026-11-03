import hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT/'generate.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'controls.py')],check=True)
out=pathlib.Path('/tmp/record-fixtures');out.mkdir(parents=True,exist_ok=True)
for p in list((ROOT/'fixtures').glob('*.ndjson'))+list((ROOT/'controls').glob('*.ndjson')):shutil.copy2(p,out/p.name)
subprocess.run(['zstd','-dq','-f',str(ROOT/'source-prefix.ndjson.zst'),'-o',str(out/'original.ndjson')],check=True)
assert hashlib.sha256((out/'original.ndjson').read_bytes()).hexdigest()=='2833a44b446524b25c8053006a3684d0fdab5779d76ef17695cbd4763ec9a0cd'
# Old source fixtures carried v as a noncanonical regenerated motive name.
# Preserve exact originals as negatives; alter only that Name record in positives.
for label in ['parameter-record','homogeneous-pair']:
 raw=(ROOT.parents[1]/('metatron-kernel/tests/fixtures/good-'+label+'.ndjson')).read_text()
 (out/('legacy-'+label+'.ndjson')).write_text(raw)
 records=[json.loads(line)for line in raw.splitlines()]
 changed=0
 for record in records:
  if record.get('str',{}).get('pre')==0 and record['str']['str']=='v':
   record['str']['str']='u_1';changed+=1
 assert changed==1
 (out/('canonical-'+label+'.ndjson')).write_text(''.join(json.dumps(r,separators=(',',':'))+'\n'for r in records))
rows=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),expected=0 if p.stem in {'two','dependent','boundary','original','owner-u1','owner-w','binder-name','binder-info','canonical-parameter-record','canonical-homogeneous-pair'}else 1)for p in sorted(out.glob('*.ndjson'))]
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
