import concurrent.futures,hashlib,json,os,pathlib,subprocess,time,gzip
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
flags=json.load(open('flags.json'));env={**os.environ,**flags}
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
base=json.load(open('base/reports/authoritative-parity.json'));assert len(base)==403
binary='candidate/metatron-kernel'
def run(row):
 assert digest(row['case'])==row['input_sha256'];start=time.monotonic()
 with open(row['case'],'rb')as inp:
  try:rc=subprocess.run([binary],stdin=inp,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env,timeout=240).returncode
  except subprocess.TimeoutExpired:rc=124
 return {**row,'parent':row['new'],'new':rc,'seconds':time.monotonic()-start}
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,base))
(out/'ordinary-403.json').write_text(json.dumps(rows,indent=2));changes=[r for r in rows if r['new']!=r['parent']]
print('ORDINARY_CHANGED',json.dumps(changes),flush=True);assert not changes
n=0
with gzip.open('base-prefix/reports/mathlib-through-LinearMap.ndjson.gz','rb')as src,open('protected-prefix.ndjson','wb')as dst:
 for line in src:
  dst.write(line)
  if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
   n+=1
   if n==4662:break
sha=digest('protected-prefix.ndjson');assert sha=='4a6673e49c28ecd7986cf371de5c3c9c4fadd858a7c484b04ce8f0ddc963f629'
start=time.monotonic()
with open('protected-prefix.ndjson','rb')as inp,open(out/'protected-prefix.stderr','wb')as err:
 r=subprocess.run([binary],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=env,timeout=300)
receipt={'binary_sha256':digest(binary),'profile':'release','flags':flags,'ordinary_cases':len(rows),'changed_cases':len(changes),'protected_prefix_sha256':sha,'protected_prefix_declarations':n,'protected_prefix_rc':r.returncode,'protected_prefix_seconds':time.monotonic()-start}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True);assert r.returncode==0
