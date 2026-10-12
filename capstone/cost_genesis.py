"""V3: derive a stopping predicate from primitive partition comparisons; verify no semantic loss."""
import itertools,json
from genesis import independent_oracle,execute,machines
from falsifier import TRAIN,HOLD,machine,partition,step

# Primitive predicate expression language: constants and comparisons of the
# current and proposed partitions; no named fixed-point/stop operator.
PREDICATES={
 'false':lambda old,new:False,
 'true':lambda old,new:True,
 'equal':lambda old,new:old==new,
 'unequal':lambda old,new:old!=new,
 'same_count':lambda old,new:len(set(old))==len(set(new)),
 'different_count':lambda old,new:len(set(old))!=len(set(new)),
}
def run(obs,tr,pred):
 p=partition(obs);count=0
 for _ in range(len(obs)):
  q=step(p,tr,'both');count+=1
  if PREDICATES[pred](p,q):break
  p=q
 return p,count

def main():
 # Selection occurs without holdout access. Exhaustively enumerate n=2,3
 # and use two adversarial source-independent delayed-split machines.
 train=[(obs,tr) for n in (2,3) for obs,tr in machines(n)]
 train += [([0,0,0,1],[(0,0),(0,2),(3,0),(3,3)]),
           ([0,0,0,0,1],[(1,0),(2,0),(3,0),(4,0),(4,4)])]
 # Evaluate all candidates against independent word-based semantics, not
 # against the very same refinement code that executes them.
 records=[]
 for name in PREDICATES:
  incorrect=0;steps=0;witness=None
  for obs,tr in train:
   got,cost=run(obs,tr,name);want=independent_oracle(obs,tr)
   steps+=cost
   if got!=want:
    incorrect+=1
    if witness is None:witness={'obs':list(obs),'tr':[list(x) for x in tr],'got':got,'want':want}
  records.append({'name':name,'incorrect':incorrect,'steps':steps,'witness':witness})
 viable=[r for r in records if r['incorrect']==0]
 chosen=min(viable,key=lambda r:(r['steps'],r['name']))
 # Frozen holdouts, evaluated only after choosing the rule.
 held={}
 for t in HOLD:
  _,obs,tr=machine(t)
  got,cost=run(obs,tr,chosen['name']);want=independent_oracle(obs,tr)
  _,base=run(obs,tr,'false')
  held[t]={'pass':got==want,'iterations':cost,'baseline_iterations':base,'saved':base-cost}
 # Requalification of all previously protected families.
 old={}
 for t in TRAIN:
  _,obs,tr=machine(t)
  got,cost=run(obs,tr,chosen['name']);old[t]=got==independent_oracle(obs,tr)
 assert all(old.values()) and all(x['pass'] for x in held.values())
 assert chosen['name'] in ('equal','same_count')
 assert all(x['saved']>=0 for x in held.values())
 result={'status':'FINITE_VERIFIED_COST_REPAIR','training_machine_count':len(train),
 'predicates':records,'selected':chosen['name'],'holdout':held,
 'prior_protected':old,'new_rule_from_supplied_predicate_grammar':True,
 'strong_ledger_same_algorithm_can_match':True,
 'limitations':['finite Moore model','source-supplied predicate grammar','no independent Lean proof','no demonstrated economic advantage against equal baseline']}
 print(json.dumps(result,indent=2,sort_keys=True))
 return result
if __name__=='__main__':main()
