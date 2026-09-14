#!/usr/bin/env python3
"""
ARC-AGI-3 developmental kernel v5: minimal active ontology.

No game source, palette meanings, fixed coordinates, stored path, or level logic.

Developmental lineage frozen by prior runs:
 v1 raw frames -> over-splitting;
 v2 persistent object identity -> unsupported;
 v3 raw change -> dominated by common action consequence;
 v4 factor common consequence -> reference + 4-axis causal geometry emerged,
      but full scene hashes over-split every encounter.

V5 contracts the active state to the least currently warranted executable form:
    (consequence-earned position, intervention)
Rich pixels remain provenance only.  A scene distinction is promoted only if
the same active state/action produces incompatible consequences.
"""
from __future__ import annotations
import argparse, json, random
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any
import numpy as np
import arc_agi
from arcengine import GameState


def frame(obs):
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


def expand_common(common,pad=4):
    out=np.zeros_like(common,bool)
    for b in blobs(common,1):
        out[max(0,b["y0"]-pad):min(out.shape[0],b["y1"]+pad+1),
            max(0,b["x0"]-pad):min(out.shape[1],b["x1"]+pad+1)]=1
    return out


def fdiff(a,b,nuis):
    d=a!=b
    return d if nuis is None else d & ~nuis


def local_reference(d):
    bs=[b for b in blobs(d,2) if b["n"]<=200 and b["y1"]-b["y0"]<24 and b["x1"]-b["x0"]<24]
    if not bs: return None
    # Minimal localized consequence is preferred over a broad scene change.
    b=min(bs,key=lambda z:(z["n"],z["y0"],z["x0"]))
    return (int(round(b["cy"])),int(round(b["cx"]))),b


def motion_from_reference(d,ref):
    bs=blobs(d,2)
    if not bs: return None,bs
    # First try old/new support pair with old nearest known reference.
    old=min(bs,key=lambda b:abs(b["cy"]-ref[0])+abs(b["cx"]-ref[1]))
    cand=[]
    for n in bs:
        if n is old: continue
        ratio=max(old["n"],n["n"])/max(1,min(old["n"],n["n"]))
        if ratio>3: continue
        p1=(int(round(n["cy"])),int(round(n["cx"])))
        v=(p1[0]-ref[0],p1[1]-ref[1])
        if 0<abs(v[0])+abs(v[1])<=24:
            cand.append((abs(old["n"]-n["n"]),abs(v[0])+abs(v[1]),v,p1,old,n))
    if cand:
        _,_,v,p1,o,n=min(cand,key=lambda z:(z[0],z[1]))
        return dict(v=v,new=p1,old_n=o["n"],new_n=n["n"],mode="paired_support"),bs
    # If only the destination support is cleanly visible, allow the nearest non-reference blob.
    far=[]
    for n in bs:
        p1=(int(round(n["cy"])),int(round(n["cx"])))
        v=(p1[0]-ref[0],p1[1]-ref[1]); dist=abs(v[0])+abs(v[1])
        if 2<=dist<=24 and n["n"]<=200:
            far.append((dist,n["n"],v,p1,n))
    if far:
        _,_,v,p1,n=min(far,key=lambda z:(z[0],z[1]))
        return dict(v=v,new=p1,old_n=None,new_n=n["n"],mode="destination_support"),bs
    return None,bs


def bootstrap(env):
    acts=list(env.action_space)
    one={}
    baselines={}
    probe_arrays={}
    for a in acts:
        o0=env.reset(); g0=frame(o0)
        o1=env.step(a,data={},reasoning={"mode":"ONE_STEP_INTERVENTION"})
        g1=frame(o1)
        one[a.name]=(g0,g1,g0!=g1)
        probe_arrays["reset_"+a.name]=g0
        probe_arrays["one_"+a.name]=g1
        baselines[a.name]=int(np.count_nonzero(g0!=g1))
    common=np.logical_and.reduce([one[a.name][2] for a in acts])
    nuisance=expand_common(common,pad=4)
    unique={a.name:int(np.count_nonzero(one[a.name][2]&~nuisance)) for a in acts}

    # Reference action: largest action-specific consequence; deterministic lexical tie-break.
    ref_action=min([a.name for a in acts],key=lambda n:(-unique[n],n))
    dref=one[ref_action][2]&~nuisance
    rp=local_reference(dref)
    ref_pos=rp[0] if rp else None

    vectors={}
    vector_evidence={}
    if ref_pos is not None:
        # Controlled two-step experiments: recreate the same reference state, then vary one action.
        for a in acts:
            o0=env.reset(); g0=frame(o0)
            ract=next(x for x in acts if x.name==ref_action)
            oref=env.step(ract,data={},reasoning={"mode":"REFERENCE_RECONSTRUCTION"})
            gref=frame(oref)
            o2=env.step(a,data={},reasoning={"mode":"SECOND_ORDER_INTERVENTION"})
            g2=frame(o2)
            probe_arrays["ref_"+a.name]=gref
            probe_arrays["two_"+a.name]=g2
            d=fdiff(gref,g2,nuisance)
            m,bs=motion_from_reference(d,ref_pos)
            vector_evidence[a.name]={
                "filtered_delta":int(d.sum()),
                "blobs":bs[:8],
                "motion":({**m,"v":list(m["v"]),"new":list(m["new"])} if m else None)
            }
            if m is not None:
                vectors[a.name]=tuple(m["v"])
    Path("arc3-results").mkdir(parents=True,exist_ok=True)
    np.savez_compressed("arc3-results/probes.npz",**probe_arrays,nuisance=nuisance.astype(np.uint8))
    return nuisance,baselines,unique,ref_action,ref_pos,vectors,vector_evidence


