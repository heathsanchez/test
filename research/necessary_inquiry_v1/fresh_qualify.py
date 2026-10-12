#!/usr/bin/env python3
"""Run the source-frozen V2 rule generator on prospectively frozen dimensions/seeds.
Rule/code head frozen before fresh_protocol.md. No per-task changes.
"""
from random import Random
import json
import verify as v
import meta_verify as m

def main():
    source=v.Oracle(3,1,0b101,((0,1),))
    rule=m.induce(source.get)
    assert rule and rule['source_witness']==(0,1,2,3)
    assert len(source.cache)==4
    out=[]
    for n in (12,20,40,60):
        probes=v.design(n)
        mask_count=len(probes[0])
        assert mask_count>=32
        cases=0
        readouts=0
        full_readouts=0
        affine_adequate=0
        for k in (0,1,2):
            for j in range(6):
                seed=995000+n*1000+k*100+j
                _,c,a,ee=v.task(n,k,seed)
                o=v.Oracle(n,c,a,ee)
                found=m.developed_solver(n,o,probes,rule)
                assert found==(c,a,ee),('fresh transfer mismatch',n,k,j,found,ee)
                good=v.Oracle(n,c,a,ee)
                assert v.full(n,good)==found
                rng=Random(seed+2701)
                assert all(v.truth(x,n,*found)==v.truth(x,n,c,a,ee)
                           for x in (rng.getrandbits(n) for _ in range(512)))
                readouts+=len(o.cache)
                full_readouts+=len(good.cache)
                affine_adequate+=int(k==0)
                cases+=1
        # Exact negative control: an outside-grammar cycle is not admitted.
        neg=v.Oracle(n,1,0,((0,1),(0,2),(1,2)))
        assert m.developed_solver(n,neg,probes,rule) is None
        # Count information acquisition, not computation/memory/engineering costs.
        full_per_task=n+1+n*(n-1)//2
        assert full_readouts==full_per_task*cases
        cheap='sparse' if (n+1+3*mask_count)<full_per_task else 'full'
        out.append({'n':n,'protected_cases':cases,'correct':cases,
                    'probe_tests':mask_count,'sparse_queries_per_task':readouts//cases,
                    'full_queries_per_task':full_per_task,
                    'best_preselected_method':cheap,
                    'affine_only_solvable':affine_adequate,
                    'three_edge_countercontrol':'UNKNOWN'})
    assert sum(r['correct'] for r in out)==72
    assert sum(r['affine_only_solvable'] for r in out)==24
    print(json.dumps({'status':'PASS_PROSPECTIVE_SOURCE_FROZEN_RULE_TRANSFER',
                      'generator_freeze_commit':'2f00c75d0f97e469b097dacd342baae51dd25616',
                      'protocol':'research/necessary_inquiry_v1/fresh_protocol.md',
                      'source_rule':rule,'fresh':out,
                      'strong_sparse_stateless_comparator':'TIES_IF_GIVEN_SAME_PRIMITIVES',
                      'boundary':'synthetic GF2 quadratic<=2 with supplied generic query XOR and frame transport'},indent=2))

if __name__=="__main__":main()
