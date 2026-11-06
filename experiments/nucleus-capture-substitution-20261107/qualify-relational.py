import concurrent.futures,hashlib,json,os,pathlib,subprocess,time,gzip
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
flags=json.load(open('flags.json'));env={**os.environ,**flags}
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
base=json.load(open('base/reports/ordinary-403.json'));assert len(base)==403
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

# Exact unchanged source prefix through the formerly unresolved chain6 proof.
source=pathlib.Path('original196/good/perf/fueled-chain.ndjson')
prefix=pathlib.Path('chain6-prefix.ndjson');prefix.write_bytes(b''.join(source.read_bytes().splitlines(keepends=True)[:8250]))
assert digest(prefix)=='16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'
rows=[]
for executable in ['base/candidate/metatron-kernel',binary]:
 start=time.monotonic()
 with prefix.open('rb')as inp,open(out/('chain6-'+('parent'if executable.startswith('base/')else'candidate')+'.stderr'),'wb')as err:
  result=subprocess.run([executable],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=env,timeout=240)
 rows.append({'binary_sha256':digest(executable),'rc':result.returncode,'seconds':time.monotonic()-start})
(out/'chain6-prefix-receipt.json').write_text(json.dumps({'input_sha256':digest(prefix),'steps':262144,'flags':flags,'rows':rows},indent=2))
print('CHAIN6_EXACT_PREFIX',json.dumps(rows),flush=True);assert [r['rc']for r in rows]==[2,0]
