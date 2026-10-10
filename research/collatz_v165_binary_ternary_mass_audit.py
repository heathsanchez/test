"""V165 exact population transport from binary source cylinder to ternary endpoint.

For the true shortcut T, source-to-endpoint mass counts for an invariant
future-class predicate obey:
  count_{0<=q<Q} P(r+2^k*q)
    = count_{0<=q<Q} P(T^k(r)+3^a*q).
This is actually a pointwise matching, not a statistical mixing
assumption or a claim of density-one convergence.

For a NON-COLLATZ synthetic generalized shortcut G7, the SAME exact
source-affine law transports TWO genuinely disjoint periodic basins
simultaneously. Thus this identity alone does not impose a spectral gap
or imply any source converges under the real 3n+1 map.

All G7 classifications below are finite-source exact trace receipts.
Unterminated/unknown classifications are never silently promoted.
"""
import json
from collections import Counter


def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def G(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+7)//2


def prefix(n,k,step):
    a=0
    for _ in range(k):
        a+=n%2
        n=step(n)
    return a,n


def classify(n:int,step,cache:dict):
    if n in cache:
        return cache[n]
    cur=n
    path=[]
    seen=set()
    for _ in range(10000):
        if cur in cache:
            result=cache[cur]
            break
        if cur in seen:
            # A third actual future class, if found, would remain
            # a legitimate distinct class, not proof of convergence.
            result='OTHER_FINITE_CYCLE'
            break
        assert cur>=0
        assert cur.bit_length()<4096
        seen.add(cur)
        path.append(cur)
        cur=step(cur)
    else:
        raise AssertionError(('unresolved finite audit trajectory',n))
    for v in path:
        cache[v]=result
    return result


def main():
    k_max=9
    Q=96
    populations=[]
    instance_count=0
    both_class_present=0
    caches={
      'T':{0:'ZERO',1:'TERMINAL',2:'TERMINAL'},
      'G':{0:'ZERO',1:'B',2:'B',5:'B',11:'B',20:'B',10:'B',
           7:'A',14:'A'}
    }
    for label,step in (('T',T),('G',G)):
        cache=caches[label]
        nontrivial=0
        sample_profiles=[]
        for k in range(k_max+1):
            max_a=0
            for r in range(1<<k):
                a,g=prefix(r,k,step)
                max_a=max(max_a,a)
                observedA=Counter()
                observedB=Counter()
                for q in range(Q):
                    n=r+(1<<k)*q
                    y=g+(3**a)*q
                    exact_a,actual_y=prefix(n,k,step)
                    assert a==exact_a and y==actual_y,(label,k,r,q)
                    cn=classify(n,step,cache)
                    cy=classify(y,step,cache)
                    assert cn==cy,(label,k,r,q,n,y,cn,cy)
                    observedA[cn]+=1
                    observedB[cy]+=1
                    instance_count+=1
                assert observedA==observedB and sum(observedA.values())==Q
                if label=='G' and observedA['A']>0 and observedA['B']>0:
                    nontrivial+=1
                    both_class_present+=1
                if r in (0,1,(1<<k)-1) and len(sample_profiles)<30:
                    sample_profiles.append({
                        'k':k,'source_residue':r,
                        'target_endpoint':g,'odd_count':a,
                        'source_A':observedA['A'],
                        'source_B':observedA['B'],
                        'source_TERMINAL':observedA['TERMINAL'],
                        'source_ZERO':observedA['ZERO']
                    })
            assert max_a<=k
        assert nontrivial>0 if label=='G' else nontrivial==0
        populations.append({'map':label,'congruent_classes_preserved':True,
            'mixed_binary_source_cylinders_for_G7':nontrivial,
            'examples':sample_profiles})
    return {
      'schema':'COLLATZ_V165_EXACT_BINARY_TERNARY_FUTURE_CLASS_MASS',
      'actual_shortcut_T':'even n/2 odd (3n+1)/2',
      'synthetic_shortcut_G':'even n/2 odd (3n+7)/2',
      'distinct_synthetic_G_class_cycles':['7->14->7','5->11->20->10->5'],
      'finite_source_indices_per_cylinder':Q,
      'max_source_prefix_depth':k_max,
      'exact_source_endpoint_class_agreements':instance_count,
      'all_checked_finite_class_counts_equal':True,
      'synthetic_dual_class_fibers_detected':both_class_present,
      'same_mass_transport_admits_disjoint_future_classes':True,
      'true_Collatz_global_future_class_uniqueness_proved':False,
      'uniform_mass_spectral_gap_or_density_contraction_proved':False,
      'V151_sparse_terminal_exceptional_mass_proved':False,
      'synthetic_basin_counts_proved_all_scales':False,
      'tested_profiles':populations,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
