from __future__ import annotations
from itertools import product

from basis import Row, World
from kernel import Kernel

N=4

S22=((0,1),(2,3))
S4=((0,),(1,),(2,),(3,))

IDENTITY2=((0,0),(1,1))
SWAP2=((0,1),(1,0))
FULL4=((0,2),(1,0),(2,3),(3,1))

VARIANTS=(
    (False,False),
    (True,False),
    (False,True),
)

EXPECTED_METRIC={
    "constant":(0,0,0),
    "bags":(0,1,0),
    "segmentation_only":(1,2,0),
    "joint_passive":(1,2,2),
    "joint_active":(1,2,2),
    "full_persistence":(1,6,4),
}

def map_segmentation(seg,reverse):
    if not reverse:
        return seg,{i:i for i in range(len(seg))}
    mapped=[tuple(sorted(N-1-i for i in block)) for block in seg]
    order=sorted(range(len(mapped)),key=lambda i:mapped[i])
    new=tuple(mapped[i] for i in order)
    old_to_new={old:new_i for new_i,old in enumerate(order)}
    return new,old_to_new

def transform_candidate(sb,sa,m,variant):
    rb,ra=VARIANTS[int(variant)]
    nsb,bmap=map_segmentation(sb,rb)
    nsa,amap=map_segmentation(sa,ra)
    nm=tuple(sorted((bmap[i],amap[j]) for i,j in m))
    return nsb,nsa,nm

def bag_signature(before,after):
    return (
        tuple(sorted(int(v) for v in before)),
        tuple(sorted(int(v) for v in after)),
    )

def labels_for(kind,variant):
    rb,ra=VARIANTS[int(variant)]
    if kind=="segmentation_only":
        sb,sa,m=transform_candidate(S22,S22,(),variant)
    elif kind in ("joint_passive","joint_active"):
        sb,sa,m=transform_candidate(S22,S22,IDENTITY2,variant)
    elif kind=="full_persistence":
        sb,sa,m=transform_candidate(S4,S4,FULL4,variant)
    else:
        sb=sa=m=None

    states=[]
    sigs=[]
    for values in product((0,1),repeat=2*N):
        before=tuple(values[:N])
        after=tuple(values[N:])
        states.append((before,after))
        if kind=="constant":
            sig=()
        elif kind=="bags":
            sig=bag_signature(before,after)
        else:
            probe=Row(before,after,-1,-1,0)
            sig=Kernel.signature(probe,sb,sa,m)
        sigs.append(sig)

    ids={}
    labels=[]
    for sig in sigs:
        if sig not in ids:
            ids[sig]=len(ids)
        labels.append(ids[sig])
    return states,labels,(sb,sa,m)

def response_for_action(action,sb,sa,m):
    bi=next(i for i,b in enumerate(sb) if int(action) in b)
    targets=[j for i,j in m if i==bi]
    if len(targets)!=1:
        raise ValueError("active hidden map must match every before segment exactly once")
    return min(sa[targets[0]])

def make_world(kind,variant=0,*,relabel=False,incomplete=False):
    states,labels,candidate=labels_for(kind,variant)
    sb,sa,m=candidate
    rows=[]
    for (before,after),y in zip(states,labels):
        if relabel:
            y=31+17*int(y)
        rows.append(Row(before,after,-1,-1,None if incomplete else int(y)))
        if kind=="joint_active":
            for action in range(N):
                response=response_for_action(action,sb,sa,m)
                rows.append(Row(
                    before,after,int(action),int(response),
                    None if incomplete else int(y),
                ))
    return World(
        f"{kind}_v{variant}" + ("_rel" if relabel else ""),
        tuple(rows),
        not incomplete,
    )

KINDS=(
    "constant","bags","segmentation_only",
    "joint_passive","joint_active","full_persistence",
)

WORLDS={(kind,v):make_world(kind,v) for kind in KINDS for v in range(len(VARIANTS))}
RELABELLED={kind:make_world(kind,0,relabel=True) for kind in KINDS}
INCOMPLETE=make_world("segmentation_only",0,incomplete=True)
