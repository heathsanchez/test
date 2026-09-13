#!/usr/bin/env python3
from __future__ import annotations
from basis import InstrumentWorld

# Future signatures on states: 0,2 are class 0; 1,3 are class 1.
# A swaps 1<->2 and therefore changes future-relevant class for those states.
# B swaps 0<->2 and preserves future class.
# I is identity.
MAIN=InstrumentWorld(
 state_count=4,
 instrument_names=("mA","mB","mI"),
 outcomes=(
   (0,0,0,0),
   (0,0,0,0),
   (0,0,0,0),
 ),
 post_states=(
   (0,2,1,3),
   (2,1,0,3),
   (0,1,2,3),
 ),
 future_signatures=((0,),(1,),(0,),(1,)),
 complete=True,world_id="main"
)

def relabel(world,state_perm,instrument_perm,world_id):
 inv=[0]*world.state_count
 for old,new in enumerate(state_perm):inv[new]=old
 futures=tuple(world.future_signatures[inv[new]] for new in range(world.state_count))
 outs=[]; posts=[]; names=[]
 for oldm in instrument_perm:
  names.append(world.instrument_names[oldm])
  out=[0]*world.state_count; post=[0]*world.state_count
  for newx in range(world.state_count):
   oldx=inv[newx]
   out[newx]=world.outcomes[oldm][oldx]
   oldpost=world.post_states[oldm][oldx]
   post[newx]=state_perm[oldpost]
  outs.append(tuple(out)); posts.append(tuple(post))
 return InstrumentWorld(world.state_count,tuple(names),tuple(outs),tuple(posts),futures,True,world_id)

RELABELED=relabel(MAIN,(2,0,3,1),(1,0,2),"relabelled")

INCOMPLETE=InstrumentWorld(
 state_count=4,instrument_names=MAIN.instrument_names,outcomes=MAIN.outcomes,
 post_states=MAIN.post_states,future_signatures=MAIN.future_signatures,
 complete=False,world_id="incomplete"
)
