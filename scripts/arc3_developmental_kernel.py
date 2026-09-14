#!/usr/bin/env python3
"""
ARC-AGI-3 developmental kernel v3: change-before-object.

No game source, fixed route, coordinates, palette meanings, or level-number logic.

The first two frozen runs established a specific obstruction:
  - frames changed consistently under action,
  - object/component persistence did not survive the representation,
  - therefore persistent object identity was not warranted.

V3 moves one layer down. It derives a controllable position directly from the
boundary of pixel change (disappearing/appearing support), learns action ->
displacement from intervention, compiles that causal geometry, and explores a
position/action graph. Objecthood is optional and comes later.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np
import arc_agi
from arcengine import GameState


def latest_grid(obs: Any) -> np.ndarray:
    frames=getattr(obs,"frame",None)
    if frames is None: raise RuntimeError("observation has no frame")
    a=np.asarray(frames[-1] if isinstance(frames,(list,tuple)) else frames)
    a=np.squeeze(a)
    if a.ndim!=2: raise RuntimeError(a.shape)
    return a.astype(np.int16,copy=False)


def mode_color(g:np.ndarray)->int:
    v,c=np.unique(g,return_counts=True)
    return int(v[np.argmax(c)])


def blobs(mask:np.ndarray,min_n:int=2):
    h,w=mask.shape; seen=np.zeros_like(mask,dtype=bool); out=[]
    for y in range(h):
        for x in range(w):
            if seen[y,x] or not mask[y,x]: continue
            st=[(y,x)]; seen[y,x]=True; pts=[]
            while st:
                yy,xx=st.pop(); pts.append((yy,xx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True; st.append((ny,nx))
            if len(pts)>=min_n:
                ys=np.array([p[0] for p in pts]); xs=np.array([p[1] for p in pts])
                out.append({"n":len(pts),"cy":float(ys.mean()),"cx":float(xs.mean()),
                            "y0":int(ys.min()),"x0":int(xs.min()),"y1":int(ys.max()),"x1":int(xs.max())})
    return out


def boundary_motion(prev:np.ndarray,nxt:np.ndarray):
    """Candidate old->new carrier motion from changed support, without object identity."""
    bp,bn=mode_color(prev),mode_color(nxt)
    d=prev!=nxt
    # support that disappears into modal field / appears out of modal field
    old=blobs(d & (prev!=bp) & (nxt==bn),2)
    new=blobs(d & (prev==bp) & (nxt!=bn),2)
    cand=[]
    for o in old:
        for n in new:
            ratio=max(o["n"],n["n"])/max(1,min(o["n"],n["n"]))
            if ratio>2.5: continue
            dy=int(round(n["cy"]-o["cy"])); dx=int(round(n["cx"]-o["cx"]))
            dist=abs(dy)+abs(dx)
            if dist==0 or dist>24: continue
            # Similar support size is stronger; shorter plausible displacement wins ties.
            score=(abs(o["n"]-n["n"]),ratio,dist)
            cand.append((score,(dy,dx),(int(round(o["cy"])),int(round(o["cx"]))),
                         (int(round(n["cy"])),int(round(n["cx"]))),o["n"],n["n"]))
    cand.sort(key=lambda z:z[0])
    return cand


def structural_sig(g:np.ndarray, ignore_center:tuple[int,int]|None=None)->str:
    """Coarse scene signature; suppress a small carrier neighborhood if known."""
    a=g.copy()
    if ignore_center:
        y,x=ignore_center
        y0,y1=max(0,y-5),min(a.shape[0],y+6); x0,x1=max(0,x-5),min(a.shape[1],x+6)
        a[y0:y1,x0:x1]=mode_color(a)
    # 8x8 palette counts: enough to notice structural events, intentionally not full pixels.
    feat=[]
    q=np.clip(a,0,15)
    for y in range(0,a.shape[0],8):
        for x in range(0,a.shape[1],8):
            feat.extend((np.bincount(q[y:y+8,x:x+8].ravel(),minlength=16)//4).tolist())
    return hashlib.sha1(np.asarray(feat,dtype=np.int16).tobytes()).hexdigest()[:16]


class Agent:
    def __init__(self,seed=0):
        self.rng=random.Random(seed)
        self.events=[]; self.records=[]
        self.action_counts=Counter()
        self.motion=defaultdict(Counter)              # action -> vector counts
        self.vectors={}                               # compiled best vector per action
        self.pos=None
        self.graph=defaultdict(Counter)               # (scene,pos,action) -> (scene2,pos2) counts
        self.tried=defaultdict(set)                   # (scene,pos) -> actions
        self.blocked=set()
        self.visits=Counter()
        self.scene=None
        self.level=0; self.max_level=0; self.gameovers=0
        self.phase="CHANGE_BOUNDARY_GENESIS"
        self.last_boundary=None

    def event(self,kind,**kw):
        e={"t":len(self.records),"kind":kind,**kw}; self.events.append(e)
        print("EVENT",json.dumps(e,sort_keys=True),flush=True)

    def compile_vectors(self):
        old=dict(self.vectors)
        for an,c in self.motion.items():
            if not c: continue
            v,n=c.most_common(1)[0]
            total=sum(c.values())
            # One exact intervention is provisional; repeated agreement compiles.
            if n>=2 or (n==1 and total==1):
                self.vectors[an]=v
        if self.vectors!=old:
            self.phase="COMPILED_CAUSAL_GEOMETRY"
            self.event("ACTION_GEOMETRY_COMPILED",
                       vectors={k:list(v) for k,v in self.vectors.items()},
                       evidence={k:{str(list(v)):n for v,n in c.items()} for k,c in self.motion.items()})

    def reset_episode(self,grid,keep_compiled=True):
        self.pos=None
        self.scene=structural_sig(grid,None)
        self.graph.clear(); self.tried.clear(); self.blocked.clear(); self.visits.clear()
        self.last_boundary=None
        if not keep_compiled:
            self.motion.clear(); self.vectors.clear(); self.phase="CHANGE_BOUNDARY_GENESIS"

    def update(self,prev,grid,action,obs):
        cands=boundary_motion(prev,grid)
        chosen=cands[0] if cands else None
        oldpos=self.pos

        if chosen:
            _,vec,p0,p1,n0,n1=chosen
            # If we have a compiled vector for this action, prefer a candidate agreeing with it.
            if action in self.vectors:
                matches=[c for c in cands if c[1]==self.vectors[action]]
                if matches: chosen=matches[0]; _,vec,p0,p1,n0,n1=chosen
            self.last_boundary={"vector":list(vec),"old":list(p0),"new":list(p1),"support":[n0,n1]}
            self.motion[action][vec]+=1
            self.compile_vectors()
            # Boundary itself supplies the first provisional carrier position.
            if self.pos is None:
                self.pos=p1
                self.event("POSITION_GENESIS_FROM_CHANGE",action=action,old=list(p0),new=list(p1),vector=list(vec))
            else:
                # Prefer observed boundary destination when it agrees with our current position or compiled law.
                if abs(p0[0]-self.pos[0])+abs(p0[1]-self.pos[1])<=8 or self.vectors.get(action)==vec:
                    self.pos=p1
        else:
            self.last_boundary=None
            # No boundary motion: under a compiled vector, this is a blocked or non-motion intervention.
            if self.pos is not None and action in self.vectors:
                self.blocked.add((self.scene,self.pos,action))

        newscene=structural_sig(grid,self.pos)
        if oldpos is not None and self.pos is not None:
            k=(self.scene,oldpos)
            self.tried[k].add(action)
            self.graph[(self.scene,oldpos,action)][(newscene,self.pos)]+=1
            self.visits[(newscene,self.pos)]+=1
            # If coarse world structure changed beyond ordinary carrier motion, preserve it as state.
            if newscene!=self.scene:
                self.event("STRUCTURAL_STATE_SPLIT",old_scene=self.scene,new_scene=newscene,
                           at=list(self.pos),action=action)

        self.scene=newscene
        lvl=int(getattr(obs,"levels_completed",0))
        if lvl>self.max_level:
            self.event("VERIFIED_PROGRESS",from_level=self.max_level,to_level=lvl,action=action)
            self.max_level=lvl
        if lvl!=self.level:
            self.event("LEVEL_BOUNDARY",old=self.level,new=lvl)
            self.level=lvl
            # Compile action geometry across levels; discard local position graph.
            self.graph.clear(); self.tried.clear(); self.blocked.clear(); self.visits.clear()
            self.pos=None; self.scene=structural_sig(grid,None)

        self.records.append({
            "i":len(self.records),"action":action,
            "pixel_delta":int(np.count_nonzero(prev!=grid)),
            "boundary_candidates":[{"vec":list(c[1]),"old":list(c[2]),"new":list(c[3]),"support":[c[4],c[5]]}
                                   for c in cands[:8]],
            "chosen_boundary":self.last_boundary,
            "pos":list(self.pos) if self.pos else None,
            "scene":self.scene,
            "vectors":{k:list(v) for k,v in self.vectors.items()},
            "phase":self.phase,"level":lvl,
            "state":getattr(getattr(obs,"state",None),"name",str(getattr(obs,"state",None)))
        })

    def choose(self,actions):
        # Before position exists, balanced interventions seek a separating change boundary.
        if self.pos is None:
            # Prefer already compiled movement action after reset, otherwise balance.
            known=[a for a in actions if a.name in self.vectors]
            if known:
                a=min(known,key=lambda z:(self.action_counts[z.name],z.name))
                return a,{"mode":"REACQUIRE_POSITION","reason":"reuse compiled action geometry to recover change-defined position"}
            a=min(actions,key=lambda z:(self.action_counts[z.name],z.name))
            return a,{"mode":"BOUNDARY_PROBE","reason":"balanced intervention; object identity not assumed"}

        node=(self.scene,self.pos)
        names=[a.name for a in actions]
        # Test untried interventions at a newly warranted state.
        unseen=[a for a in actions if a.name not in self.tried[node]]
        if unseen:
            # Prefer actions whose geometry is unknown first, then least used.
            a=min(unseen,key=lambda z:(z.name in self.vectors,self.action_counts[z.name],z.name))
            return a,{"mode":"CAUSAL_PROBE","state":[self.scene,list(self.pos)],
                      "reason":"untried intervention at consequence-derived state"}

        # Search known graph for nearest state with unresolved intervention.
        adj=defaultdict(list)
        for (sc,p,an),outs in self.graph.items():
            if len(outs)==1:
                (sc2,p2),n=next(iter(outs.items()))
                adj[(sc,p)].append((an,(sc2,p2)))
        q=deque([(node,[])]); seen={node}
        while q:
            n,path=q.popleft()
            if n!=node and len(self.tried[n])<len(actions) and path:
                first=path[0]
                for a in actions:
                    if a.name==first:
                        return a,{"mode":"ROUTE_TO_FRONTIER","target":[n[0],list(n[1])],
                                  "reason":"shortest learned route to unresolved intervention"}
            for an,n2 in adj.get(n,[]):
                if n2 not in seen:
                    seen.add(n2); q.append((n2,path+[an]))

        # Expand position frontier using compiled vectors, preferring unseen predicted positions.
        opts=[]
        for a in actions:
            v=self.vectors.get(a.name)
            if v is None or (self.scene,self.pos,a.name) in self.blocked: continue
            p2=(self.pos[0]+v[0],self.pos[1]+v[1])
            opts.append((self.visits[(self.scene,p2)],self.action_counts[a.name],a,p2))
        if opts:
            _,_,a,p2=min(opts,key=lambda z:(z[0],z[1],z[2].name))
            return a,{"mode":"POSITION_FRONTIER","predicted_next":list(p2),
                      "reason":"least-visited position under compiled causal geometry"}

        a=min(actions,key=lambda z:(self.action_counts[z.name],z.name))
        return a,{"mode":"UNKNOWN_SEARCH","reason":"current causal graph has no warranted progress route"}

    def result(self):
        return {"actions":len(self.records),"max_levels_completed":self.max_level,
                "vectors":{k:list(v) for k,v in self.vectors.items()},
                "motion_evidence":{k:{str(list(v)):n for v,n in c.items()} for k,c in self.motion.items()},
                "phase":self.phase,"gameovers":self.gameovers,"action_counts":dict(self.action_counts),
                "events":self.events,"records":self.records}


def action_data(a,grid,rng):
    if not a.is_complex(): return {}
    return {"x":grid.shape[1]//2,"y":grid.shape[0]//2}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game",default="ls20"); ap.add_argument("--max-actions",type=int,default=400)
    ap.add_argument("--seed",type=int,default=0); ap.add_argument("--out",default="arc3_developmental_result.json")
    args=ap.parse_args()

    arc=arc_agi.Arcade()
    env=arc.make(args.game,save_recording=True,include_frame_data=True,render_mode=None)
    if env is None: raise SystemExit("arc.make returned None")
    obs=env.reset()
    if obs is None: raise SystemExit("reset returned None")
    grid=latest_grid(obs)
    A=Agent(args.seed); A.level=int(getattr(obs,"levels_completed",0)); A.max_level=A.level
    A.reset_episode(grid,keep_compiled=True)

    print("START",args.game,"actions",[a.name for a in env.action_space],
          "levels",getattr(obs,"levels_completed",None),"win_levels",getattr(obs,"win_levels",None),flush=True)

    for i in range(args.max_actions):
        acts=list(env.action_space)
        if not acts: break
        a,reason=A.choose(acts); A.action_counts[a.name]+=1
        prev=grid
        obs=env.step(a,data=action_data(a,grid,A.rng),reasoning=reason)
        if obs is None:
            A.event("NULL_OBSERVATION",action=a.name); continue
        grid=latest_grid(obs); A.update(prev,grid,a.name,obs)
        r=A.records[-1]
        print("STEP",i+1,a.name,reason["mode"],"delta",r["pixel_delta"],
              "pos",A.pos,"vectors",A.vectors,"level",getattr(obs,"levels_completed",None),
              "state",getattr(getattr(obs,"state",None),"name",None),flush=True)
        if obs.state==GameState.WIN:
            A.event("WIN",step=i+1); break
        if obs.state==GameState.GAME_OVER:
            A.gameovers+=1; A.event("GAME_OVER",step=i+1,count=A.gameovers)
            if A.gameovers>=4: break
            obs=env.reset()
            if obs is None: break
            grid=latest_grid(obs)
            # Retention test: causal geometry survives; local trajectory does not.
            A.reset_episode(grid,keep_compiled=True)

    result=A.result()
    result.update({"game":args.game,"seed":args.seed,
                   "final_levels_completed":int(getattr(obs,"levels_completed",0)) if obs else None,
                   "final_state":getattr(getattr(obs,"state",None),"name",None) if obs else None,
                   "win_levels":int(getattr(obs,"win_levels",0)) if obs else None})
    try:
        sc=arc.close_scorecard()
        if sc is not None: result["scorecard"]=sc.model_dump(mode="json") if hasattr(sc,"model_dump") else str(sc)
    except Exception as e: result["scorecard_error"]=repr(e)
    Path(args.out).write_text(json.dumps(result,indent=2,default=str))
    print("RESULT",json.dumps({k:v for k,v in result.items() if k not in ("records","events","scorecard","motion_evidence")},sort_keys=True),flush=True)
    print("OUTPUT",args.out,flush=True)

if __name__=="__main__": main()
