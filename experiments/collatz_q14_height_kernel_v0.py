#!/usr/bin/env python3
"""Crystal joint residue/height viability kernel for Q14 reverse barriers.

Finite abstraction over exact residues y mod 3^Q plus reverse-implied asymptotic
height barriers.  We conservatively retain an edge if there exist arbitrarily
large integer source/endpoint pairs in the source-relative height interval that
realize the shortcut residue transition and meet the target barrier.

This is a finite Q14 abstraction, not a proof unless the kernel empties under a
sound over-approximation.
"""
from fractions import Fraction
from collections import defaultdict,Counter,deque
import json
from collatz_reverse_predecessor_tree import enumerate_first_contractions

Q=14; M=3**Q
certs=enumerate_first_contractions(Q)
bar=[Fraction(1,1) for _ in range(M)]
for c in certs:
    z=Fraction(c.d,c.a)
    for r in range(c.residue,M,c.d):
        if z>bar[r]:bar[r]=z

# Residue transition mod M:
# even y: y must be divisible by 2, but mod odd M each residue has both parity
# lifts among integers; T=y/2 gives residue r*inv2.
# odd y: T=(3y+1)/2, residue determined.
inv2=pow(2,-1,M)
# Height update asymptotically: even h/2, odd 3h/2.
# A state has no upper height bound. Thus an edge to target barrier always
# exists for sufficiently large h. To gain sound pruning we need track a
# bounded/relative height interval, not only a lower barrier.
# Report this explicitly rather than fabricating an empty kernel.
edges={}
for r in range(M):
    re=(r*inv2)%M
    ro=((3*r+1)*inv2)%M
    edges[r]=(re,ro)

# Every residue has at least one outgoing edge and lower-bound-only height can
# be made arbitrarily large, hence the conservative viability kernel is all
# states. Compress by barrier class and edge barrier-class signatures.
sig=Counter()
for r,(a,b) in edges.items():
    sig[(bar[r],bar[a],bar[b])]+=1
print(json.dumps({
 "schema":"COLLATZ_Q14_HEIGHT_KERNEL_V0",
 "Q":Q,"states":M,"kernel_size":M,
 "barrier_classes":len(set(bar)),
 "transition_signatures":len(sig),
 "top_signatures":[{"src":[x[0].numerator,x[0].denominator],
                    "even":[x[1].numerator,x[1].denominator],
                    "odd":[x[2].numerator,x[2].denominator],"count":n}
                   for x,n in sig.most_common(30)],
 "decision":"LOWER_HEIGHT_BARRIERS_ALONE_CANNOT_PRUNE_POSTFIXED_KERNEL",
 "residual":"need an earned upper/resource constraint on normalized height, or a certificate whose applicability grows with height; lower bounds alone allow arbitrarily large h",
 "global_collatz":"UNKNOWN"},indent=2))
