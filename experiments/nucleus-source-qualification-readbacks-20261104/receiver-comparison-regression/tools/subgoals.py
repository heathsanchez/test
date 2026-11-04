from pathlib import Path
import runpy,json,hashlib,functools
R=Path(__file__).resolve().parent;ns=runpy.run_path(str(R/'reify.py'));s=json.loads((R/'snapshots/pair-0.json').read_text());r=ns['Reifier'](s);data=r.build();assert hashlib.sha256(data).hexdigest()=='ce6bb6ab05205db63996338f4905f2e69ad2e90e69506515c32b23c9b89b329b';summary=r.summary;nodes={**ns['expr'],**{x['ie']:{k:v for k,v in x.items()if k!='ie'}for x in r.add if 'ie'in x}}
names={x['in']:{k:v for k,v in x.items()if k!='in'}for x in ns['records']if 'in'in x}
@functools.lru_cache(None)
def name(i):
 if not i:return ''
 x=names[i]
 if 'str'in x:v=x['str'];tail=v['str']
 else:v=x['num'];tail=str(v['i'])
 return(name(v['pre'])+'.'if v['pre']else'')+tail
byname={name(i):i for i in names};eq=byname['Eq'];refl=byname['Eq.refl'];goals=[]
def spine(i):
 args=[]
 while 'app'in nodes[i]:v=nodes[i]['app'];args.append(v['arg']);i=v['fn']
 return i,list(reversed(args))
@functools.lru_cache(None)
def lift(i,cutoff=0):
 node=nodes[i];tag=next(iter(node));v=node[tag]
 if tag=='bvar':return r.e({'bvar':v+int(v>=cutoff)})
 if tag=='app':return r.e({'app':{'fn':lift(v['fn'],cutoff),'arg':lift(v['arg'],cutoff)}})
 if tag in('lam','forallE'):return r.e({tag:{**v,'type':lift(v['type'],cutoff),'body':lift(v['body'],cutoff+1)}})
 if tag=='letE':return r.e({tag:{**v,'type':lift(v['type'],cutoff),'value':lift(v['value'],cutoff),'body':lift(v['body'],cutoff+1)}})
 if tag=='proj':return r.e({'proj':{**v,'struct':lift(v['struct'],cutoff)}})
 return i
def app(fn,*args):
 for a in args:fn=r.e({'app':{'fn':fn,'arg':a}})
 return fn
def emit(path,a,b,kind,carrier=None,us=None):
 goalname=r.name('NucleusReceiverSubgoal'+str(len(goals)))
 if kind=='type':
  typ=r.e({'forallE':{'name':0,'binderInfo':'default','type':b,'body':lift(b)}});val=r.e({'lam':{'name':0,'binderInfo':'default','type':a,'body':r.e({'bvar':0})}})
 else:
  typ=app(r.e({'const':{'name':eq,'us':us}}),carrier,a,b);val=app(r.e({'const':{'name':refl,'us':us}}),carrier,a)
 for i in reversed(range(summary['context_len'])):
  domain=summary['domains'][i];typ=r.e({'forallE':{'name':0,'binderInfo':'default','type':domain,'body':typ}});val=r.e({'lam':{'name':0,'binderInfo':'default','type':domain,'body':val}})
 thm={'thm':{'name':goalname,'levelParams':summary['universe_params'],'type':typ,'value':val,'all':[goalname]}};added=[x for x in r.add if 'thm'not in x]+[thm]
 data=b''.join(ns['parent'])+b''.join((json.dumps(x,separators=(',',':'),ensure_ascii=False)+'\n').encode()for x in added);D=R/'subgoals'/f'{len(goals):02d}-{path}';D.mkdir(parents=True,exist_ok=True);(D/'goal.ndjson').write_bytes(data);row=dict(path=path,kind=kind,left=a,right=b,carrier=carrier,universe_levels=us,input_sha256=hashlib.sha256(data).hexdigest(),input_bytes=len(data),reference_status='PENDING',no_full_mathlib_or_rank_claim=True);(D/'reification.json').write_text(json.dumps(row,indent=2));goals.append(row)
def walk(a,b,path='root',depth=0):
 if a==b or depth>=3:return
 ha,aa=spine(a);hb,bb=spine(b);ca=nodes[ha].get('const');cb=nodes[hb].get('const')
 if not(ca and cb and ca['name']==cb['name']==eq and len(aa)==len(bb)==3):return
 if aa[0]!=bb[0]:emit(path+'-carrier',aa[0],bb[0],'type')
 for i in[1,2]:
  if aa[i]!=bb[i]:
   emit(path+'-arg'+str(i),aa[i],bb[i],'term',aa[0],ca['us']);walk(aa[i],bb[i],path+'-arg'+str(i),depth+1)
walk(summary['left_type'],summary['right_type']);(R/'subgoals-report.json').write_text(json.dumps(goals,indent=2));print(json.dumps(goals,indent=2))
