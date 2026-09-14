#!/usr/bin/env python3
"""
ARC-AGI-3 developmental kernel v7: objecthood from intervention-induced co-motion.

No game source, fixed coordinates, palette semantics, stored route, or level logic.

Frozen lineage:
 v1 raw frame state over-split;
 v2 appearance-persistent objects were not available;
 v3 undifferentiated change mixed world and common consequence;
 v4 common consequence factorization yielded a reference/action geometry but unstable identity;
 v5 position-only ontology contracted too aggressively because motion estimation was contaminated.

V7 derives the controlled carrier generically:
  connected visual components are matched across controlled interventions;
  components that undergo the same non-zero displacement form a causal co-motion group;
  the group, not a supplied "player" concept, becomes the active carrier.
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


def blobs(mask,min_n=1):
    h,w=mask.shape; seen=np.zeros_like(mask,bool); out=[]
    for y in range(h):
        for x in range(w):
            if seen[y,x] or not mask[y,x]: continue
            st=[(y,x)]; seen[y,x]=1; pts=[]
            while st:
                yy,xx=st.pop(); pts.append((yy,xx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
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


def components(g,nuis=None):
    out=[]
    for c in np.unique(g):
        m=(g==c)
        if nuis is not None: m=m & ~nuis
        for b in blobs(m,1):
            h=b["y1"]-b["y0"]+1; w=b["x1"]-b["x0"]+1
            out.append(dict(color=int(c),area=b["n"],h=h,w=w,
                            cy=b["cy"],cx=b["cx"],y0=b["y0"],x0=b["x0"],y1=b["y1"],x1=b["x1"]))
    return out


def desc(c):
    return (c["color"],c["area"],c["h"],c["w"])


def match_components(g0,g1,nuis=None):
    a=components(g0,nuis); b=components(g1,nuis)
    by0=defaultdict(list); by1=defaultdict(list)
    for c in a: by0[desc(c)].append(c)
    for c in b: by1[desc(c)].append(c)
    matches=[]
    for d in set(by0)&set(by1):
        aa=by0[d]; bb=by1[d]; used=set()
        # greedy nearest matching is exact for isolated translated components here,
        # but remains generic and makes no color-role assumption.
        for c0 in aa:
            choices=[]
            for j,c1 in enumerate(bb):
                if j in used: continue
                dy=c1["cy"]-c0["cy"]; dx=c1["cx"]-c0["cx"]
                choices.append((abs(dy)+abs(dx),j,c1))
            if choices:
                _,j,c1=min(choices); used.add(j)
                dy=int(round(c1["cy"]-c0["cy"])); dx=int(round(c1["cx"]-c0["cx"]))
                matches.append((d,c0,c1,(dy,dx)))
    return matches


def motion_evidence(g0,g1,nuis=None):
    ms=match_components(g0,g1,nuis)
    support=defaultdict(lambda:{"weight":0,"count":0,"descs":[]})
    for d,c0,c1,v in ms:
        dist=abs(v[0])+abs(v[1])
        if 2<=dist<=12:
            support[v]["weight"]+=c0["area"]
            support[v]["count"]+=1
            support[v]["descs"].append(d)
    ranked=sorted(support.items(),key=lambda kv:(-kv[1]["count"],-kv[1]["weight"],abs(kv[0][0])+abs(kv[0][1])))
    return ranked,ms


def locate_group(g,group_descs,nuis=None,near=None):
    cs=components(g,nuis)
    cand=[c for c in cs if desc(c) in group_descs]
    if not cand: return None,[]
    # If multiple copies exist, form spatial clusters; causal carrier descriptors should co-locate.
    # Seed candidate groups around each component and score descriptor coverage + compactness.
    best=None
    needed=set(group_descs)
    for seed in cand:
        group=[c for c in cand if abs(c["cy"]-seed["cy"])+abs(c["cx"]-seed["cx"])<=10]
        cov=len({desc(c) for c in group}&needed)
        if cov==0: continue
        total=sum(c["area"] for c in group)
        cy=sum(c["cy"]*c["area"] for c in group)/total
        cx=sum(c["cx"]*c["area"] for c in group)/total
        compact=sum(abs(c["cy"]-cy)+abs(c["cx"]-cx) for c in group)
        nearcost=(abs(cy-near[0])+abs(cx-near[1])) if near is not None else 0
        score=(-cov,compact,nearcost,-total)
        if best is None or score<best[0]:
            best=(score,(int(round(cy)),int(round(cx))),group)
    return (best[1],best[2]) if best else (None,[])


def local_sig(g,pos,r=6):
    if pos is None: return "NONE"
    y,x=pos
    y0,y1=max(0,y-r),min(g.shape[0],y+r+1)
    x0,x1=max(0,x-r),min(g.shape[1],x+r+1)
    patch=g[y0:y1,x0:x1]
    # Position is already in active state; this hash represents only local contextual appearance.
    import hashlib
    return hashlib.sha1(patch.tobytes()).hexdigest()[:12]


def bootstrap(env):
    acts=list(env.action_space)
    one={}; raw={}
    for a in acts:
        o0=env.reset(); g0=frame(o0)
        o1=env.step(a,data={},reasoning={"mode":"ONE_STEP_INTERVENTION"}); g1=frame(o1)
        one[a.name]=(g0,g1,g0!=g1); raw[a.name]=int(np.count_nonzero(g0!=g1))
    common=np.logical_and.reduce([one[a.name][2] for a in acts])
    nuis=expand_common(common,pad=4)
    unique={a.name:int(np.count_nonzero(one[a.name][2]&~nuis)) for a in acts}

    # Collect first-order motion evidence.
    action_votes=defaultdict(Counter)
    action_descs=defaultdict(lambda:defaultdict(list))
    for a in acts:
        ranked,_=motion_evidence(one[a.name][0],one[a.name][1],nuis)
        for v,e in ranked[:3]:
            action_votes[a.name][v]+=e["count"]*100+e["weight"]
            action_descs[a.name][v].extend(e["descs"])

    # Pick a reference-forming intervention with strongest coherent nonzero motion.
    def strength(an):
        return max(action_votes[an].values()) if action_votes[an] else 0
    ref_action=min([a.name for a in acts],key=lambda n:(-strength(n),-unique[n],n))

    # Controlled second-order interventions from the same reconstructed reference state.
    second={}
    for a in acts:
        o0=env.reset(); g0=frame(o0)
        ract=next(x for x in acts if x.name==ref_action)
        orf=env.step(ract,data={},reasoning={"mode":"REFERENCE_RECONSTRUCTION"}); gr=frame(orf)
        o2=env.step(a,data={},reasoning={"mode":"SECOND_ORDER_INTERVENTION"}); g2=frame(o2)
        second[a.name]=(gr,g2)
        ranked,_=motion_evidence(gr,g2,nuis)
        for v,e in ranked[:3]:
            action_votes[a.name][v]+=e["count"]*100+e["weight"]
            action_descs[a.name][v].extend(e["descs"])

    vectors={}
    for an,votes in action_votes.items():
        if votes:
            v,n=votes.most_common(1)[0]
            # Require at least one coherent translated component with displacement >=2.
            vectors[an]=v

    # Causal carrier descriptors are those that participate in selected action translations,
    # preferably across more than one intervention.
    dc=Counter()
    for an,v in vectors.items():
        for d in action_descs[an][v]:
            dc[d]+=1
    group_descs={d for d,n in dc.items() if n>=2}
    if not group_descs and dc:
        mx=max(dc.values()); group_descs={d for d,n in dc.items() if n==mx}

    # Locate derived carrier after reference intervention.
    gr=second[next(iter(second))][0] if second else one[ref_action][1]
    ref_pos,ref_group=locate_group(gr,group_descs,nuis,None)

    Path("arc3-results").mkdir(parents=True,exist_ok=True)
    np.savez_compressed("arc3-results/probes.npz",
        nuisance=nuis.astype(np.uint8),**{f"reset_{a}":one[a][0] for a in one},
        **{f"one_{a}":one[a][1] for a in one},
        **{f"ref_{a}":second[a][0] for a in second},
        **{f"two_{a}":second[a][1] for a in second})

    diag={
      "raw_delta":raw,"unique_delta":unique,"nuisance_pixels":int(nuis.sum()),
      "reference_action":ref_action,"reference_pos":list(ref_pos) if ref_pos else None,
      "vectors":{k:list(v) for k,v in vectors.items()},
      "group_descs":[list(d) for d in sorted(group_descs)],
      "descriptor_votes":{str(list(d)):n for d,n in dc.items()},
      "action_votes":{a:{str(list(v)):n for v,n in vs.items()} for a,vs in action_votes.items()}
    }
    return nuis,ref_action,ref_pos,vectors,group_descs,diag


class Agent:
    def __init__(self,nuis,ref_action,ref_pos,vectors,group_descs,seed=0):
        self.nuis=nuis; self.ref_action=ref_action; self.ref_pos=ref_pos
        self.vectors=dict(vectors); self.group_descs=set(group_descs); self.rng=random.Random(seed)
        self.pos=None; self.events=[]; self.records=[]; self.action_counts=Counter()
        self.graph=defaultdict(Counter); self.tried=defaultdict(set); self.visits=Counter()
        self.consequence=defaultdict(Counter)
        self.context_trials=defaultdict(lambda:defaultdict(set))
        self.use_local_context=False
        self.use_event_state=False
        self.event_box=None
        self.event_modes=set()
        self.node=None
        self.trace_frames=[]
        self.reset_boundaries=[]
        self.level=0; self.max_level=0; self.gameovers=0; self.phase="CAUSAL_CARRIER_ONTOLOGY"

    def ev(self,k,**kw):
        e={"t":len(self.records),"kind":k,**kw}; self.events.append(e)
        print("EVENT",json.dumps(e,sort_keys=True),flush=True)

    def reset(self):
        self.pos=None
        self.node=None

    def event_sig(self,g):
        if not self.use_event_state or self.event_box is None: return None
        y0,y1,x0,x1=self.event_box
        import hashlib
        return hashlib.sha1(g[y0:y1,x0:x1].tobytes()).hexdigest()[:12]

    def make_node(self,g):
        if self.pos is None: return None
        parts=[self.pos]
        if self.use_event_state:
            parts.append(self.event_sig(g))
        if self.use_local_context:
            parts.append(local_sig(g,self.pos))
        return tuple(parts) if len(parts)>1 else self.pos

    def residual_mask(self,prev,g,oldpos,newpos):
        m=(prev!=g)&~self.nuis
        # Remove the intervention-induced carrier itself from the residual.
        # The causal carrier is compact; use a generic padded neighborhood around
        # its derived centroids rather than a supplied sprite shape.
        for p in (oldpos,newpos):
            if p is None: continue
            y,x=p
            m[max(0,y-4):min(m.shape[0],y+5),
              max(0,x-4):min(m.shape[1],x+5)]=False
        return m

    def maybe_birth_event_state(self,prev,g,oldpos,newpos,st):
        if self.use_event_state or oldpos is None or newpos is None or st=="GAME_OVER":
            return False
        m=self.residual_mask(prev,g,oldpos,newpos)
        ys,xs=np.where(m)
        # Ordinary UI/resource ticks are tiny. Authorize a new persistent state
        # only when a compact non-carrier residual is large enough to be a real
        # intervention consequence.
        if len(xs)<6:
            return False
        y0,y1=int(ys.min()),int(ys.max())+1
        x0,x1=int(xs.min()),int(xs.max())+1
        if (y1-y0)*(x1-x0)>160:
            return False
        pad=4
        self.event_box=(max(0,y0-pad),min(g.shape[0],y1+pad),
                        max(0,x0-pad),min(g.shape[1],x1+pad))
        self.use_event_state=True
        before=self.event_sig(prev); after=self.event_sig(g)
        self.event_modes.update([before,after])
        self.phase="PERSISTENT_EVENT_STATE_GENESIS"
        # Keep learned geometry, but re-index active consequence state.
        self.graph.clear(); self.tried.clear(); self.consequence.clear()
        self.ev("BIRTH_PERSISTENT_EVENT_STATE",box=list(self.event_box),
                witness_position=list(newpos),residual_pixels=len(xs),
                before=before,after=after)
        return True

    def locate(self,g):
        p,grp=locate_group(g,self.group_descs,self.nuis,self.pos)
        return p,grp

    def choose(self,acts):
        if self.pos is None:
            a=next((x for x in acts if x.name==self.ref_action),None) or min(acts,key=lambda z:z.name)
            return a,{"mode":"RECONSTRUCT_CAUSAL_CARRIER"}

        node=self.node
        unseen=[a for a in acts if a.name not in self.tried[node]]
        if unseen:
            a=min(unseen,key=lambda z:(self.action_counts[z.name],z.name))
            return a,{"mode":"LOCAL_INTERVENTION_FRONTIER","position":list(self.pos),
                      "contextual":self.use_local_context}

        adj=defaultdict(list)
        for (p,an),outs in self.graph.items():
            if len(outs)==1:
                p2=next(iter(outs)); adj[p].append((an,p2))
        q=deque([(node,[])]); seen={node}
        while q:
            p,path=q.popleft()
            if p!=node and len(self.tried[p])<len(acts) and path:
                an=path[0]; a=next(x for x in acts if x.name==an)
                return a,{"mode":"ROUTE_TO_FRONTIER","target":str(p)}
            for an,p2 in adj.get(p,[]):
                if p2 not in seen:
                    seen.add(p2); q.append((p2,path+[an]))

        # All observed nodes locally explored: use learned action geometry to seek least visited predicted location.
        opts=[]
        for a in acts:
            v=self.vectors.get(a.name)
            if v is None: continue
            outs=self.graph.get((node,a.name),Counter())
            # Once an action is observed only to return to the same active state,
            # it is no longer a lawful "predicted frontier" move. This prevents
            # repeatedly paying for a certified self-loop.
            if outs and set(outs)=={node}:
                continue
            p2=(self.pos[0]+v[0],self.pos[1]+v[1])
            opts.append((self.visits[p2],self.action_counts[a.name],a,p2))
        if opts:
            _,_,a,p2=min(opts,key=lambda z:(z[0],z[1],z[2].name))
            return a,{"mode":"PREDICTED_POSITION_FRONTIER","predicted_next":list(p2)}

        # If every learned move is a self-loop, preserve UNKNOWN but diversify
        # rather than deterministically hammering the same action forever.
        a=min(acts,key=lambda z:(self.action_counts[z.name],z.name))
        return a,{"mode":"UNKNOWN_SEARCH_NO_PRODUCTIVE_EDGE"}

    def update(self,prev,g,action,obs,prev_level):
        oldpos=self.pos
        oldnode=self.node
        oldlocal=local_sig(prev,oldpos) if oldpos is not None else "NONE"

        p,grp=self.locate(g)
        if p is not None:
            self.pos=p
            if oldpos is None:
                self.ev("CAUSAL_CARRIER_RECONSTRUCTED",action=action,pos=list(p),
                        group=[list(desc(c)) for c in grp])

        delta=int(np.count_nonzero((prev!=g)&~self.nuis))
        lvl=int(getattr(obs,"levels_completed",0))
        st=getattr(getattr(obs,"state",None),"name",str(getattr(obs,"state",None)))
        born=self.maybe_birth_event_state(prev,g,oldpos,self.pos,st)
        if self.use_event_state:
            mode=self.event_sig(g)
            if mode not in self.event_modes:
                self.event_modes.add(mode)
                self.ev("NEW_EVENT_MODE",mode=mode,count=len(self.event_modes),
                        position=list(self.pos) if self.pos else None)
        self.node=self.make_node(g)

        if oldpos is not None and self.pos is not None and oldnode is not None and self.node is not None:
            self.tried[oldnode].add(action)
            self.graph[(oldnode,action)][self.node]+=1
            self.visits[self.pos]+=1
            ck=(self.pos,min(9,delta//10),st,lvl-prev_level)
            self.consequence[(oldnode,action)][ck]+=1

            # While position-only is active, test whether local context is a verified separator
            # for nonterminal divergent consequences at the same position/action.
            if not self.use_local_context and not self.use_event_state and st!="GAME_OVER":
                basekey=(oldpos,action)
                self.context_trials[basekey][oldlocal].add(ck)
                trials=self.context_trials[basekey]
                outcomes=set()
                locally_deterministic=True
                for sig,outs in trials.items():
                    nonterm={o for o in outs if o[2]!="GAME_OVER"}
                    if len(nonterm)>1:
                        locally_deterministic=False
                    outcomes |= nonterm
                if len(outcomes)>1 and len(trials)>1 and locally_deterministic:
                    witness={sig:[str(o) for o in outs if o[2]!="GAME_OVER"] for sig,outs in trials.items()}
                    self.ev("VERIFIED_LOCAL_CONTEXT_SEPARATOR",position=list(oldpos),action=action,
                            witness=witness)
                    self.use_local_context=True
                    self.phase="CONTEXT_SPLIT_ON_CONSEQUENCE"
                    # Recompile the active graph under the finer state; provenance remains in records.
                    self.graph.clear(); self.tried.clear(); self.consequence.clear()
                    self.node=self.make_node(g)
                    self.ev("ACTIVE_STATE_RECOMPILED",state="position_plus_local_context",
                            current_node=str(self.node))

        if lvl>self.max_level:
            self.ev("VERIFIED_PROGRESS",from_level=self.max_level,to_level=lvl,action=action); self.max_level=lvl
        if lvl!=self.level:
            self.ev("LEVEL_BOUNDARY",old=self.level,new=lvl); self.level=lvl
            self.graph.clear(); self.tried.clear(); self.visits.clear(); self.consequence.clear()
            self.context_trials.clear(); self.pos=None; self.node=None
            self.use_local_context=False; self.use_event_state=False
            self.event_box=None; self.event_modes.clear()
            self.phase="CAUSAL_CARRIER_ONTOLOGY"

        self.trace_frames.append(g.copy())
        self.records.append(dict(i=len(self.records),action=action,raw_delta=int(np.count_nonzero(prev!=g)),
            filtered_delta=delta,old_pos=list(oldpos) if oldpos else None,pos=list(self.pos) if self.pos else None,
            old_local=oldlocal,node=str(self.node),contextual=self.use_local_context,
            group=[list(desc(c)) for c in grp],level=lvl,state=st,phase=self.phase))

    def result(self):
        return dict(actions=len(self.records),max_levels_completed=self.max_level,
          vectors={k:list(v) for k,v in self.vectors.items()},group_descs=[list(d) for d in sorted(self.group_descs)],
          phase=self.phase,gameovers=self.gameovers,action_counts=dict(self.action_counts),
          distinct_positions=len(self.visits),contextual_state=self.use_local_context,
          event_state=self.use_event_state,event_box=list(self.event_box) if self.event_box else None,
          event_mode_count=len(self.event_modes),
          events=self.events,records=self.records)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game",default="ls20"); ap.add_argument("--max-actions",type=int,default=400)
    ap.add_argument("--seed",type=int,default=0); ap.add_argument("--out",default="arc3_developmental_result.json")
    args=ap.parse_args()
    arc=arc_agi.Arcade()
    env=arc.make(args.game,save_recording=True,include_frame_data=True,render_mode=None)
    if env is None: raise SystemExit("make failed")

    nuis,ref_action,ref_pos,vectors,group_descs,diag=bootstrap(env)
    print("BOOTSTRAP",json.dumps(diag,sort_keys=True),flush=True)
    obs=env.reset(); g=frame(obs)
    A=Agent(nuis,ref_action,ref_pos,vectors,group_descs,args.seed)
    A.level=int(getattr(obs,"levels_completed",0)); A.max_level=A.level
    A.trace_frames=[g.copy()]
    A.reset_boundaries=[0]
    A.ev("CAUSAL_CARRIER_GENESIS",**diag)
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
        print("STEP",i+1,a.name,reason["mode"],"delta",r["filtered_delta"],"pos",A.pos,
              "level",getattr(obs,"levels_completed",None),"state",getattr(getattr(obs,"state",None),"name",None),flush=True)
        if obs.state==GameState.WIN:
            A.ev("WIN",step=i+1); break
        if obs.state==GameState.GAME_OVER:
            A.gameovers+=1; A.ev("GAME_OVER",step=i+1,count=A.gameovers)
            if A.gameovers>=4: break
            obs=env.reset()
            if obs is None: break
            g=frame(obs); A.reset()
            A.trace_frames.append(g.copy()); A.reset_boundaries.append(len(A.trace_frames)-1)

    result=A.result()
    result.update(game=args.game,seed=args.seed,reference_action=ref_action,
      reference_pos=list(ref_pos) if ref_pos else None,nuisance_pixels=int(nuis.sum()),
      final_levels_completed=int(getattr(obs,"levels_completed",0)) if obs else None,
      final_state=getattr(getattr(obs,"state",None),"name",None) if obs else None,
      win_levels=int(getattr(obs,"win_levels",0)) if obs else None)
    try:
        sc=arc.close_scorecard()
        if sc is not None: result["scorecard"]=sc.model_dump(mode="json") if hasattr(sc,"model_dump") else str(sc)
    except Exception as e: result["scorecard_error"]=repr(e)
    Path(args.out).write_text(json.dumps(result,indent=2,default=str))
    np.savez_compressed("arc3-results/trajectory_frames.npz",
        frames=np.stack(A.trace_frames), reset_boundaries=np.asarray(A.reset_boundaries,dtype=np.int32))
    print("TRACE_FRAMES",len(A.trace_frames),"RESETS",A.reset_boundaries,flush=True)
    print("RESULT",json.dumps({k:v for k,v in result.items() if k not in ("records","events","scorecard")},sort_keys=True),flush=True)
    print("OUTPUT",args.out,flush=True)

if __name__=="__main__": main()
