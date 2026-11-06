import gzip,json,hashlib,pathlib
n=0;h=hashlib.sha256()
with gzip.open('reports/mathlib-through-LinearMap.ndjson.gz','rb')as src,open('protected-prefix.ndjson','wb')as out:
 for line in src:
  r=json.loads(line);out.write(line);h.update(line)
  if set(r)&{'axiom','def','thm','opaque','quot','inductive'}:
   n+=1
   if n==4662:break
assert n==4662
pathlib.Path('reports/protected-prefix-manifest.json').write_text(json.dumps({'declarations':n,'sha256':h.hexdigest(),'full_source_sha256':'22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6','expected_ordinary_exit':0},indent=2))