class Agent:
    def __init__(self,nuis,ref_action,ref_pos,vectors,seed=0):
        self.nuis=nuis; self.ref_action=ref_action; self.ref_pos=ref_pos
        self.vectors=dict(vectors); self.rng=random.Random(seed)
        self.pos=None; self.events=[]; self.records=[]; self.action_counts=Counter()
        self.graph=defaultdict(Counter)  # (pos,action)->pos'
        self.tried=defaultdict(set); self.blocked=set(); self.visits=Counter()
        self.consequence=defaultdict(Counter) # (pos,action)->(pos',delta_bucket,state,level_delta)
        self.level=0; self.max_level=0; self.gameovers=0; self.phase="MINIMAL_POSITION_ONTOLOGY"

    def ev(self,k,**kw):
        e={"t":len(self.records),"kind":k,**kw}; self.events.append(e)
        print("EVENT",json.dumps(e,sort_keys=True),flush=True)

    def reset(self):
        self.pos=None

    def choose(self,acts):
        if self.pos is None:
            a=next((x for x in acts if x.name==self.ref_action),None)
            if a is None: a=min(acts,key=lambda z:z.name)
            return a,{"mode":"RECONSTRUCT_REFERENCE","reason":"reuse verified reference-forming intervention"}

        unseen=[a for a in acts if a.name not in self.tried[self.pos]]
        if unseen:
            # Prioritize actions with known geometry; unknowns still get tested.
            a=min(unseen,key=lambda z:(z.name not in self.vectors,self.action_counts[z.name],z.name))
            return a,{"mode":"LOCAL_CAUSAL_PROBE","position":list(self.pos)}

        # Route through verified single-outcome graph to nearest unresolved position.
        adj=defaultdict(list)
        for (p,an),outs in self.graph.items():
            if len(outs)==1:
                p2=next(iter(outs)); adj[p].append((an,p2))
        q=deque([(self.pos,[])]); seen={self.pos}
        while q:
            p,path=q.popleft()
            if p!=self.pos and len(self.tried[p])<len(acts) and path:
                an=path[0]; a=next(x for x in acts if x.name==an)
                return a,{"mode":"ROUTE_TO_FRONTIER","target":list(p)}
            for an,p2 in adj.get(p,[]):
                if p2 not in seen:
                    seen.add(p2); q.append((p2,path+[an]))

        # If all known positions are locally closed, expand least-visited predicted continuation.
        opts=[]
        for a in acts:
            v=self.vectors.get(a.name)
            if v is None or (self.pos,a.name) in self.blocked: continue
            p2=(self.pos[0]+v[0],self.pos[1]+v[1])
            opts.append((self.visits[p2],self.action_counts[a.name],a,p2))
        if opts:
            _,_,a,p2=min(opts,key=lambda z:(z[0],z[1],z[2].name))
            return a,{"mode":"POSITION_FRONTIER","predicted_next":list(p2)}

        a=min(acts,key=lambda z:(self.action_counts[z.name],z.name))
        return a,{"mode":"UNKNOWN_SEARCH","reason":"no licensed continuation in current active ontology"}

    def update(self,prev,g,action,obs,prev_level):
        d=fdiff(prev,g,self.nuis); delta=int(d.sum())
        old=self.pos
        if self.pos is None and action==self.ref_action and self.ref_pos is not None:
            self.pos=self.ref_pos
            self.ev("REFERENCE_RECONSTRUCTED",action=action,pos=list(self.pos))
        elif self.pos is not None and action in self.vectors:
            v=self.vectors[action]
            if delta==0:
                self.blocked.add((self.pos,action))
            else:
                # Minimal executable commitment: use the intervention-derived displacement.
                self.pos=(self.pos[0]+v[0],self.pos[1]+v[1])

        lvl=int(getattr(obs,"levels_completed",0))
        state=getattr(getattr(obs,"state",None),"name",str(getattr(obs,"state",None)))
        if old is not None and self.pos is not None:
            self.tried[old].add(action); self.graph[(old,action)][self.pos]+=1; self.visits[self.pos]+=1
            bucket=min(9,delta//10)
            ck=(self.pos,bucket,state,lvl-prev_level)
            self.consequence[(old,action)][ck]+=1
            if len(self.consequence[(old,action)])>1:
                self.ev("CERTIFIED_POSITION_ONTOLOGY_INADEQUATE",position=list(old),action=action,
                        alternatives=[str(x) for x in self.consequence[(old,action)]])
        if lvl>self.max_level:
            self.ev("VERIFIED_PROGRESS",from_level=self.max_level,to_level=lvl,action=action)
            self.max_level=lvl
        if lvl!=self.level:
            self.ev("LEVEL_BOUNDARY",old=self.level,new=lvl); self.level=lvl
            # Geometry transfers; local map does not.
            self.graph.clear(); self.tried.clear(); self.blocked.clear(); self.visits.clear(); self.consequence.clear()
            self.pos=None
        self.records.append(dict(i=len(self.records),action=action,raw_delta=int(np.count_nonzero(prev!=g)),
            filtered_delta=delta,old_pos=list(old) if old else None,pos=list(self.pos) if self.pos else None,
            vectors={k:list(v) for k,v in self.vectors.items()},level=lvl,state=state,phase=self.phase))

    def result(self):
        return dict(actions=len(self.records),max_levels_completed=self.max_level,
                    vectors={k:list(v) for k,v in self.vectors.items()},phase=self.phase,
                    gameovers=self.gameovers,action_counts=dict(self.action_counts),
                    distinct_positions=len(self.visits),events=self.events,records=self.records)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game",default="ls20"); ap.add_argument("--max-actions",type=int,default=400)
    ap.add_argument("--seed",type=int,default=0); ap.add_argument("--out",default="arc3_developmental_result.json")
    args=ap.parse_args()
    arc=arc_agi.Arcade()
    env=arc.make(args.game,save_recording=True,include_frame_data=True,render_mode=None)
    if env is None: raise SystemExit("make failed")

    nuis,raw,unique,ref_action,ref_pos,vectors,ve=bootstrap(env)
    print("BOOTSTRAP",json.dumps({"raw_delta":raw,"unique_delta":unique,"nuisance_pixels":int(nuis.sum()),
          "reference_action":ref_action,"reference_pos":list(ref_pos) if ref_pos else None,
          "vectors":{k:list(v) for k,v in vectors.items()},"vector_evidence":ve},default=str),flush=True)

    obs=env.reset(); g=frame(obs)
    A=Agent(nuis,ref_action,ref_pos,vectors,args.seed)
    A.level=int(getattr(obs,"levels_completed",0)); A.max_level=A.level
    A.ev("MINIMAL_ONTOLOGY_ACTIVATED",reference_action=ref_action,
         reference_pos=list(ref_pos) if ref_pos else None,vectors={k:list(v) for k,v in vectors.items()})

    print("START",args.game,"actions",[a.name for a in env.action_space],
          "levels",getattr(obs,"levels_completed",None),"win_levels",getattr(obs,"win_levels",None),flush=True)

    for i in range(args.max_actions):
        acts=list(env.action_space)
        if not acts: break
        a,reason=A.choose(acts); A.action_counts[a.name]+=1
        prev=g; prev_level=int(getattr(obs,"levels_completed",0))
        obs=env.step(a,data={},reasoning=reason)
        if obs is None: A.ev("NULL_OBSERVATION",action=a.name); continue
        g=frame(obs); A.update(prev,g,a.name,obs,prev_level)
        r=A.records[-1]
        print("STEP",i+1,a.name,reason["mode"],"filtered",r["filtered_delta"],
              "pos",A.pos,"level",getattr(obs,"levels_completed",None),
              "state",getattr(getattr(obs,"state",None),"name",None),flush=True)
        if obs.state==GameState.WIN:
            A.ev("WIN",step=i+1); break
        if obs.state==GameState.GAME_OVER:
            A.gameovers+=1; A.ev("GAME_OVER",step=i+1,count=A.gameovers)
            if A.gameovers>=4: break
            obs=env.reset()
            if obs is None: break
            g=frame(obs); A.reset()

    result=A.result()
    result.update(game=args.game,seed=args.seed,reference_action=ref_action,
                  reference_pos=list(ref_pos) if ref_pos else None,
                  bootstrap_unique=unique,nuisance_pixels=int(nuis.sum()),
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
