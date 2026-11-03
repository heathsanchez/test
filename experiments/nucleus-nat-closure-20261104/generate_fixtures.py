#!/usr/bin/env python3
"""Original byte-pinned prefix and minimal, explicitly invalid source controls."""
import argparse,copy,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SHA='7767e7f90b3e24b30ecb5324f1117d6858b5f40653b31011ad1948eed747e8ea'
DEFAULT=ROOT.parent/'nucleus-nat-frontier-20261104/fixtures/nat-prefix.ndjson.zst'
def generate(source,out):
 source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 data=subprocess.run(['zstd','-dc',str(source)],capture_output=True,check=True).stdout if source.suffix=='.zst' else source.read_bytes()
 assert hashlib.sha256(data).hexdigest()==SHA
 lines=data.splitlines(keepends=True);records=[json.loads(x)for x in lines];names={0:''}
 for r in records:
  if 'in'in r:
   n=r.get('str')or r.get('num');names[r['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')))
 def const(symbol):return next((i,r)for i,r in enumerate(records)if 'const'in r and names.get(r['const']['name'])==symbol and r['const']['us']==[])
 _,false=const('False');last=copy.deepcopy(records[-1]);assert 'thm'in last;last['thm']['type']=false['ie']
 changes={'false-goal':(len(lines)-1,last)}
 for symbol,label in [('Nat.pred','pred-universe'),('Nat.sub','sub-universe')]:
  index,r=const(symbol);r=copy.deepcopy(r);r['const']['us']=[0];changes[label]=(index,r)
 report=[]
 for name,change in [('nat-original',None),*changes.items()]:
  if change is None:payload=data
  else:
   index,r=change;pieces=lines.copy();pieces[index]=(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode();payload=b''.join(pieces)
  path=out/(name+'.ndjson');path.write_bytes(payload);report.append(dict(file=path.name,sha256=hashlib.sha256(payload).hexdigest(),expected=0 if change is None else 1))
 (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',default=str(DEFAULT));p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(generate(a.input,a.out)))
