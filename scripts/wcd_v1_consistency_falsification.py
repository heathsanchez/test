#!/usr/bin/env python3
"""Targeted epistemic consistency attack on frozen WCD V1."""
FROZEN="978af4e94815128b4c517562f9a0bae26eea1e55"

def dist(worlds):
    return all(any(a!=b for a,b in zip(p,q)) for p,q in worlds)
def eq(worlds):
    return all(all(a==b for a,b in zip(p,q)) for p,q in worlds)

def run():
    worlds=[]
    d=dist(worlds)
    e=eq(worlds)
    print("frozen_wcd_commit",FROZEN)
    print("empty_compatible_world_set",worlds)
    print("DIST_E",d)
    print("EQ_E",e)
    if d and e:
        print("FALSIFIED_WCD_V1_EMPTY_WORLD_VACUITY")
        raise SystemExit(1)
    print("WCD_V1_CONSISTENCY_ATTACK_DID_NOT_FALSIFY")

if __name__=="__main__":run()
