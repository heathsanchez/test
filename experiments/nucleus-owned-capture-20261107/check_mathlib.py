import json,gzip,os,subprocess,pathlib
r=json.load(open('reports/mathlib-census.json'));assert r['visited_declarations']>4852,r
subprocess.run(['python','experiments/nucleus-structural-inquiry-20261107/extract_prefix.py'],check=True)
subprocess.run(['python','experiments/nucleus-owned-capture-20261107/protect_prefix.py'],check=True)
flags=json.load(open('flags.json'));env={**os.environ,**flags,'NUCLEUS_TRACE_DOWNSTREAM':'1'}
with open('protected-prefix.ndjson','rb')as inp,open('reports/protected-prefix.stderr','wb')as err:
 r=subprocess.run(['candidate/metatron-kernel'],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env=env,timeout=300)
assert r.returncode==0,r.returncode
print('PROTECTED_PREVIOUS_MATHLIB_PREFIX_ACCEPT',flush=True)
with gzip.open('reports/mathlib-through-LinearMap.ndjson.gz','rb')as src,open('prefix.ndjson','wb')as dst:
 import shutil;shutil.copyfileobj(src,dst)
with open('prefix.ndjson','rb')as inp,open('reports/focused-candidate.json','wb')as out,open('reports/focused-candidate.stderr','wb')as err:
 r=subprocess.run(['candidate/nucleus-census','--source-assumptions-only','262144','64','256','4851'],stdin=inp,stdout=out,stderr=err,env={**env,'NUCLEUS_DIAGNOSTIC_SIGNATURE_IDS':'30446,30461,30464'},timeout=180)
assert r.returncode==2,r.returncode
r=json.load(open('reports/focused-candidate.json'));assert r['finished_all_declarations']is True and r['whole_export_warrant']=='FORBIDDEN';assert r['assumed_prefix_checks']>0
print('LINEARMAP_FORMS_CONDITIONALLY_WITH_EXPLICIT_SOURCE_ASSUMPTIONS',flush=True)
