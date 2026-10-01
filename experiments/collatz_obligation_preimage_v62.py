"""Exact backward reuse of two qualified laws on the joined V61 obligations.

This qualifies a scoped compiler and measures its limit. Conditional guards
are retained as candidates; their existence is not an exhaustion theorem.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from math import gcd
import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import orbit

@dataclass(frozen=True)
class Law:
    name: str
    base: int
    modulus: int
    lower: int
    lower_slope: int
    steps: int

LAWS=[Law('V60',926660659327753256987,2**71,772958606084060086381,2*3**44,71),
      Law('V58',3403982007377265835376667,2**83,1516043288339062768749913,2*3**51,83)]

def pullback(N,S,X,R,law):
    """Return an exact guarded ray on u, with its lower source below N+S*u.

    The source is never replaced by the macro endpoint. This computes
    applicability AND the origin inequality, not a feature signature.
    """
    g=gcd(R,law.modulus)
    if (law.base-X)%g:return None
    period=law.modulus//g
    residue=(((law.base-X)//g)*pow(R//g,-1,period))%period if period>1 else 0
    v0=(X+R*residue-law.base)//law.modulus
    vs=R//g
    delta0=N+S*residue-law.lower-law.lower_slope*v0
    delta_slope=S*period-law.lower_slope*vs
    if delta_slope<0 or (delta_slope==0 and delta0<=0):return None
    start=max(0,(-v0+vs-1)//vs,
        (-delta0)//delta_slope+1 if delta_slope>0 and delta0<=0 else 0)
    first=residue+period*start
    parameter=v0+vs*start
    assert parameter>=0
    assert X+R*first==law.base+law.modulus*parameter
    assert N+S*first>law.lower+law.lower_slope*parameter
    assert delta_slope>=0
    return dict(first=str(first),period=str(period),parameter0=str(parameter),
        parameter_slope=str(vs),origin_margin0=str(N+S*first-law.lower-law.lower_slope*parameter),
        origin_margin_slope=str(delta_slope))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--state',required=True)
    args=ap.parse_args();state=json.load(open(args.state))
    checksum=state.pop('certificate_sha256')
    assert hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()==checksum
    assert checksum=='a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6'
    live=state['joined_reclosure']['residual_residues'];assert len(live)==14934
    S=bank.NC*2**18
    counts=Counter(whole_cell_closures=0);sizes=Counter();best=None;best_new=None
    for r in live:
        N=bank.N0+bank.NC*r
        for j,X,R,q in bank.fixed_prefix(N,S):
            for law in LAWS:
                p=pullback(N,S,X,R,law)
                if p is None:continue
                m=int(p['period']);u=int(p['first'])
                bits=m.bit_length()-1;assert m==2**bits
                counts['guarded_rays']+=1;sizes[bits]+=1
                if m==1 and u==0:counts['whole_cell_closures']+=1
                prior_v58=r==900 and u%64==0 and m%64==0
                if prior_v58:counts['subsumed_by_retained_V58']+=1
                key=(bits,u,j,r,law.name)
                row=dict(r=r,macro_steps=j,law=law.name,guard=p,
                    known_subsumed=prior_v58)
                if best is None or key<best[0]:best=(key,row)
                if not prior_v58 and (best_new is None or key<best_new[0]):best_new=(key,row)
    assert counts['whole_cell_closures']==0
    assert best[1]['r']==900 and best[1]['macro_steps']==0 and best[1]['law']=='V58'
    assert int(best[1]['guard']['period'])==64 and best[1]['known_subsumed']
    # Independent actual orbit replay of the smallest non-subsumed guard.
    replay=[]
    if best_new is not None:
        row=best_new[1];law=next(x for x in LAWS if x.name==row['law'])
        r=row['r'];N=bank.N0+bank.NC*r;p=row['guard']
        for t in (0,1,3):
            u=int(p['first'])+int(p['period'])*t
            n=N+S*u;y=orbit(n,row['macro_steps'])[0]
            v=(y-law.base)//law.modulus
            lower=law.lower+law.lower_slope*v
            assert v>=0 and y==law.base+law.modulus*v and 0<lower<n
            assert orbit(n,row['macro_steps']+law.steps)[0]==orbit(lower,1)[0]
            replay.append(dict(t=t,source=str(n),lower=str(lower)))
    # An immediate protected guard depends on its source frame.
    # Source 4/current 3 is a direct exit; source 1/current 3 is not.
    assert 0<3<4 and not 0<3<1
    result=dict(schema='COLLATZ_GUARDED_OBLIGATION_PREIMAGE_V62',
        parent_run=36830138059,parent_state_sha256=checksum,
        protected_query='ExitObligation(original_source,current)',
        formal_reuse='coalescence preserves the eventual-exit obligation under arbitrary actual continuations with the same source',
        input_cells=len(live),frozen_laws=[x.name for x in LAWS],
        counts=dict(counts),guard_parameter_bits=dict(sorted(sizes.items())),
        cheapest=best[1],cheapest_non_subsumed=best_new[1] if best_new else None,
        exact_replays=replay,
        adaptation='reject direct preimages of these two frozen laws along maximal fixed prefixes as whole-cell exhaustion in this compiler scope; do not promote conditional rays into universal progress',
        proof_obligations=dict(universal_source_admission='UNKNOWN',
            universal_certificate_production='UNKNOWN',termination='UNKNOWN'),
        qed=False,global_collatz='UNKNOWN',
        boundary='two-law compiler test on the exact joined family residual; no complete ROS saturation or full policy-to-future quotient claimed')
    result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
