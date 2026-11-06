import concurrent.futures,gzip,hashlib,json,os,pathlib,subprocess,tarfile,time,zipfile
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def unpack(path,expected,dest):
 assert sha(path)==expected
 with zipfile.ZipFile(path)as z:
  assert z.testzip()is None;z.extractall(dest)
unpack('original196.zip','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2','original-archive')
with tarfile.open('original-archive/lean-arena-tests.tar.gz')as t:t.extractall('original196',filter='data')
unpack('prefix.zip','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879','prefix')
with gzip.open('prefix/reports/mathlib-through-LinearMap.ndjson.gz','rb')as f:pathlib.Path('mathlib-prefix.ndjson').write_bytes(f.read())
assert sha('mathlib-prefix.ndjson')=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
flags=json.load(open('base/flags.json'));env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env['NUCLEUS_TRACE_DOWNSTREAM']='1';env['NUCLEUS_TRACE_ALIAS_RESULT_REUSE']='1'
binary='candidate/metatron-kernel'
def run(name,path,timeout=300):
 start=time.monotonic()
 with open(path,'rb')as inp,open(out/(name+'.stderr'),'wb')as err:
  try:rc=subprocess.run([binary],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=env,timeout=timeout).returncode
  except subprocess.TimeoutExpired:rc=124
 first=next((x for x in(out/(name+'.stderr')).read_text().splitlines()if x.startswith('NUCLEUS_DOWNSTREAM:')),None)
 row={'name':name,'input_sha256':sha(path),'rc':rc,'seconds':time.monotonic()-start,'first_failure':first,'alias_result_reuse':[json.loads(line.split(':',1)[1])for line in(out/(name+'.stderr')).read_text().splitlines()if line.startswith('NUCLEUS_ALIAS_RESULT_REUSE:')]};print(json.dumps(row),flush=True);return row
names=['magma-list-pair-n7','magma-list-pair-n21','magma-list-deep-n21','magma-list-deep-n36','fueled-chain','grind-ring-5']
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(lambda name:run(name,'original196/good/perf/'+name+'.ndjson',240),names))
assert all(r['rc']in(0,2)for r in rows),rows
data=pathlib.Path('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True)
pathlib.Path('chain6.ndjson').write_bytes(b''.join(data[:8250]));pathlib.Path('chain9.ndjson').write_bytes(b''.join(data[:11792]))
assert sha('chain6.ndjson')=='16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'
assert sha('chain9.ndjson')=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'
a=run('chain6-protected','chain6.ndjson');b=run('chain9-new','chain9.ndjson');assert a['rc']==0;assert b['rc']in(0,2)
n=0
with open('mathlib-prefix.ndjson','rb')as inp,open('mathlib-4679.ndjson','wb')as dst:
 for line in inp:
  dst.write(line)
  if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
   n+=1
   if n==4679:break
assert sha('mathlib-4679.ndjson')=='cb1a3bee5ec54f9aa1af069a7ea804a566d627180e92e12e6237f4ad7f37c0e2'
c=run('mathlib-4679-protected','mathlib-4679.ndjson');assert c['rc']==0
d=run('mathlib-new-frontier','mathlib-prefix.ndjson');assert d['rc']in(0,2)
gain=any(x['rc']==0 for x in rows)or b['rc']==0 or d['rc']==0 or(d['first_failure']is not None and'name=AddMonoidAlgebra.semiring:'not in d['first_failure'])
receipt={'status':'CANDIDATE','binary_sha256':sha(binary),'profile':'release','judgment_steps':262144,'flags':flags,'rows':rows+[a,b,c,d],'new_native_reach':gain}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
if gain:
 with open('arena207.zip','wb')as f:subprocess.run(['gh','api','repos/heathsanchez/test/actions/artifacts/13276400289/zip'],stdout=f,check=True)
 unpack('arena207.zip','a9582eadc0d9893cbe39e6bcfccd79bfaec2032838851b8a487c35df16096763','arena-archive')
 with tarfile.open('arena-archive/lean-arena-tests.tar.gz')as t:t.extractall('arena207',filter='data')
 baseline=json.load(open('base/reports/ordinary-403.json'));assert len(baseline)==403
 def compare(row):
  assert sha(row['case'])==row['input_sha256']
  r=run('parity-'+row['case'].replace('/','_'),row['case'],240)
  return {**r,'parent':row['new'],'expected':row['expected']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:allrows=list(pool.map(compare,baseline))
 (out/'ordinary-403.json').write_text(json.dumps(allrows,indent=2))
 assert all(r['rc']==r['parent']or(r['parent']==2 and r['rc']==r['expected'])for r in allrows)
 receipt['protected_403']='PASS';receipt['status']='WARRANTED_BOUNDED';(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
else:
 receipt['status']='REJECTED_AS_SUFFICIENT';(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
