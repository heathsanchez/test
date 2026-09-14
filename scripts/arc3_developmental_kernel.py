#!/usr/bin/env python3
"""
ARC-AGI-3 developmental kernel v4: factor common consequence before ontology.

No game implementation/source, fixed coordinates, palette semantics, stored route,
or level-number-specific behavior.

Frozen residuals from v1-v3:
  v1: raw visual state over-split motion.
  v2: persistent object identity could not be established.
  v3: raw change was dominated by an invariant 52-pixel consequence.

V4 therefore starts with controlled interventions from the same reset state.
It quotients the change support common to every legal action (a nuisance/common
consequence channel), then develops reference, motion, and an executable graph
only from the remaining action-dependent consequence.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any
import numpy as np
import arc_agi
from arcengine import GameState


def grid(obs):
    f=getattr(obs,"frame",None)
    if f is None: raise RuntimeError("no frame")
    a=np.asarray(f[-1] if isinstance(f,(list,tuple)) else f)
    a=np.squeeze(a)
    if a.ndim!=2: raise RuntimeError(a.shape)
    return a.astype(np.int16,copy=False)


def blobs(mask,min_n=2):
    h,w=mask.shape; seen=np.zeros_like(mask,bool); out=[]
    for y in range(h):
        for x in range(w):
            if seen[y,x] or not mask[y,x]: continue
            st=[(y,x)]; seen[y,x]=1; pts=[]
            while st:
                yy,xx=st.pop(); pts.append((yy,xx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1; st.append((ny,nx))
            if len(pts)>=min_n:
                ys=np.array([p[0] for p in pts]); xs=np.array([p[1] for p in pts])
                out.append(dict(n=len(pts),cy=float(ys.mean()),cx=float(xs.mean()),
                                y0=int(ys.min()),x0=int(xs.min()),y1=int(ys.max()),x1=int(xs.max())))
    return out


def bbox_mask(shape,bs,pad=3):
    m=np.zeros(shape,bool)
    for b in bs:
        y0=max(0,b["y0"]-pad); y1=min(shape[0],b["y1"]+pad+1)
        x0=max(0,b["x0"]-pad); x1=min(shape[1],b["x1"]+pad+1)
        m[y0:y1,x0:x1]=1
    return m


def filtered_diff(a,b,nuis):
    d=a!=b
    if nuis is not None: d=d & ~nuis
    return d


def scene_sig(g,nuis,pos=None):
    a=g.copy()
    if nuis is not None: a[nuis]=-1
    if pos is not None:
        y,x=pos; a[max(0,y-4):min(a.shape[0],y+5),max(0,x-4):min(a.shape[1],x+5)]=-1
    q=np.clip(a,0,15); feat=[]
    for y in range(0,a.shape[0],8):
        for x in range(0,a.shape[1],8):
            feat.extend((np.bincount(q[y:y+8,x:x+8].ravel(),minlength=16)//4).tolist())
    return hashlib.sha1(np.asarray(feat,dtype=np.int16).tobytes()).hexdigest()[:14]


def infer_motion_from_change(d,pos=None):
    """Derive displacement from change components, using existing reference only to orient it."""
    bs=blobs(d,2)
    cand=[]
    if pos is not None and len(bs)>=2:
        old=min(bs,key=lambda b:abs(b["cy"]-pos[0])+abs(b["cx"]-pos[1]))
        for new in bs:
            if new is old: continue
            ratio=max(old["n"],new["n"])/max(1,min(old["n"],new["n"]))
            if ratio>3: continue
            dy=int(round(new["cy"]-old["cy"])); dx=int(round(new["cx"]-old["cx"]))
            dist=abs(dy)+abs(dx)
            if 0<dist<=24:
                cand.append(((abs(old["n"]-new["n"]),dist),(dy,dx),
                             (int(round(old["cy"])),int(round(old["cx"]))),
                             (int(round(new["cy"])),int(round(new["cx"]))),
                             old["n"],new["n"]))
    cand.sort(key=lambda z:z[0])
    return cand,bs


class Agent:
    def __init__(self,nuisance,bootstrap_unique,seed=0):
        self.nuisance=nuisance
        self.bootstrap_unique=bootstrap_unique
        self.bootstrap_order=sorted(bootstrap_unique,key=lambda a:(-bootstrap_unique[a],a))
        self.rng=random.Random(seed)
        self.events=[]; self.records=[]; self.action_counts=Counter()
        self.motion=defaultdict(Counter); self.vectors={}
        self.pos=None; self.scene=None
        self.graph=defaultdict(Counter); self.tried=defaultdict(set); self.blocked=set(); self.visits=Counter()
        self.level=0; self.max_level=0; self.gameovers=0; self.phase="COMMON_CONSEQUENCE_QUOTIENTED"

    def ev(self,k,**kw):
        e={"t":len(self.records),"kind":k,**kw}; self.events.append(e)
        print("EVENT",json.dumps(e,sort_keys=True),flush=True)

    def compile(self):
        old=dict(self.vectors)
        for a,c in self.motion.items():
            if c:
                v,n=c.most_common(1)[0]
                if n>=1: self.vectors[a]=v
        if old!=self.vectors:
            self.phase="CAUSAL_GEOMETRY"
            self.ev("ACTION_GEOMETRY_UPDATE",vectors={k:list(v) for k,v in self.vectors.items()},
                    evidence={k:{str(list(v)):n for v,n in c.items()} for k,c in self.motion.items()})

    def start_frame(self,g,keep_graph=True):
        self.pos=None; self.scene=scene_sig(g,self.nuisance,None)
        if not keep_graph:
            self.graph.clear(); self.tried.clear(); self.blocked.clear(); self.visits.clear()

    def update(self,prev,g,action,obs):
        d=filtered_diff(prev,g,self.nuisance)
        bs=blobs(d,2)
        oldpos=self.pos
        mc,_=infer_motion_from_change(d,self.pos)
        chosen=mc[0] if mc else None

        if self.pos is None and bs:
            # A localized action-specific change is enough to establish a provisional reference,
            # without calling it an object.
            local=[b for b in bs if b["n"]<=200 and (b["y1"]-b["y0"]+1)<=24 and (b["x1"]-b["x0"]+1)<=24]
            if local:
                b=min(local,key=lambda z:(z["n"],z["y0"],z["x0"]))
                self.pos=(int(round(b["cy"])),int(round(b["cx"])))
                self.phase="REFERENCE_FROM_ACTION_DIFFERENCE"
                self.ev("REFERENCE_GENESIS",action=action,pos=list(self.pos),support=b["n"])
        elif chosen:
            _,v,p0,p1,n0,n1=chosen
            # Require the inferred old support to be near the current reference.
            if abs(p0[0]-self.pos[0])+abs(p0[1]-self.pos[1])<=8:
                self.motion[action][v]+=1; self.compile(); self.pos=p1

        # If a compiled action predicts displacement but no motion candidate occurred, it is blocked here.
        if oldpos is not None and self.pos==oldpos and action in self.vectors:
            self.blocked.add((self.scene,oldpos,action))

        newscene=scene_sig(g,self.nuisance,self.pos)
        if oldpos is not None and self.pos is not None:
            node=(self.scene,oldpos); out=(newscene,self.pos)
            self.tried[node].add(action); self.graph[(self.scene,oldpos,action)][out]+=1
            self.visits[out]+=1
            if newscene!=self.scene:
                self.ev("STRUCTURAL_STATE_SPLIT",old_scene=self.scene,new_scene=newscene,
                        pos=list(self.pos),action=action)
        self.scene=newscene

        lvl=int(getattr(obs,"levels_completed",0))
        if lvl>self.max_level:
            self.ev("VERIFIED_PROGRESS",from_level=self.max_level,to_level=lvl,action=action); self.max_level=lvl
        if lvl!=self.level:
            self.ev("LEVEL_BOUNDARY",old=self.level,new=lvl); self.level=lvl
            # Transfer only causal action geometry; local graph belongs to prior level.
            self.graph.clear(); self.tried.clear(); self.blocked.clear(); self.visits.clear()
            self.pos=None; self.scene=scene_sig(g,self.nuisance,None)

        self.records.append(dict(i=len(self.records),action=action,
             raw_delta=int(np.count_nonzero(prev!=g)),filtered_delta=int(np.count_nonzero(d)),
             change_blobs=bs[:12],
             motion_candidates=[{"v":list(c[1]),"old":list(c[2]),"new":list(c[3]),"n":[c[4],c[5]]} for c in mc[:6]],
             pos=list(self.pos) if self.pos else None,scene=self.scene,
             vectors={k:list(v) for k,v in self.vectors.items()},phase=self.phase,
             level=lvl,state=getattr(getattr(obs,"state",None),"name",str(getattr(obs,"state",None)))))

    def choose(self,actions):
        # If no reference yet, choose the intervention with largest action-specific consequence.
        if self.pos is None:
            for an in self.bootstrap_order:
                for a in actions:
                    if a.name==an and self.bootstrap_unique[an]>0:
                        return a,{"mode":"REFERENCE_PROBE","reason":"largest consequence after common-channel quotient"}
            a=min(actions,key=lambda z:(self.action_counts[z.name],z.name))
            return a,{"mode":"UNKNOWN_PROBE","reason":"no action-specific consequence identified"}

        node=(self.scene,self.pos)
        unseen=[a for a in actions if a.name not in self.tried[node]]
        if unseen:
            # Unknown action geometry before known geometry; then lower use.
            a=min(unseen,key=lambda z:(z.name in self.vectors,self.action_counts[z.name],z.name))
            return a,{"mode":"CAUSAL_PROBE","state":[self.scene,list(self.pos)],
                      "reason":"untried intervention at warranted state"}

        # Route to closest known state with an unresolved action.
        adj=defaultdict(list)
        for (sc,p,an),outs in self.graph.items():
            if len(outs)==1:
                out=next(iter(outs))
                adj[(sc,p)].append((an,out))
        q=deque([(node,[])]); seen={node}
        while q:
            n,path=q.popleft()
            if n!=node and len(self.tried[n])<len(actions) and path:
                an=path[0]
                a=next(x for x in actions if x.name==an)
                return a,{"mode":"ROUTE_TO_FRONTIER","target":[n[0],list(n[1])]}
            for an,n2 in adj.get(n,[]):
                if n2 not in seen:
                    seen.add(n2); q.append((n2,path+[an]))

        # Predictively expand the least-visited position under compiled action geometry.
        opts=[]
        for a in actions:
            v=self.vectors.get(a.name)
            if v is None or (self.scene,self.pos,a.name) in self.blocked: continue
            p2=(self.pos[0]+v[0],self.pos[1]+v[1])
            opts.append((self.visits[(self.scene,p2)],self.action_counts[a.name],a,p2))
        if opts:
            _,_,a,p2=min(opts,key=lambda z:(z[0],z[1],z[2].name))
            return a,{"mode":"POSITION_FRONTIER","predicted_next":list(p2),
                      "reason":"least-visited continuation under compiled geometry"}

        a=min(actions,key=lambda z:(self.action_counts[z.name],z.name))
        return a,{"mode":"UNKNOWN_SEARCH","reason":"no warranted progress continuation"}

    def result(self):
        return dict(actions=len(self.records),max_levels_completed=self.max_level,
            vectors={k:list(v) for k,v in self.vectors.items()},phase=self.phase,gameovers=self.gameovers,
            bootstrap_unique=self.bootstrap_unique,action_counts=dict(self.action_counts),
            nuisance_pixels=int(self.nuisance.sum()) if self.nuisance is not None else 0,
            events=self.events,records=self.records)


def bootstrap(env):
    actions=list(env.action_space)
    diffs={}; raw={}
    for a in actions:
        o0=env.reset(); g0=grid(o0)
        o1=env.step(a,data={},reasoning={"mode":"FROZEN_ONE_STEP_INTERVENTION"})
        g1=grid(o1); d=g0!=g1
        diffs[a.name]=d; raw[a.name]=int(d.sum())
    common=np.logical_and.reduce([diffs[a.name] for a in actions])
    common_bs=blobs(common,1)
    nuisance=bbox_mask(common.shape,common_bs,pad=4) if common_bs else np.zeros(common.shape,bool)
    unique={a.name:int((diffs[a.name]&~nuisance).sum()) for a in actions}
    return nuisance,raw,unique,common_bs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game",default="ls20"); ap.add_argument("--max-actions",type=int,default=400)
    ap.add_argument("--seed",type=int,default=0); ap.add_argument("--out",default="arc3_developmental_result.json")
    args=ap.parse_args()

    arc=arc_agi.Arcade()
    env=arc.make(args.game,save_recording=True,include_frame_data=True,render_mode=None)
    if env is None: raise SystemExit("make failed")

    nuisance,raw,unique,common_bs=bootstrap(env)
    print("BOOTSTRAP",json.dumps({"raw_delta":raw,"unique_delta":unique,
          "common_pixels":int(np.logical_and.reduce([(grid(env.reset())!=grid(env.reset())) for _ in []]).sum()) if False else None,
          "nuisance_pixels":int(nuisance.sum()),"common_blobs":common_bs},default=str),flush=True)

    obs=env.reset(); g=grid(obs)
    A=Agent(nuisance,unique,args.seed); A.level=int(getattr(obs,"levels_completed",0)); A.max_level=A.level
    A.start_frame(g,keep_graph=False)
    A.ev("COMMON_CONSEQUENCE_QUOTIENT",raw_delta=raw,unique_delta=unique,
         nuisance_pixels=int(nuisance.sum()),common_blobs=common_bs)

    print("START",args.game,"actions",[a.name for a in env.action_space],
          "levels",getattr(obs,"levels_completed",None),"win_levels",getattr(obs,"win_levels",None),flush=True)

    for i in range(args.max_actions):
        acts=list(env.action_space)
        if not acts: break
        a,reason=A.choose(acts); A.action_counts[a.name]+=1
        prev=g
        obs=env.step(a,data={},reasoning=reason)
        if obs is None: A.ev("NULL_OBSERVATION",action=a.name); continue
        g=grid(obs); A.update(prev,g,a.name,obs)
        r=A.records[-1]
        print("STEP",i+1,a.name,reason["mode"],"raw",r["raw_delta"],"filtered",r["filtered_delta"],
              "pos",A.pos,"vectors",A.vectors,"level",getattr(obs,"levels_completed",None),
              "state",getattr(getattr(obs,"state",None),"name",None),flush=True)
        if obs.state==GameState.WIN:
            A.ev("WIN",step=i+1); break
        if obs.state==GameState.GAME_OVER:
            A.gameovers+=1; A.ev("GAME_OVER",step=i+1,count=A.gameovers)
            if A.gameovers>=4: break
            obs=env.reset()
            if obs is None: break
            g=grid(obs)
            # Retain verified causal geometry and local graph across identical reset world.
            A.start_frame(g,keep_graph=True)

    result=A.result()
    result.update(game=args.game,seed=args.seed,
                  final_levels_completed=int(getattr(obs,"levels_completed",0)) if obs else None,
                  final_state=getattr(getattr(obs,"state",None),"name",None) if obs else None,
                  win_levels=int(getattr(obs,"win_levels",0)) if obs else None)
    try:
        sc=arc.close_scorecard()
        if sc is not None: result["scorecard"]=sc.model_dump(mode="json") if hasattr(sc,"model_dump") else str(sc)
    except Exception as e: result["scorecard_error"]=repr(e)
    Path(args.out).write_text(json.dumps(result,indent=2,default=str))
    print("RESULT",json.dumps({k:v for k,v in result.items() if k not in ("records","events","scorecard")},sort_keys=True),flush=True)
    print("OUTPUT",args.out,flush=True)

if __name__=="__main__": main()
