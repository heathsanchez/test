import gzip,hashlib,json,os,pathlib,subprocess,time,zipfile
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pins=[('parent.zip','39195a945244d6975feaff4f36cb9d26ae22373eb3d763ef567a048117d08baa','parent'),('candidate.zip','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f','candidate'),('prefix.zip','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879','prefix')]
for path,digest,destination in pins:
 assert sha(path)==digest
 with zipfile.ZipFile(path)as z:
  assert z.testzip()is None
  z.extractall(destination)
flags=json.load(open('candidate/flags.json'));assert flags==json.load(open('parent/flags.json'))
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env['NUCLEUS_TRACE_DOWNSTREAM']='1'
n=0
with gzip.open('prefix/reports/mathlib-through-LinearMap.ndjson.gz','rb')as src,open('accepted-prefix.ndjson','wb')as dst:
 for line in src:
  dst.write(line)
  if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
   n+=1
   if n==4679:break
assert n==4679 and sha('accepted-prefix.ndjson')=='cb1a3bee5ec54f9aa1af069a7ea804a566d627180e92e12e6237f4ad7f37c0e2'
rows=[]
for tag,expected_binary in [('parent','6a867284fd376e8380bf794b449804ca2983bbd3f902b1909523d6d91cefa339'),('candidate','d3e024777287f950d87bb20ba8bd02754b49a2660b52f88b96603fd89eb7883c')]:
 binary=pathlib.Path(tag)/'candidate/metatron-kernel';binary.chmod(0o755);assert sha(binary)==expected_binary;start=time.monotonic()
 with open('accepted-prefix.ndjson','rb')as inp,open(out/(tag+'.stderr'),'wb')as err:
  try:rc=subprocess.run([str(binary)],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=env,timeout=300).returncode
  except subprocess.TimeoutExpired:rc=124
 row={'tag':tag,'rc':rc,'binary_sha256':sha(binary),'seconds':time.monotonic()-start};rows.append(row);print(json.dumps(row),flush=True)
receipt={'schema':'nucleus.original-prefix.v1','profile':'release','configured_judgment_steps':262144,'declarations':n,'input_sha256':sha('accepted-prefix.ndjson'),'input_bytes':pathlib.Path('accepted-prefix.ndjson').stat().st_size,'flags':flags,'rows':rows}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));assert [x['rc']for x in rows]==[2,0]
