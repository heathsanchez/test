import hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT/'generate.py')],check=True)
out=pathlib.Path('/tmp/enum-fixtures');out.mkdir(parents=True,exist_ok=True)
for p in(ROOT/'fixtures').glob('*.ndjson'):shutil.copy2(p,out/p.name)
subprocess.run(['zstd','-dq','-f',str(ROOT/'ordering-prefix.ndjson.zst'),'-o',str(out/'original.ndjson')],check=True)
assert hashlib.sha256((out/'original.ndjson').read_bytes()).hexdigest()=='e0034bd4cb29aa1f260a40ced49d03bf4e748a191335bedfd23fce60afa85a48'
rows=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),expected=0 if p.stem in {'enum3','enum16','enum17','original'}else 1,native_expected=2 if p.stem=='enum17'else(0 if p.stem in {'enum3','enum16','original'}else 1),reference=p.stem not in {'deep-rule-annotation','dag-rule-annotation'})for p in sorted(out.glob('*.ndjson'))]
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
