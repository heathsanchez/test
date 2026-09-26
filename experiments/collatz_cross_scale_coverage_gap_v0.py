#!/usr/bin/env python3
import json

MAX_DEPTH=24
frontier=[('',0)]
terminal=[]
by_depth={}
for k in range(MAX_DEPTH):
    nxt=[]
    for w,q in frontier:
        for b in (0,1):
            q2=q+b
            w2=w+str(b)
            d=k+1
            if 3**q2 < 2**d:
                terminal.append(w2)
                by_depth[d]=by_depth.get(d,0)+1
            else:
                nxt.append((w2,q2))
    frontier=nxt
term=set(terminal)
prefix_collisions=[]
for w in terminal:
    for i in range(1,len(w)):
        if w[:i] in term:
            prefix_collisions.append((w[:i],w))
            break
extension_first_crossing=0
for w in terminal:
    for b in '01':
        z=w+b
        q=0
        first=None
        for i,ch in enumerate(z,1):
            q += ch=='1'
            if 3**q < 2**i:
                first=i
                break
        if first==len(z):
            extension_first_crossing+=1
assert not prefix_collisions
assert extension_first_crossing==0
assert terminal
print(json.dumps({
 'schema':'COLLATZ_CROSS_SCALE_COVERAGE_GAP_V0',
 'max_depth':MAX_DEPTH,
 'terminal_first_crossing_words':len(terminal),
 'terminal_counts_by_depth':by_depth,
 'prefix_collisions':len(prefix_collisions),
 'one_step_extensions_that_are_later_first_crossings':extension_first_crossing,
 'decision':'FIRST_CROSSING_TERMINAL_LANGUAGE_IS_PREFIX_FREE',
 'theorem_level_consequence':'Excluding infinite coherent paths does not by itself exclude a finite M>=0 first-crossing cylinder.',
 'missing_coverage_bridge':'A universal proof needs a direct well-founded rank on finite M>=0 terminals or a proved obstruction-to-obstruction recursion. P35/P37 is the existing candidate.',
 'scope':'Coverage obstruction only; not a Collatz proof or counterexample.',
 'global_collatz':'UNKNOWN'
},indent=2,sort_keys=True))
