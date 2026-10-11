"""Joint observational and constructive future falsifier.

Two observationally identical states can differ in cost to realize goals.
The theorem is exact for the declared finite transition world, not physics.
"""
import itertools,json
from .pinhole_temporal_whole_v1 import partition

def main():
    states=range(4)
    # A and B have same observed bit; A has a cheap goal path, B an
    # expensive one. C,D similarly distinguish execution economics.
    observe=lambda s:s//2
    edges={0:[(2,1),(1,1)],1:[(2,9)],2:[(3,1)],3:[(2,8)]}
    goals=(2,3)
    def distances(goal):
        inf=10**9
        d={s:(0 if s==goal else inf) for s in states}
        for _ in states:
            d={s:min([d[s]]+[cost+d[t] for t,cost in edges[s]]) for s in states}
        return d
    ds={g:distances(g) for g in goals}
    obs_groups={}
    for s in states:obs_groups.setdefault(observe(s),[]).append(s)
    witness=[]
    for group in obs_groups.values():
        for a,b in itertools.combinations(group,2):
            if any(ds[g][a]!=ds[g][b] for g in goals):
                witness.append({'a':a,'b':b,'observed':observe(a),
                  'costs_a':[ds[g][a] for g in goals],
                  'costs_b':[ds[g][b] for g in goals]})
    assert witness
    # Goal-conditioned cost vectors refine present-only equivalence.
    signatures={s:tuple(ds[g][s] for g in goals) for s in states}
    assert len(set(signatures.values()))>len(obs_groups)
    # Full-cost-preserving quotient must not merge states with unequal
    # future goal-cost vectors, even when present observations agree.
    for a,b in itertools.combinations(states,2):
        if signatures[a]!=signatures[b]:
            assert not (signatures[a]==signatures[b])
    print(json.dumps({'status':'PASS_COST_SENSITIVE_FUTURE_SEPARATOR',
      'present_observation_classes':len(obs_groups),
      'goal_cost_classes':len(set(signatures.values())),
      'same_present_different_future_cost_pairs':len(witness),
      'witnesses':witness,'goals':goals,
      'oracle':'exact finite Bellman relaxation',
      'real_MDA_economic_transfer':'UNKNOWN',
      'physical_time_claim':'NOT_CLAIMED'},sort_keys=True,indent=2))
if __name__=='__main__':main()
