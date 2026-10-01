import sys,json,hashlib,collections,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import collatz_crystal_parameter_quotient_v25 as bank
from collatz_obligation_preimage_v62 import Law,pullback
from collatz_consequential_splice_reuse_v57 import orbit
ap=argparse.ArgumentParser();ap.add_argument('--bank',required=True);ap.add_argument('--state',required=True);args=ap.parse_args()
assert hashlib.sha256(Path(args.bank).read_bytes()).hexdigest()=='f6ae7adab39824a50f227546be6d4990ac7045f2ec320a134db2354048e530b9'
cs=json.load(open(args.bank))
laws=[]
for c in cs:
 n=int(c['n']);s=int(c['source_slope']);y=int(c['y']);k=c['k'];q=c['q']
 assert n==bank.N0+bank.NC*c['r'] and s==bank.NC*2**c['h']
 end=3**(q+8)
 assert orbit(n,k)[0]==y
 if c['kind']=='D': lower=y;ls=end;depth=0
 else:
  lower=int(c['p']);ls=2*3**(q+7);depth=1
  assert orbit(lower,1)[0]==y
 assert 0<lower<n and 0<ls<=s
 # Independent affine replay: supports compiler qualification, not replacement of Lean bank.
 for u in (1,2):
  assert orbit(n+s*u,k)[0]==y+end*u
  assert orbit(lower+ls*u,depth)[0]==y+end*u
 dyadic=2**k
 prefix=bank.fixed_prefix(n,dyadic)
 assert prefix[-1]==(k,y,3**q,q)
 assert ls%6561==0
 laws.append((Law(str(c['r'])+'/'+str(c['h']),n,dyadic,lower,ls//6561,k),depth))
state=json.load(open(args.state));parent_checksum=state.pop('certificate_sha256')
assert hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()==parent_checksum
assert parent_checksum=='a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6'
live=state['joined_reclosure']['residual_residues'][:128]
counts=collections.Counter();hist=collections.Counter();examples=[];closed=[];u0_hits=[]
S=bank.NC*2**18
transitions=[]
for residue in range(6):
 coefficient,constant=(3,residue//2) if residue%2==0 else (9,(3*residue+1)//2)
 assert coefficient%3==0
 if residue%3:assert constant%3!=0
 if residue%2:assert constant%3==2
 transitions.append(dict(residue=residue,coefficient=coefficient,constant=constant))
assert bank.N0%6561==0 and bank.N0%2==1 and bank.NC%6561==0 and bank.NC%2==0
from collatz_obligation_preimage_v62 import LAWS
control=pullback(bank.N0+bank.NC*900,S,bank.N0+bank.NC*900,S,LAWS[1])
assert control and int(control['first'])==0 and int(control['period'])==64
indexes={}
for e in range(78):
 groups=collections.defaultdict(list)
 for law,depth in laws:
  bits=min(e,law.modulus.bit_length()-1)
  groups[(bits,law.base%(2**bits))].append((law,depth))
 indexes[e]=groups
for r in live:
 N=bank.N0+bank.NC*r; rays=[]
 for j,X,R,q in bank.fixed_prefix(N,S):
  counts['prefixes']+=1
  # Dyadic requalification removes the frozen ternary guard.
  counts['ternary_eligible_prefixes']+=1
  e=bank.v2(R)
  candidates=[]
  for bits in range(e+1):candidates.extend(indexes[e].get((bits,X%(2**bits)),[]))
  for law,depth in candidates:
   counts['law_tests']+=1
   p=pullback(N,S,X,R,law)
   if p is None:continue
   counts['guarded_rays']+=1
   first=int(p['first']);period=int(p['period']);hist[period.bit_length()-1]+=1
   row=dict(r=r,j=j,law=law.name,lower_depth=depth,guard=p)
   rays.append((first,period,row))
   if first==0:u0_hits.append(row)
   if len(examples)<8:examples.append(row)
 # A union cannot cover all u>=0 unless it contains u=0.
 if not any(f==0 for f,m,row in rays):counts['cells_with_uncovered_zero']+=1
 else:
  counts['cells_requiring_union_check']+=1
  # Full congruence rays suffice; merge sibling dyadic classes to root.
  classes={(m,f) for f,m,row in rays if f<m}
  changed=True
  while changed:
   changed=False
   for m,a in list(classes):
    if m>1 and (m,a^(m//2)) in classes:
     classes.discard((m,a));classes.discard((m,a^(m//2)));classes.add((m//2,a%(m//2)));changed=True
  if (1,0) in classes:closed.append(r)
  else:counts['union_unresolved']+=1
assert len(live)==128
res=dict(parent_state_sha256=parent_checksum,bank_run=36663027013,residue_transition_certificate=transitions,positive_control=control,adaptation='REQUALIFY source-cylinder guards; no coordinate expansion warranted',global_collatz='UNKNOWN',schema='COLLATZ_DYADIC_BANK_REQUALIFICATION_PROBE',bank_laws=len(laws),input_cells=len(live),counts=dict(counts),whole_cell_closures=closed,u0_hits=u0_hits,guard_bits=dict(hist),examples=examples,qed=False,scope='Candidate dyadic requalification of 3294 bank laws; direct preimages on the first 128 V61 cells only. Exact fixed-prefix arithmetic, no new Lean admission; no full residual saturation claim.')
res['certificate_sha256']=hashlib.sha256(json.dumps(res,sort_keys=True).encode()).hexdigest()
print(json.dumps(res,indent=2,sort_keys=True))
