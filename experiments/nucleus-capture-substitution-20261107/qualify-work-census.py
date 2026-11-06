import gzip,hashlib,json,os,pathlib,subprocess,time,tarfile,zipfile
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha('original196.zip')=='f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2'
with zipfile.ZipFile('original196.zip')as z:
 pathlib.Path('original196.tar.gz').write_bytes(z.read('lean-arena-tests.tar.gz'))
with tarfile.open('original196.tar.gz')as t:t.extractall('original196',filter='data')
assert sha('prefix.zip')=='f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879'
with zipfile.ZipFile('prefix.zip')as z:
 pathlib.Path('mathlib-prefix.gz').write_bytes(z.read('reports/mathlib-through-LinearMap.ndjson.gz'))
with gzip.open('mathlib-prefix.gz','rb')as f:pathlib.Path('mathlib-prefix.ndjson').write_bytes(f.read())
assert sha('mathlib-prefix.ndjson')=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
data=pathlib.Path('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True)
pathlib.Path('chain9-prefix.ndjson').write_bytes(b''.join(data[:11792]));pathlib.Path('chain6-prefix.ndjson').write_bytes(b''.join(data[:8250]))
assert sha('chain9-prefix.ndjson')=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'
assert sha('chain6-prefix.ndjson')=='16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'
flags=json.load(open('base/flags.json'));env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags)
binary=pathlib.Path('metatron-kernel/target/inquiry/nucleus-census');normal=pathlib.Path('metatron-kernel/target/inquiry/metatron-kernel')
summary=[]
for name,source,index in [('chain9','chain9-prefix.ndjson',140),('semiring','mathlib-prefix.ndjson',4679)]:
 reports=[]
 for enabled in [False,True]:
  label=name+('-on'if enabled else'-off');local=env.copy()
  if enabled:local['NUCLEUS_DIAGNOSTIC_WORK_CENSUS']='1'
  start=time.monotonic()
  with open(source,'rb')as inp,open(out/(label+'.stdout'),'wb')as output,open(out/(label+'.stderr'),'wb')as err:
   p=subprocess.run([str(binary),'--source-assumptions-only','262144','64','1',str(index)],stdin=inp,stdout=output,stderr=err,env=local,timeout=300)
  assert p.returncode==2,(label,p.returncode)
  report=json.load(open(out/(label+'.stdout')));assert report['whole_export_warrant']=='FORBIDDEN'and report['diagnostic_only'];reports.append(report)
  meters=[json.loads(x.split(':',1)[1])for x in(out/(label+'.stderr')).read_text().splitlines()if x.startswith('NUCLEUS_INFERENCE_WORK_CENSUS:')]
  if enabled:assert meters and all(x['acceptance_authority']is False for x in meters)
  row={'label':label,'seconds':time.monotonic()-start,'source_sha256':sha(source),'rc':p.returncode,'failures':report['failures'],'meters':meters}
  summary.append(row);print(json.dumps(row),flush=True)
 assert reports[0]==reports[1],name+' observer changed a census outcome'
for enabled in [False,True]:
 local=env.copy()
 if enabled:local['NUCLEUS_DIAGNOSTIC_WORK_CENSUS']='1'
 label='chain6-native-'+str(enabled)
 with open('chain6-prefix.ndjson','rb')as inp,open(out/(label+'.stderr'),'wb')as err:
  p=subprocess.run([str(normal)],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=local,timeout=240)
 assert p.returncode==0,(label,p.returncode)
(out/'summary.json').write_text(json.dumps({'scope':'DIAGNOSTIC_ONLY; conditional source assumptions; no kernel repair','flags':flags,'census_binary_sha256':sha(binary),'normal_binary_sha256':sha(normal),'observations':summary,'chain6_native_on_off':'ACCEPT/ACCEPT'},indent=2))
