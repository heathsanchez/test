"""Extract an exact source prefix and a separately labeled signature-only diagnostic."""
import argparse,json,hashlib
from pathlib import Path

def extract(source,out,target):
 names={0:''};counter=0;offset=0;digest=hashlib.sha256();changed=0
 with source.open('rb')as inp,(out/'next-frontier.ndjson').open('wb')as original,(out/'signature-diagnostic.ndjson').open('wb')as diagnostic:
  for raw in inp:
   counter+=1;row=json.loads(raw);original.write(raw);digest.update(raw);offset+=len(raw)
   if 'in'in row:
    n=row.get('str',row.get('num'));names[row['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')))
   decl=next(((k,row[k])for k in ['thm','def','opaque','axiom','inductive','quot']if k in row),None)
   found=decl is not None and names.get(decl[1].get('name'))==target
   if 'thm'in row and not found:
    d=row['thm'];row={'axiom':dict(name=d['name'],levelParams=d['levelParams'],type=d['type'],isUnsafe=False)};diagnostic.write((json.dumps(row,separators=(',',':'))+'\n').encode());changed+=1
   else:diagnostic.write(raw)
   if found:break
  else:raise RuntimeError('target not found')
 report=dict(target=target,record=counter,bytes=offset,sha256=digest.hexdigest(),declaration=decl,diagnostic=dict(status='COUNTERFACTUAL_DIAGNOSTIC_NOT_ORIGINAL_MATHLIB_VERIFICATION',sha256=hashlib.sha256((out/'signature-diagnostic.ndjson').read_bytes()).hexdigest(),earlier_theorems_as_typed_axioms=changed))
 (out/'frontier.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--target',required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);extract(a.source,a.out,a.target)
