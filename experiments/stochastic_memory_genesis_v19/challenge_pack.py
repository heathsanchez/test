#!/usr/bin/env python3
"""Post-freeze seeded noisy temporal worlds for V19."""
from __future__ import annotations
import random
from basis import TemporalWorld

TESTS=((0,),(1,))

def draw(p,n,rng):
    n1=sum(1 for _ in range(n) if rng.random()<p)
    return (n-n1,n1)

def present_world(seed,world_id,trials=64):
    rng=random.Random(seed); windows=[]; counts=[]
    for rep in range(4):
        for a,b in ((0,0),(0,1),(1,0),(1,1)):
            cur=(7,a,5,9,b,4)
            prev=(rep%2,(rep+1)%2,rep%3,8,(rep//2)%2,6)
            windows.append((cur,prev))
            counts.append((draw(.1 if a==0 else .9,trials,rng),draw(.2 if b==0 else .8,trials,rng)))
    return TemporalWorld(6,1,tuple(windows),TESTS,tuple(counts),True,world_id)

def memory_world(seed,world_id,trials=64,signal_channel=2):
    rng=random.Random(seed); windows=[]; counts=[]
    for rep in range(6):
        for s in (0,1):
            cur=(5,5,5,5,5,5)
            prev=[9,9,9,9,9,9]; prev[signal_channel]=s
            # nonpredictive variation on another channel
            prev[(signal_channel+2)%6]=rep%3
            windows.append((cur,tuple(prev)))
            counts.append((draw(.12 if s==0 else .88,trials,rng),draw(.18 if s==0 else .82,trials,rng)))
    return TemporalWorld(6,1,tuple(windows),TESTS,tuple(counts),True,world_id)

def mixed_world(seed,world_id,trials=64):
    rng=random.Random(seed); windows=[]; counts=[]
    for rep in range(4):
        for a,b in ((0,0),(0,1),(1,0),(1,1)):
            cur=(7,a,5,9,5,4)
            prev=(8,8,8,8,b,rep%2)
            windows.append((cur,prev))
            counts.append((draw(.1 if a==0 else .9,trials,rng),draw(.15 if b==0 else .85,trials,rng)))
    return TemporalWorld(6,1,tuple(windows),TESTS,tuple(counts),True,world_id)

PRESENT=present_world(1901,"present_sufficient")
MEM_A=memory_world(1911,"memory_a")
MEM_B=memory_world(1912,"memory_b")
MEM_C=memory_world(1913,"memory_c")
MIXED=mixed_world(1921,"mixed")
WRONG=memory_world(1931,"wrong_temporal_signal",signal_channel=5)

LOW=TemporalWorld(
    6,1,MEM_A.windows,TESTS,
    tuple(((1,0),(1,0)) for _ in MEM_A.windows),
    True,"low_data"
)
INCOMPLETE=TemporalWorld(
    MEM_A.channel_count,MEM_A.max_lag,MEM_A.windows,MEM_A.future_tests,MEM_A.counts,False,"incomplete"
)
