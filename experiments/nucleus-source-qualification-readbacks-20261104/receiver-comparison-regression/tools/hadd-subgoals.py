from pathlib import Path
import runpy,json,hashlib,functools
R=Path(__file__).resolve().parent;g=runpy.run_path(str(R/'subgoals.py'));r=g['r'];nodes=g['nodes'];summary=g['summary'];byname=g['byname'];spine=g['spine'];app=g['app'];n=summary['context_len'];left,right=272625,272669
ha,aa=spine(left);hb,bb=spine(right);ca=nodes[ha]['const'];cb=nodes[hb]['const'];assert ca['name']==cb['name']==byname['HAdd.hAdd'];assert len(aa)==len(bb)==6 and aa[:3]==bb[:3] and len(set(aa[:3]))==1
carrier_inst=app(r.e({'const':{'name':byname['HAdd'],'us':ca['us']}}),*aa[:3]);nodes.update({x['ie']:{k:v for k,v in x.items()if k!='ie'}for x in r.add if 'ie'in x});eq_levels=[132];results=[]
def children(i,intr):
 x=nodes[i];tag=next(iter(x));v=x[tag]
 if tag=='app':return[(v['fn'],intr),(v['arg'],intr)]
 if tag in('lam','forallE'):return[(v['type'],intr),(v['body'],intr+1)]
 if tag=='letE':return[(v['type'],intr),(v['value'],intr),(v['body'],intr+1)]
 if tag=='proj':return[(v['struct'],intr)]
 return[]
def support(root,scope):
 pending=[(root,0)];seen=set();found=set()
 while pending:
  i,d=pending.pop()
  if(i,d)in seen:continue
  seen.add((i,d));x=nodes[i]
  if'bvar'in x and x['bvar']>=d:
   pos=scope-1-(x['bvar']-d);assert pos>=0;found.add(pos)
  pending.extend(children(i,d))
 return found
def thin(roots):
 keep=set().union(*(support(x,n)for x in roots))
 while True:
  new=keep|set().union(*(support(summary['domains'][i],i)for i in keep))
  if new==keep:break
  keep=new
 ordered=sorted(keep);position={old:i for i,old in enumerate(ordered)}
 @functools.lru_cache(None)
 def rewrite(i,scope,newscope,d=0):
  x=nodes[i];tag=next(iter(x));v=x[tag]
  def child(j,binder=False):return rewrite(j,scope,newscope,d+int(binder))
  if tag=='bvar':
   if v<d:return i
   old=scope-1-(v-d);assert old in position;return r.e({'bvar':newscope-1-position[old]+d})
  if tag=='app':return r.e({'app':{'fn':child(v['fn']),'arg':child(v['arg'])}})
  if tag in('lam','forallE'):return r.e({tag:{**v,'type':child(v['type']),'body':child(v['body'],True)}})
  if tag=='letE':return r.e({tag:{**v,'type':child(v['type']),'value':child(v['value']),'body':child(v['body'],True)}})
  if tag=='proj':return r.e({'proj':{**v,'struct':child(v['struct'])}})
  return i
 mapped=[rewrite(x,n,len(ordered))for x in roots];domains=[rewrite(summary['domains'][old],old,j)for j,old in enumerate(ordered)];return mapped,domains,ordered
def emit(label,carrier,a,b,do_thin):
 if do_thin:(carrier,a,b),domains,kept=thin([carrier,a,b])
 else:domains=[summary['domains'][i]for i in range(n)];kept=list(range(n))
 name=r.name('NucleusHAddSubgoal'+str(len(results)));typ=app(r.e({'const':{'name':byname['Eq'],'us':eq_levels}}),carrier,a,b);val=app(r.e({'const':{'name':byname['Eq.refl'],'us':eq_levels}}),carrier,a)
 for domain in reversed(domains):typ=r.e({'forallE':{'name':0,'binderInfo':'default','type':domain,'body':typ}});val=r.e({'lam':{'name':0,'binderInfo':'default','type':domain,'body':val}})
 thm={'thm':{'name':name,'levelParams':summary['universe_params'],'type':typ,'value':val,'all':[name]}};added=[x for x in r.add if'thm'not in x]+[thm];data=b''.join(g['ns']['parent'])+b''.join((json.dumps(x,separators=(',',':'),ensure_ascii=False)+'\n').encode()for x in added);D=R/'hadd-subgoals'/label;D.mkdir(parents=True,exist_ok=True);(D/'goal.ndjson').write_bytes(data);row=dict(label=label,input_sha256=hashlib.sha256(data).hexdigest(),input_bytes=len(data),context_len=len(domains),original_context_positions=kept,reference_verification='PENDING',hypothesized_typed_subgoal=True,no_rank_claim=True);(D/'reification.json').write_text(json.dumps(row,indent=2));results.append(row)
emit('instance-full',carrier_inst,aa[3],bb[3],False);emit('instance-thin',carrier_inst,aa[3],bb[3],True);emit('left-sum-thin',aa[0],aa[4],bb[4],True);emit('right-sum-thin',aa[0],aa[5],bb[5],True);(R/'hadd-subgoals-report.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
