from pathlib import Path
import json,hashlib,lzma
R=Path(__file__).resolve().parent;rows=[]
for label,source in [('root',R/'reified/pair-0/goal.ndjson'),('proposition',R/'subgoals/00-root-arg1/goal.ndjson'),('data',R/'subgoals/01-root-arg1-arg2/goal.ndjson')]:
 raw=source.read_bytes();lines=raw.splitlines(True);records=[json.loads(x)for x in lines];expr={r['ie']:r for r in records if 'ie'in r};roots=set()
 def root_values(v):
  if isinstance(v,dict):
   for k,w in v.items():
    if k in('type','value','rhs')and isinstance(w,int)and not isinstance(w,bool):roots.add(w)
    else:root_values(w)
  elif isinstance(v,list):
   for w in v:root_values(w)
 for r in records:
  if not any(k in r for k in('ie','il','in','meta')):root_values(r)
 needed=set();pending=list(roots)
 while pending:
  i=pending.pop()
  if i in needed:continue
  if i not in expr:raise ValueError(('missing-expression',i))
  needed.add(i);r={k:v for k,v in expr[i].items()if k!='ie'};tag=next(iter(r));v=r[tag]
  if tag=='app':pending.extend([v['fn'],v['arg']])
  elif tag in('lam','forallE'):pending.extend([v['type'],v['body']])
  elif tag=='letE':pending.extend([v['type'],v['value'],v['body']])
  elif tag=='proj':pending.append(v['struct'])
  elif tag not in('sort','bvar','const','natVal','strVal'):raise ValueError(('unsupported-expression-tag',tag))
 data=b''.join(line for line,r in zip(lines,records)if 'ie'not in r or r['ie']in needed);D=R/'compact'/label;D.mkdir(parents=True,exist_ok=True);(D/'goal.ndjson').write_bytes(data);compressed=lzma.compress(data,preset=6);(D/'goal.ndjson.xz').write_bytes(compressed)
 row=dict(label=label,parent_input_sha256=hashlib.sha256(raw).hexdigest(),input_sha256=hashlib.sha256(data).hexdigest(),input_bytes=len(data),compressed_sha256=hashlib.sha256(compressed).hexdigest(),compressed_bytes=len(compressed),retained_expression_records=len(needed),original_expression_records=len(expr),all_declarations_names_levels_retained=True,only_unreferenced_expression_records_removed=True,reference_verification='PENDING',no_rank_claim=True,complete_mathlib_accept=False)
 (D/'compaction.json').write_text(json.dumps(row,indent=2));rows.append(row);print(json.dumps(row),flush=True)
(R/'compaction-report.json').write_text(json.dumps(rows,indent=2))
