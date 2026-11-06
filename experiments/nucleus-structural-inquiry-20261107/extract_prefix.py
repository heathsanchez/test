"""Retain exact original source bytes through one declaration boundary."""
import gzip,hashlib,json,pathlib
n=0;h=hashlib.sha256();names={0:''};rawblock=None
with open('mathlib-full.ndjson','rb')as f,gzip.open('reports/mathlib-through-LinearMap.ndjson.gz','wb')as out:
 for lineno,line in enumerate(f,1):
  r=json.loads(line);out.write(line);h.update(line)
  if 'in'in r:
   k=r['in']
   if 'str'in r:names[k]=names[r['str']['pre']]+('.'if names[r['str']['pre']]else'')+r['str']['str']
   elif 'num'in r:names[k]=names[r['num']['pre']]+'.'+str(r['num']['i'])
  if set(r)&{'axiom','def','thm','opaque','quot','inductive'}:
   n+=1
   if n==4852:
    rawblock=r;break
assert n==4852 and 'inductive'in rawblock
owner=names[rawblock['inductive']['types'][0]['name']];assert owner=='LinearMap',owner
pathlib.Path('reports/LinearMap-source-block.json').write_text(json.dumps(rawblock,indent=2))
pathlib.Path('reports/prefix-manifest.json').write_text(json.dumps({'source_full_sha256':'22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6','prefix_sha256':h.hexdigest(),'source_lines':lineno,'declarations':n,'last_owner':owner,'scope':'EXACT_SOURCE_PREFIX_NOT_FULL_EXPORT'},indent=2))
print(owner,n,lineno,h.hexdigest())
