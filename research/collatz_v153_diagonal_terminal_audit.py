"""V153 finite diagonal terminal-clock audit; no asymptotic inference.
All accepted starts have a *real* verified shortcut path to terminal {1,2};
each memoized duration is justified by a checked successor edge.
"""
from __future__ import annotations
import json
from collections import Counter

def shortcut(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def build(limit_k:int=21):
    assert 8<=limit_k<=23
    time={1:0,2:0}
    edges=0
    largest=2
    hist=Counter({0:2})
    result={}
    for n in range(3,1<<limit_k):
        x=n
        trace=[]
        while x not in time:
            assert x>0
            trace.append(x)
            nxt=shortcut(x)
            assert nxt>0
            largest=max(largest,x,nxt)
            x=nxt
        t=time[x]
        for y in reversed(trace):
            nxt=shortcut(y)
            assert nxt in time and time[nxt]==t
            time[y]=t+1
            edges+=1
            t+=1
        hist[time[n]]+=1
        if (n+1)&n==0 and n+1>=256:
            k=(n+1).bit_length()-1
            assert sum(hist.values())==n
            cutoff=1<<k
            rows=[]
            for c in (1,2,4,6,8,10,12,16):
                unknown=sum(ct for age,ct in hist.items() if age>c*k)
                assert 0<=unknown<cutoff
                rows.append(dict(c=c,horizon=c*k,exceptional_count=unknown,
                    fraction=round(unknown/cutoff,10),
                    complete_proof_carrying_terminal_count=cutoff-1-unknown))
            result[k]=dict(k=k,cutoff=cutoff,
                           max_terminal_time=max(hist),clocks=rows)
    assert len(result)==limit_k-7
    return result,edges,len(time),largest

def adversarial_corridors():
    rows=[]
    for K in (8,16,32,64,128):
        x=(1<<K)-1
        for j in range(K+1):
            assert x==pow(3,j)*pow(2,K-j)-1
            assert x not in (1,2)
            if j<K:
                assert x%2==1
                x=shortcut(x)
        rows.append(dict(K=K,source_bits=K,
                         no_direct_terminal_within_odd_corridor=True,
                         general_lower_merge_not_ruled_out=True))
    return rows

def main():
    data,edges,states,largest=build()
    def frac(k,c):
        return next(z['exceptional_count']/data[k]['cutoff']
                    for z in data[k]['clocks'] if z['c']==c)
    assert frac(21,4)>frac(8,4)
    assert frac(21,8)<frac(8,8)
    assert frac(21,12)>frac(18,12)
    assert frac(21,12)>0 and frac(21,8)>0
    return {
      'schema':'COLLATZ_V153_FINITE_DIAGONAL_TERMINAL_CLOCK',
      'finite_dyadic_k_min':8,'finite_dyadic_k_max':21,
      'certified_successor_edges':edges,
      'memoized_actual_source_states':states,
      'largest_visited_integer':str(largest),
      'terminating_shortcut_terminal_roots':[1,2],
      'source_attached_finite_terminal_clocks_only':True,
      'no_descent_only_promotions':True,
      'all_finite_population_paths_terminate':True,
      'all_population_densities_sampled_only':True,
      'c4_timeout_fraction_k21_gt_k8':True,
      'c8_timeout_fraction_k21_lt_k8':True,
      'c12_timeout_fraction_k21_gt_k18':True,
      'c12_timeouts_nonzero_at_k21':True,
      'unknown_is_not_a_counterexample':True,
      'actual_mersenne_prefix_controls':adversarial_corridors(),
      'finite_rows':[data[k] for k in sorted(data)],
      'sparse_all_depth_population_bound_proved':False,
      'external_predecessor_amplifier_rebuilt':False,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
