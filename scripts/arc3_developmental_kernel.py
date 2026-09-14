#!/usr/bin/env python3
"""
ARC-AGI-3 observation-only developmental kernel, v2.

Constitution:
- begin from public frames + public legal actions only;
- infer a controllable visual carrier from intervention-linked motion;
- treat that carrier/position quotient as the active executable state when warranted;
- keep a fallback perceptual frontier for unresolved cases;
- plan toward unresolved structural candidates without reading game implementation;
- retain causal action->displacement laws only after repeated agreement;
- revoke blocked/failed transitions locally.

This is an experiment, not a claimed general ARC-3 solver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import arc_agi
from arcengine import GameState


def latest_grid(obs: Any) -> np.ndarray:
    frames = getattr(obs, "frame", None)
    if frames is None:
        raise RuntimeError("observation has no frame")
    arr = np.asarray(frames[-1] if isinstance(frames, (list, tuple)) else frames)
    arr = np.squeeze(arr)
    if arr.ndim != 2:
        raise RuntimeError(f"expected 2D frame, got {arr.shape}")
    return arr.astype(np.int16, copy=False)


@dataclass(frozen=True)
class Comp:
    key: str
    area: int
    cy: float
    cx: float
    y0: int
    x0: int
    y1: int
    x1: int
    dominant: int
    palette: tuple[int, ...]


def components(grid: np.ndarray, min_area: int = 3) -> list[Comp]:
    """Generic foreground components: background := modal colour."""
    h, w = grid.shape
    vals, counts = np.unique(grid, return_counts=True)
    bg = int(vals[np.argmax(counts)])
    fg = grid != bg
    seen = np.zeros((h, w), dtype=bool)
    out: list[Comp] = []
    for y in range(h):
        for x in range(w):
            if seen[y, x] or not fg[y, x]:
                continue
            stack=[(y,x)]; seen[y,x]=True; pts=[]
            while stack:
                yy,xx=stack.pop(); pts.append((yy,xx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<h and 0<=nx<w and not seen[ny,nx] and fg[ny,nx]:
                        seen[ny,nx]=True; stack.append((ny,nx))
            if len(pts) < min_area:
                continue
            ys=np.array([p[0] for p in pts]); xs=np.array([p[1] for p in pts])
            y0,y1,x0,x1=int(ys.min()),int(ys.max()),int(xs.min()),int(xs.max())
            # Skip huge frame-sized structures, but keep normal walls/objects.
            if (y1-y0+1) > 0.95*h and (x1-x0+1) > 0.95*w:
                continue
            patch = np.full((y1-y0+1, x1-x0+1), -99, dtype=np.int16)
            colors=[]
            for yy,xx in pts:
                patch[yy-y0,xx-x0]=grid[yy,xx]
                colors.append(int(grid[yy,xx]))
            cvals, ccnts = np.unique(np.array(colors), return_counts=True)
            dom = int(cvals[np.argmax(ccnts)])
            pal = tuple(sorted(int(v) for v in cvals))
            # Translation-invariant exact visual key.
            key = hashlib.sha1(patch.tobytes()).hexdigest()[:14]
            out.append(Comp(key,len(pts),float(ys.mean()),float(xs.mean()),y0,x0,y1,x1,dom,pal))
    return out


def match_motion(prev: list[Comp], nxt: list[Comp]) -> list[tuple[Comp,Comp,tuple[int,int]]]:
    """Match same visual component by nearest position and return nonzero displacements."""
    by0=defaultdict(list); by1=defaultdict(list)
    for c in prev: by0[c.key].append(c)
    for c in nxt: by1[c.key].append(c)
    moved=[]
    for k in set(by0) & set(by1):
        a=by0[k][:]; b=by1[k][:]
        used=set()
        for c0 in a:
            choices=[(abs(c1.cy-c0.cy)+abs(c1.cx-c0.cx),j,c1)
                     for j,c1 in enumerate(b) if j not in used]
            if not choices: continue
            _,j,c1=min(choices)
            used.add(j)
            dy=int(round(c1.cy-c0.cy)); dx=int(round(c1.cx-c0.cx))
            if dy or dx:
                moved.append((c0,c1,(dy,dx)))
    return moved


def coarse_frame_sig(grid: np.ndarray) -> str:
    # Deliberately coarse fallback: 8x8 block histograms quantized to suppress tiny HUD changes.
    vals=np.clip(grid,0,15)
    feat=[]
    for y in range(0,grid.shape[0],8):
        for x in range(0,grid.shape[1],8):
            b=vals[y:y+8,x:x+8].ravel()
            feat.extend((np.bincount(b,minlength=16)//4).tolist())
    return hashlib.sha1(np.asarray(feat,dtype=np.int16).tobytes()).hexdigest()[:16]


class Kernel:
    def __init__(self, seed:int=0):
        self.rng=random.Random(seed)
        self.events=[]
        self.records=[]
        self.motion_evidence=defaultdict(lambda: defaultdict(Counter))  # compkey -> action -> vector counts
        self.control_key: str|None=None
        self.action_vectors: dict[str,tuple[int,int]]={}
        self.current_pos: tuple[int,int]|None=None
        self.prev_pos: tuple[int,int]|None=None
        self.pos_action_outcomes=defaultdict(Counter)  # (pos,action)->nextpos counts
        self.blocked=set()
        self.tried_actions=defaultdict(set)
        self.visited_pos=Counter()
        self.target_fail=set()
        self.current_target: tuple[int,int]|None=None
        self.current_level=0
        self.max_level=0
        self.phase="DISCOVER_CONTROL"
        self.action_counts=Counter()
        self.gameovers=0
        self.prev_components: list[Comp]|None=None

    def event(self,kind:str,**kw):
        e={"t":len(self.records),"kind":kind,**kw}
        self.events.append(e)
        print("EVENT",json.dumps(e,sort_keys=True),flush=True)

    def infer_control(self):
        best=None
        for key, amap in self.motion_evidence.items():
            action_support=0; consistent=0; vectors=set()
            for an,cnt in amap.items():
                if not cnt: continue
                vec,n=cnt.most_common(1)[0]
                if n>=1:
                    action_support+=1; consistent+=n; vectors.add(vec)
            # Prefer components that move under several actions with action-specific vectors.
            score=(len(vectors)>=2, action_support, consistent)
            if best is None or score>best[0]:
                best=(score,key)
        if best and best[0][0] and best[0][1]>=2:
            key=best[1]
            if key!=self.control_key:
                self.control_key=key
                self.phase="CONTROL_MODEL"
                self.event("CONTROLLED_CARRIER_BIRTH",carrier=key,score=best[0])
            amap=self.motion_evidence[key]
            vecs={}
            for an,cnt in amap.items():
                if cnt:
                    vec,n=cnt.most_common(1)[0]
                    if n>=1:
                        vecs[an]=vec
            old=dict(self.action_vectors)
            self.action_vectors=vecs
            if old!=vecs:
                self.event("ACTION_GEOMETRY_UPDATE",vectors={k:list(v) for k,v in vecs.items()})

    def locate_control(self, comps:list[Comp]) -> tuple[int,int]|None:
        if self.control_key:
            cs=[c for c in comps if c.key==self.control_key]
            if cs:
                if self.current_pos is None:
                    c=cs[0]
                else:
                    c=min(cs,key=lambda z:abs(z.cy-self.current_pos[0])+abs(z.cx-self.current_pos[1]))
                return (int(round(c.cy)),int(round(c.cx)))
        return None

    def update_after(self, prev_grid, grid, action_name, obs):
        prev_comps=self.prev_components if self.prev_components is not None else components(prev_grid)
        comps=components(grid)
        moved=match_motion(prev_comps,comps)
        for c0,c1,vec in moved:
            # Ignore implausibly huge jumps for control induction; those are more likely HUD/scene changes.
            if abs(vec[0])+abs(vec[1]) <= 24:
                self.motion_evidence[c0.key][action_name][vec]+=1
        self.infer_control()

        before=self.current_pos
        now=self.locate_control(comps)

        # If the exact carrier key changed, use an already-warranted action vector to reacquire
        # the nearest plausible component near the expected destination. This is exaptation, not
        # a claim of persistent object identity.
        if now is None and before is not None and action_name in self.action_vectors:
            dy,dx=self.action_vectors[action_name]
            ey,ex=before[0]+dy,before[1]+dx
            cands=[c for c in comps if 2<=c.area<=200]
            if cands:
                c=min(cands,key=lambda z:abs(z.cy-ey)+abs(z.cx-ex))
                if abs(c.cy-ey)+abs(c.cx-ex)<=6:
                    old=self.control_key
                    self.control_key=c.key
                    now=(int(round(c.cy)),int(round(c.cx)))
                    self.event("CARRIER_REQUALIFY",old=old,new=c.key,expected=[ey,ex],observed=list(now))

        self.prev_pos=before
        self.current_pos=now
        if now is not None:
            self.visited_pos[now]+=1
        if before is not None and now is not None:
            self.pos_action_outcomes[(before,action_name)][now]+=1
            self.tried_actions[before].add(action_name)
            if now==before:
                self.blocked.add((before,action_name))
            else:
                # Observed displacement gets authority even if visual key changed.
                vec=(now[0]-before[0],now[1]-before[1])
                self.motion_evidence[self.control_key][action_name][vec]+=1
                self.infer_control()

        lvl=int(getattr(obs,"levels_completed",0))
        if lvl>self.max_level:
            self.event("VERIFIED_PROGRESS",from_level=self.max_level,to_level=lvl,action=action_name)
            self.max_level=lvl
        if lvl!=self.current_level:
            self.event("LEVEL_BOUNDARY",old=self.current_level,new=lvl)
            self.current_level=lvl
            self.reset_level_model(keep_motion=True)

        self.prev_components=comps
        rec={
            "i":len(self.records),"action":action_name,
            "pixel_delta":int(np.count_nonzero(grid!=prev_grid)),
            "moved_components":[{"key":a.key,"vec":list(v),"area":a.area} for a,b,v in moved[:20]],
            "control_key":self.control_key,
            "control_pos":list(self.current_pos) if self.current_pos else None,
            "vectors":{k:list(v) for k,v in self.action_vectors.items()},
            "level":lvl,
            "state":getattr(getattr(obs,"state",None),"name",str(getattr(obs,"state",None))),
            "phase":self.phase,
        }
        self.records.append(rec)

    def reset_level_model(self,keep_motion=True):
        self.current_pos=None; self.prev_pos=None
        self.pos_action_outcomes.clear(); self.blocked.clear(); self.tried_actions.clear()
        self.visited_pos.clear(); self.target_fail.clear(); self.current_target=None
        self.prev_components=None
        if not keep_motion:
            self.motion_evidence.clear(); self.control_key=None; self.action_vectors.clear(); self.phase="DISCOVER_CONTROL"

    def candidate_targets(self, comps:list[Comp]) -> list[tuple[float,tuple[int,int],str,int]]:
        if self.current_pos is None: return []
        out=[]
        for c in comps:
            if c.key==self.control_key: continue
            if not (3<=c.area<=400): continue
            # Exclude long wall-like components.
            hh=c.y1-c.y0+1; ww=c.x1-c.x0+1
            if max(hh,ww)>36 and min(hh,ww)<=3: continue
            p=(int(round(c.cy)),int(round(c.cx)))
            if p in self.target_fail: continue
            d=abs(p[0]-self.current_pos[0])+abs(p[1]-self.current_pos[1])
            # Small distinct components get preference, but geometry remains generic.
            score=d + 0.03*c.area
            out.append((score,p,c.key,c.area))
        return sorted(out)

    def choose(self, actions:list[Any], grid:np.ndarray):
        names=[a.name for a in actions]
        comps=components(grid)
        # Before a causal carrier exists: balanced interventions.
        if self.control_key is None or self.current_pos is None:
            a=min(actions,key=lambda x:(self.action_counts[x.name],x.name))
            return a,{"mode":"DISCOVER_CONTROL","reason":"balanced intervention to identify action-linked visual carrier"}

        pos=self.current_pos

        # Ensure every action is tested at least once from the current carrier position when affordable.
        unseen=[a for a in actions if a.name not in self.tried_actions[pos]]
        if unseen and sum(self.action_counts.values())<24:
            a=min(unseen,key=lambda x:(self.action_counts[x.name],x.name))
            return a,{"mode":"LOCAL_CAUSAL_PROBE","reason":"untried intervention at current derived carrier state"}

        # Choose/refresh a structural candidate target.
        targets=self.candidate_targets(comps)
        if self.current_target is None and targets:
            self.current_target=targets[0][1]
            self.event("TARGET_HYPOTHESIS",target=list(self.current_target),source="generic visual component")
        if self.current_target is not None:
            if abs(self.current_target[0]-pos[0])+abs(self.current_target[1]-pos[1])<=2:
                self.target_fail.add(self.current_target)
                self.event("TARGET_REACHED_WITHOUT_PROGRESS",target=list(self.current_target))
                self.current_target=None
                targets=self.candidate_targets(comps)
                if targets:
                    self.current_target=targets[0][1]
                    self.event("TARGET_HYPOTHESIS",target=list(self.current_target),source="next unresolved component")

        # Goal-directed movement using only action vectors learned by intervention.
        movement=[]
        if self.current_target is not None:
            ty,tx=self.current_target
            d0=abs(ty-pos[0])+abs(tx-pos[1])
            for a in actions:
                vec=self.action_vectors.get(a.name)
                if vec is None or (pos,a.name) in self.blocked: continue
                np0=(pos[0]+vec[0],pos[1]+vec[1])
                d1=abs(ty-np0[0])+abs(tx-np0[1])
                movement.append((d1-d0,self.visited_pos[np0],self.action_counts[a.name],a,np0))
            if movement:
                movement.sort(key=lambda z:(z[0],z[1],z[2],z[3].name))
                gain,_,_,a,np0=movement[0]
                if gain<0:
                    return a,{"mode":"PLAN_TO_HYPOTHESIS","target":list(self.current_target),
                              "predicted_next":list(np0),"reason":"learned action vector reduces distance to unresolved structure"}

        # Frontier exploration in derived position space.
        opts=[]
        for a in actions:
            vec=self.action_vectors.get(a.name)
            if vec is None: continue
            if (pos,a.name) in self.blocked: continue
            np0=(pos[0]+vec[0],pos[1]+vec[1])
            opts.append((self.visited_pos[np0], self.action_counts[a.name], a, np0))
        if opts:
            _,_,a,np0=min(opts,key=lambda z:(z[0],z[1],z[2].name))
            return a,{"mode":"POSITION_FRONTIER","predicted_next":list(np0),
                      "reason":"least-visited consequence-derived carrier position"}

        # If movement model cannot make progress, probe the least-used action and keep UNKNOWN explicit.
        a=min(actions,key=lambda x:(self.action_counts[x.name],x.name))
        return a,{"mode":"UNKNOWN_SEARCH","reason":"no currently warranted progress edge"}

    def summary(self):
        return {
            "actions":len(self.records),"max_levels_completed":self.max_level,
            "control_key":self.control_key,"action_vectors":{k:list(v) for k,v in self.action_vectors.items()},
            "phase":self.phase,"gameovers":self.gameovers,"action_counts":dict(self.action_counts),
            "events":self.events,"records":self.records,
        }


def action_data(action,grid,rng):
    if not action.is_complex(): return {}
    comps=components(grid)
    if comps:
        c=min(comps,key=lambda z:z.area)
        return {"x":int(round(c.cx)),"y":int(round(c.cy))}
    return {"x":grid.shape[1]//2,"y":grid.shape[0]//2}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game",default="ls20")
    ap.add_argument("--max-actions",type=int,default=400)
    ap.add_argument("--seed",type=int,default=0)
    ap.add_argument("--out",default="arc3_developmental_result.json")
    args=ap.parse_args()

    arc=arc_agi.Arcade()
    env=arc.make(args.game,save_recording=True,include_frame_data=True,render_mode=None)
    if env is None: raise SystemExit("arc.make returned None")
    obs=env.reset()
    if obs is None: raise SystemExit("reset returned None")
    grid=latest_grid(obs)
    K=Kernel(args.seed)
    K.current_level=int(getattr(obs,"levels_completed",0))
    K.max_level=K.current_level
    K.prev_components=components(grid)

    print("START",args.game,"actions",[a.name for a in env.action_space],
          "levels",getattr(obs,"levels_completed",None),"win_levels",getattr(obs,"win_levels",None),flush=True)

    for i in range(args.max_actions):
        acts=list(env.action_space)
        if not acts: break
        a,reason=K.choose(acts,grid)
        K.action_counts[a.name]+=1
        data=action_data(a,grid,K.rng)
        prev=grid
        obs=env.step(a,data=data,reasoning=reason)
        if obs is None:
            K.event("NULL_OBSERVATION",action=a.name); continue
        grid=latest_grid(obs)
        K.update_after(prev,grid,a.name,obs)
        print("STEP",i+1,a.name,reason["mode"],"delta",K.records[-1]["pixel_delta"],
              "control",K.current_pos,"vectors",K.action_vectors,
              "level",getattr(obs,"levels_completed",None),
              "state",getattr(getattr(obs,"state",None),"name",None),flush=True)

        if obs.state==GameState.WIN:
            K.event("WIN",step=i+1); break
        if obs.state==GameState.GAME_OVER:
            K.gameovers+=1
            K.event("GAME_OVER",step=i+1,count=K.gameovers)
            if K.gameovers>=4: break
            obs=env.reset()
            if obs is None: break
            grid=latest_grid(obs)
            K.reset_level_model(keep_motion=False)
            K.prev_components=components(grid)

    result=K.summary()
    result.update({"game":args.game,"seed":args.seed,
                   "final_levels_completed":int(getattr(obs,"levels_completed",0)) if obs else None,
                   "final_state":getattr(getattr(obs,"state",None),"name",None) if obs else None,
                   "win_levels":int(getattr(obs,"win_levels",0)) if obs else None})
    try:
        sc=arc.close_scorecard()
        if sc is not None:
            result["scorecard"]=sc.model_dump(mode="json") if hasattr(sc,"model_dump") else str(sc)
    except Exception as e:
        result["scorecard_error"]=repr(e)
    Path(args.out).write_text(json.dumps(result,indent=2,default=str))
    print("RESULT",json.dumps({k:v for k,v in result.items() if k not in ("records","events","scorecard")},sort_keys=True),flush=True)
    print("OUTPUT",args.out,flush=True)


if __name__=="__main__":
    main()
