#!/usr/bin/env python3
"""Retain unchanged source through any ordinary or bundled inductive declaration."""
import argparse,hashlib,json,subprocess
from pathlib import Path
INPUT_SHA='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'

def extract(source,out,target):
 parts=target.split('.');matched={0:0};found=None;names=0
 with Path(source).open('rb')as src,Path(out).open('wb')as dst:
  for line_number,line in enumerate(src,1):
   dst.write(line)
   # Every other expression/level record is copied verbatim without parsing.
   is_name=b'"in":'in line
   if not is_name and not any(tag in line for tag in [b'"thm":',b'"def":',b'"opaque":',b'"inductive":']):continue
   r=json.loads(line)
   if 'in'in r:
    names+=1;n=r.get('str')or r.get('num')
    if n:
     depth=matched.get(n.get('pre'));word=str(n.get('str',n.get('i')))
     if depth is not None and depth<len(parts)and word==parts[depth]:matched[r['in']]=depth+1
   for tag in ['thm','def','opaque']:
    if tag in r and matched.get(r[tag].get('name'))==len(parts):found=dict(target=target,tag=tag,record=line_number,declaration=r[tag]);break
   if 'inductive'in r:
    block=r['inductive']
    if any(matched.get(t.get('name'))==len(parts)for t in block.get('types',[])):
     found=dict(target=target,tag='inductive',record=line_number,declaration=block)
   if found:break
 if found is None:Path(out).unlink();raise ValueError('Target declaration not found: '+target)
 p=Path(out)
 with p.open('rb')as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 found.update(bytes=p.stat().st_size,sha256=digest,name_records_parsed=names)
 return found
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--target',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with Path(a.source).open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==INPUT_SHA
 fixture=out/'source-prefix.ndjson';r=extract(a.source,fixture,a.target);r['original_input_sha256']=INPUT_SHA;(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');(out/'declaration.json').write_text(json.dumps(r['declaration'],indent=2)+'\n');subprocess.run(['zstd','-T0','-3',str(fixture)],check=True,capture_output=True);fixture.unlink();print(json.dumps({k:v for k,v in r.items()if k!='declaration'}),flush=True)
