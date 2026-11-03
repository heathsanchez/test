import hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT/'generate.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'controls.py')],check=True)
out=pathlib.Path('/tmp/record-fixtures');out.mkdir(parents=True,exist_ok=True)
for p in list((ROOT/'fixtures').glob('*.ndjson'))+list((ROOT/'controls').glob('*.ndjson')):shutil.copy2(p,out/p.name)
subprocess.run(['zstd','-dq','-f',str(ROOT/'source-prefix.ndjson.zst'),'-o',str(out/'original.ndjson')],check=True)
assert hashlib.sha256((out/'original.ndjson').read_bytes()).hexdigest()=='2833a44b446524b25c8053006a3684d0fdab5779d76ef17695cbd4763ec9a0cd'
rows=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),expected=0 if p.stem in {'two','dependent','boundary','original'}else 1)for p in sorted(out.glob('*.ndjson'))]
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
