#!/usr/bin/env python3
"""Retain original record order through one exact declaration; never admit future declarations."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('out');a=p.parse_args()
source=Path(a.source);out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
list_ids=set();perm_ids=set();target_ids=set();found=None
with source.open('rb') as src,out.open('wb') as dst:
 for line_no,line in enumerate(src,1):
  dst.write(line)
  r=json.loads(line)
  if 'in' in r and 'str' in r:
   n=r['str'];name=n.get('str');pre=n.get('pre')
   if name=='List' and pre==0:list_ids.add(r['in'])
   if name=='Perm' and pre in list_ids:perm_ids.add(r['in'])
   if name=="recOnSwap'" and pre in perm_ids:target_ids.add(r['in'])
  for tag in ['thm','def','opaque']:
   if tag in r and r[tag].get('name') in target_ids:
    found=dict(tag=tag,name_id=r[tag]['name'],record=line_no,type=r[tag]['type'],value=r[tag]['value']);break
  if found:break
if found is None:out.unlink();raise RuntimeError('exact target declaration absent')
metadata=dict(target="List.Perm.recOnSwap'",source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),prefix_sha256=hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),bytes=out.stat().st_size,**found)
out.with_suffix('.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata),flush=True)
