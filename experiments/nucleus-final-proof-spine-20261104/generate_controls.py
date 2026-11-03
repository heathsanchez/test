#!/usr/bin/env python3
import json
from pathlib import Path
C=lambda n:('const',n)
V=lambda n:('var',n)
S=lambda n:('sort',n)
A=lambda f,*args: f if not args else A(('app',f,args[0]),*args[1:])
def bind(tag,binders,body):
 for n,t in reversed(binders):body=(tag,n,t,body)
 return body
class Export:
 def __init__(self):
  self.records=[{'meta':{'format':{'version':'3.1.0'}}},{'il':1,'succ':0}];self.names={};self.exprs={}
 def name(self,n):
  if n not in self.names:
   self.names[n]=len(self.names)+1;self.records.append({'in':self.names[n],'str':{'pre':0,'str':n}})
  return self.names[n]
 def expr(self,t,ctx=()):
  k=t[0]
  if k=='sort':r={'sort':t[1]}
  elif k=='const':r={'const':{'name':self.name(t[1]),'us':[]}}
  elif k=='var':r={'bvar':len(ctx)-1-ctx.index(t[1])}
  elif k=='app':r={'app':{'fn':self.expr(t[1],ctx),'arg':self.expr(t[2],ctx)}}
  elif k in ('pi','lam'):
   domain=self.expr(t[2],ctx);body=self.expr(t[3],ctx+(t[1],));r={('forallE' if k=='pi' else 'lam'):{'type':domain,'body':body}}
  key=json.dumps(r,sort_keys=True)
  if key not in self.exprs:
   i=len(self.exprs);self.exprs[key]=i;self.records.append(r|{'ie':i})
  return self.exprs[key]
 def axiom(self,n,t):
  ni=self.name(n);ty=self.expr(t);self.records.append({'axiom':{'name':ni,'type':ty,'levelParams':[]}})
 def theorem(self,n,ty,value):
  ni=self.name(n);t=self.expr(ty);v=self.expr(value);self.records.append({'thm':{'name':ni,'type':t,'value':v,'levelParams':[],'all':[ni]}})
 def save(self,p):p.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in self.records))
def make(kind):
 e=Export();e.axiom('C',S(1));e.axiom('P',S(0));e.axiom('Q',S(0));e.axiom('p',C('P'));e.axiom('q',C('Q') if kind=='wrong_prop' else C('P'))
 proofdom=C('C') if kind=='data_slot' else C('P')
 if kind=='data_slot':e.axiom('pData',C('C'));e.axiom('qData',C('C'))
 fty=bind('pi',[('x',C('C')),('y',C('C')),('proof',proofdom)],S(0))
 bs=[('F',fty),('a',C('C')),('b',C('C'))]
 if kind=='wrong_head':bs.insert(1,('G',fty))
 p=C('pData') if kind=='data_slot' else C('p');q=C('qData') if kind=='data_slot' else C('q')
 actual=A(V('F'),V('a'),V('b'),p)
 expected=A(V('G') if kind=='wrong_head' else V('F'),V('a'),V('a') if kind=='wrong_data' else V('b'),p if kind=='same' else q)
 bs.append(('w',actual));e.theorem('test',bind('pi',bs,expected),bind('lam',bs,V('w')));return e
def dependent():
 e=Export();e.axiom('C',S(1));e.axiom('R',bind('pi',[('x',C('C')),('y',C('C'))],S(0)))
 proof_ty=bind('pi',[('x',C('C'))],A(C('R'),V('x'),V('x')))
 e.axiom('p',proof_ty);e.axiom('q',proof_ty)
 fty=bind('pi',[('x',C('C')),('y',C('C')),('proof',A(C('R'),V('x'),V('y')))],S(0))
 bs=[('F',fty),('a',C('C')),('b',C('C')),('w',A(V('F'),V('a'),V('a'),A(C('p'),V('a'))))]
 expected=A(V('F'),V('a'),V('a'),A(C('q'),V('a')))
 e.theorem('test',bind('pi',bs,expected),bind('lam',bs,V('w')));return e
def long_prefix(mismatch=None):
 e=Export();e.axiom('C',S(1));e.axiom('R',bind('pi',[('x',C('C')),('y',C('C'))],S(0)))
 proof_ty=bind('pi',[('x',C('C'))],A(C('R'),V('x'),V('x')))
 e.axiom('p',proof_ty);e.axiom('q',proof_ty)
 data=[('x'+str(i),C('C')) for i in range(5)]
 fty=bind('pi',data+[('pr',A(C('R'),V('x0'),V('x0')))],S(0))
 bs=[('F',fty)]+[('a'+str(i),C('C')) for i in range(5)]+[('z',C('C'))]
 actual_args=[V('a'+str(i)) for i in range(5)];expected_args=actual_args.copy()
 if mismatch is not None:expected_args[mismatch]=V('z')
 actual=A(V('F'),*actual_args,A(C('p'),actual_args[0]));expected=A(V('F'),*expected_args,A(C('q'),expected_args[0]))
 bs.append(('w',actual));e.theorem('test',bind('pi',bs,expected),bind('lam',bs,V('w')));return e
if __name__=='__main__':
 root=Path(__file__).resolve().parent/'controls';root.mkdir(exist_ok=True)
 for kind in ['same','proof_last','wrong_data','wrong_prop','data_slot','wrong_head']:make(kind).save(root/(kind+'.ndjson'))

 dependent().save(root/'dependent_proof_last.ndjson')

 long_prefix().save(root/"long_prefix_valid.ndjson")
 for i in range(5):long_prefix(i).save(root/f"long_prefix_wrong_{i}.ndjson")
