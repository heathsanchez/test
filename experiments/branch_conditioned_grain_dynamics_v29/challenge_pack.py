#!/usr/bin/env python3
from __future__ import annotations
from basis import BranchWorld

MAIN=BranchWorld(
 state_count=4,
 histories=((7,1),(7,2)),
 future_signatures=(
   ((0,),(0,),(1,),(1,)),
   ((0,),(1,),(0,),(1,))
 ),
 complete=True,world_id="main"
)

DUPLICATE=BranchWorld(
 state_count=4,
 histories=((5,1),(5,2)),
 future_signatures=(
   ((0,),(0,),(1,),(1,)),
   ((0,),(0,),(1,),(1,))
 ),
 complete=True,world_id="duplicate"
)

PERTURBED=BranchWorld(
 state_count=4,
 histories=MAIN.histories,
 future_signatures=(
   ((0,),(1,),(2,),(2,)),
   MAIN.future_signatures[1]
 ),
 complete=True,world_id="perturbed"
)

def relabel(world,state_perm,history_perm,world_id):
 inv=[0]*world.state_count
 for old,new in enumerate(state_perm):inv[new]=old
 histories=tuple(world.histories[i] for i in history_perm)
 futures=tuple(tuple(world.future_signatures[i][inv[s]] for s in range(world.state_count)) for i in history_perm)
 return BranchWorld(world.state_count,histories,futures,True,world_id)

RELABELED=relabel(MAIN,(2,0,3,1),(1,0),"relabelled")

INCOMPLETE=BranchWorld(
 state_count=4,histories=MAIN.histories,future_signatures=MAIN.future_signatures,
 complete=False,world_id="incomplete"
)
