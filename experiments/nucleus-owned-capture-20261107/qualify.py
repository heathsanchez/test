import argparse,concurrent.futures,hashlib,json,os,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('mode',choices=['six','normal','mathlib']);a=p.parse_args()
flags=json.load(open('flags.json'));out=pathlib.Path('reports');out.mkdir(exist_ok=True)
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def census(path,label,timeout):
 start=time.monotonic()
 with open(path,'rb')as inp,open(out/(label+'.stderr'),'wb')as err:
  try:r=subprocess.run(['candidate/nucleus-census','--source-assumptions-only','262144','64',('512' if a.mode=='mathlib' else '256')],stdin=inp,stdout=subprocess.PIPE,stderr=err,env={**os.environ,**flags},timeout=timeout)
  except subprocess.TimeoutExpired:
   row={'diagnostic_only':True,'whole_export_warrant':'FORBIDDEN','finished_all_declarations':False,'stop_reason':'process-timeout','failures':[]}
   for line in (out/(label+'.stderr')).read_text(errors='replace').splitlines():
    if line.startswith('NUCLEUS_CENSUS_OBSERVATION:'):row['failures'].append(json.loads(line.split(':',1)[1]))
   r=None
  else:
   assert r.returncode==2,(label,r.returncode)
   row=json.loads(r.stdout);assert row['diagnostic_only']is True and row['whole_export_warrant']=='FORBIDDEN',row
   assert row['visited_declarations']<=row['total_declarations'];assert isinstance(row['finished_all_declarations'],bool)
  row.update(input_sha256=digest(path),elapsed_seconds=time.monotonic()-start,process_exit=r.returncode if r else 124)
 (out/(label+'.json')).write_text(json.dumps(row,indent=2))
 return {'case':label,'failures':[(x['name'],x['stage'],x['reason'])for x in row['failures']],'visited':row.get('visited_declarations'),'total':row.get('total_declarations'),'finished':row['finished_all_declarations'],'stop':row['stop_reason'],'process_exit':row['process_exit']}
if a.mode=='six':
 expected={'magma-list-pair-n7':'abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35','magma-list-pair-n21':'b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84','magma-list-deep-n21':'b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526','magma-list-deep-n36':'6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac','fueled-chain':'e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a','grind-ring-5':'e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f'}
 for name,sha in expected.items():assert digest('original196/good/perf/'+name+'.ndjson')==sha
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  rows=list(pool.map(lambda name:census('original196/good/perf/'+name+'.ndjson',name,600),expected))
 (out/'census-summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows));assert all(r['finished']for r in rows)
elif a.mode=='normal':
 old=[json.loads(x)for x in open('base/reports/verdicts.jsonl')if json.loads(x)['steps']==262144];assert len(old)==403
 def run(row):
  path=pathlib.Path(row['corpus'])/row['case'];assert digest(path)==row['input_sha256']
  with open(path,'rb')as f:
   try:rc=subprocess.run(['candidate/metatron-kernel'],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={**os.environ,**flags},timeout=200).returncode
   except subprocess.TimeoutExpired:rc=124
  return {'case':str(path),'old':row['rc'],'new':rc,'expected':row['expected'],'input_sha256':row['input_sha256']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,old))
 (out/'authoritative-parity.json').write_text(json.dumps(rows,indent=2));changed=[r for r in rows if r['old']!=r['new']];wrong=[r for r in rows if r['new'] not in (r['old'],r['expected']) or (r['old']!=2 and r['new']!=r['old'])];print('rows',len(rows),'changed',changed,'wrong_or_regressed',wrong);assert not wrong
else:print(json.dumps(census('mathlib-full.ndjson','mathlib-census',1200)))
