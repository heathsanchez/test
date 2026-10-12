"""V4 prospective cost-mediated dependency; strong-ledger parity is explicit."""
import itertools,json

def part(seq):
 d={};out=[]
 for x in seq:
  if x not in d:d[x]=len(d)
  out.append(d[x])
 return tuple(out)
def step(p,tr):return part([(p[i],p[a],p[b]) for i,(a,b) in enumerate(tr)])
def oracle(obs,tr):
 n=len(obs);sig=[]
 for i in range(n):
  v=[]
  for k in range(n):
   for word in itertools.product((0,1),repeat=k):
    j=i
    for a in word:j=tr[j][a]
    v.append(obs[j])
  sig.append(tuple(v))
 return part(sig)
def run(obs,tr,early):
 p=part(obs);rounds=0
 for _ in range(len(obs)):
  q=step(p,tr);rounds+=1
  if early and q==p:break
  p=q
 return p,rounds
def chain(n):
 obs=[0]*(n-1)+[1]
 tr=[(min(i+1,n-1),i) for i in range(n)]
 return obs,tr
def main():
 sizes=(4,5,6,7,8,9);budget=26;rows=[]
 for n in sizes:
  obs,tr=chain(n);want=oracle(obs,tr)
  plain=run(obs,tr,False);learned=run(obs,tr,True)
  assert plain[0]==learned[0]==want
  rows.append({'n':n,'plain_rounds':plain[1],'learned_rounds':learned[1]})
 def allocate(early):
  left=budget;solved=[]
  for row in rows:
   cost=row['learned_rounds' if early else 'plain_rounds']
   if cost<=left:solved.append(row['n']);left-=cost
   else:break
  return {'solved':solved,'remaining':left}
 outcomes={'old_generator':allocate(False),'learned_generator':allocate(True),'equally_informed_ledger':allocate(True),'deletion_ablation':allocate(False)}
 assert len(outcomes['learned_generator']['solved'])>len(outcomes['old_generator']['solved'])
 assert outcomes['learned_generator']==outcomes['equally_informed_ledger']
 result={'status':'BOUNDED_COST_MEDIATED_DEPENDENCE','budget_rounds':budget,'fresh_chain_sizes':sizes,'rows':rows,'outcomes':outcomes,'limitations':['source-constructed chain family','fixed budget in abstract rounds','same algorithm strong-ledger parity','no new generator grammar','no Lean verification','not natural-domain transfer']}
 print(json.dumps(result,sort_keys=True,indent=2))
if __name__=='__main__':main()
