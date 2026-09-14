from __future__ import annotations
import hashlib, json, random
from collections import defaultdict, deque
import numpy as np
import arc_agi

def grid(obs):
    f=obs.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)

def state_name(obs):
    s=obs.state
    return s.name if hasattr(s,'name') else str(s)

def largest_component_bbox(a):
    vals,counts=np.unique(a,return_counts=True)
    bg=int(vals[np.argmax(counts)])
    mask=(a!=bg)
    H,W=mask.shape
    seen=np.zeros_like(mask,dtype=bool)
    best=[]
    for y in range(H):
        for x in range(W):
            if not mask[y,x] or seen[y,x]: continue
            q=[(y,x)]; seen[y,x]=1; comp=[]
            for cy,cx in q:
                comp.append((cy,cx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=cy+dy,cx+dx
                    if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1; q.append((ny,nx))
            if len(comp)>len(best): best=comp
    ys=[y for y,x in best]; xs=[x for y,x in best]
    return (min(ys),max(ys)+1,min(xs),max(xs)+1),bg,len(best)

class SceneProjector:
    def __init__(self,root_grid):
        self.bbox,self.bg,self.component_size=largest_component_bbox(root_grid)
    def project(self,a):
        y0,y1,x0,x1=self.bbox
        return a[y0:y1,x0:x1]
    def sig(self,obs):
        return hashlib.blake2b(self.project(grid(obs)).tobytes(),digest_size=12).hexdigest()

class Explorer:
    def __init__(self,max_actions=2500):
        self.max_actions=max_actions
        self.edges=defaultdict(dict); self.frames={}; self.trace=[]
        self.actions_taken=0; self.resets=0; self.replays=0; self.relocations=0; self.terminals=0
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); obs=env.reset(); start=obs.levels_completed
        proj=SceneProjector(grid(obs)); aids=[getattr(a,'value',i+1) for i,a in enumerate(env.action_space)]
        amap={getattr(a,'value',i+1):a for i,a in enumerate(env.action_space)}
        root=proj.sig(obs); cur=root; self.frames[root]=proj.project(grid(obs)).copy()
        def untried(s): return [a for a in aids if a not in self.edges[s]]
        def shortest_frontier(start_s):
            q=deque([start_s]); prev={start_s:None}; pa={}
            while q:
                s=q.popleft()
                if untried(s):
                    acts=[]; c=s
                    while prev[c] is not None: acts.append(pa[c]); c=prev[c]
                    return list(reversed(acts)),s
                for a,t in self.edges.get(s,{}).items():
                    if t is not None and t not in prev:
                        prev[t]=s; pa[t]=a; q.append(t)
            return None
        while self.actions_taken<self.max_actions:
            if obs.levels_completed>start: return self.finish(arc,True,obs,proj,root,False)
            if state_name(obs)=='GAME_OVER':
                obs=env.reset(); self.resets+=1; cur=proj.sig(obs); self.frames.setdefault(cur,proj.project(grid(obs)).copy()); continue
            us=untried(cur)
            if us:
                aid=us[0]; before=cur
                nxt=env.step(amap[aid],data={},reasoning={'mode':'probe','representation':'largest_component_bbox'})
                self.actions_taken+=1
                if nxt is None:
                    self.edges[before][aid]=None; continue
                if nxt.levels_completed>start:
                    obs=nxt; self.trace.append({'n':self.actions_taken,'mode':'probe','a':aid,'level_complete':True}); return self.finish(arc,True,obs,proj,root,False)
                if state_name(nxt)=='GAME_OVER':
                    self.edges[before][aid]=None; self.terminals+=1; obs=env.reset(); self.resets+=1; cur=proj.sig(obs); continue
                t=proj.sig(nxt); is_new=t not in self.frames; self.edges[before][aid]=t; self.frames.setdefault(t,proj.project(grid(nxt)).copy())
                self.trace.append({'n':self.actions_taken,'mode':'probe','s':before,'a':aid,'t':t,'new':is_new})
                obs=nxt; cur=t; continue
            plan=shortest_frontier(cur)
            if plan and plan[0]:
                aid=plan[0][0]; target=plan[1]; before=cur
                nxt=env.step(amap[aid],data={},reasoning={'mode':'navigate','target':target})
                self.actions_taken+=1; self.relocations+=1
                if nxt is None or state_name(nxt)=='GAME_OVER':
                    self.edges[before].pop(aid,None); obs=env.reset(); self.resets+=1; cur=proj.sig(obs); continue
                if nxt.levels_completed>start: obs=nxt; return self.finish(arc,True,obs,proj,root,False)
                t=proj.sig(nxt)
                if self.edges[before].get(aid)!=t: self.edges[before].pop(aid,None)
                obs=nxt; cur=t; continue
            rootplan=shortest_frontier(root)
            if rootplan is None: return self.finish(arc,False,obs,proj,root,True)
            acts,target=rootplan; obs=env.reset(); self.resets+=1; cur=proj.sig(obs)
            for aid in acts:
                if self.actions_taken>=self.max_actions: break
                before=cur; nxt=env.step(amap[aid],data={},reasoning={'mode':'replay','target':target})
                self.actions_taken+=1; self.replays+=1
                if nxt is None or state_name(nxt)=='GAME_OVER': self.edges[before].pop(aid,None); break
                if nxt.levels_completed>start: obs=nxt; return self.finish(arc,True,obs,proj,root,False)
                obs=nxt; cur=proj.sig(nxt)
        return self.finish(arc,False,obs,proj,root,False)
    def finish(self,arc,won,obs,proj,root,exhausted):
        out={'kind':'scene_quotient_consequence_explorer','won_first_level':won,'levels_completed':obs.levels_completed,
             'actions':self.actions_taken,'resets':self.resets,'replay_actions':self.replays,'frontier_relocations':self.relocations,
             'unique_states':len(self.frames),'qualified_edges':sum(len(x) for x in self.edges.values()),
             'noop_edges':sum(1 for s,m in self.edges.items() for a,t in m.items() if s==t),'terminal_edges':self.terminals,
             'reachable_graph_exhausted_without_goal':exhausted,'bbox':proj.bbox,'background':proj.bg,
             'root_component_size':proj.component_size,'root':root,'trace_tail':self.trace[-25:]}
        try: sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
        except Exception: pass
        return out

def random_control(max_actions=400):
    rng=random.Random(20260914); arc=arc_agi.Arcade(); env=arc.make('ls20'); obs=env.reset(); start=obs.levels_completed
    n=0
    while n<max_actions and obs.levels_completed==start:
        a=rng.choice(list(env.action_space)); obs=env.step(a,data={}); n+=1
        if state_name(obs)=='GAME_OVER': obs=env.reset()
    out={'actions':n,'won_first_level':obs.levels_completed>start,'levels_completed':obs.levels_completed}
    try: sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
    except Exception: pass
    return out

def main():
    r=random_control(); print('RANDOM_RESULT',json.dumps(r,sort_keys=True))
    d=Explorer().run(); print('DEVELOPMENTAL_V2_RESULT',json.dumps(d,sort_keys=True))
    with open('arc3_developmental_v2_result.json','w') as f: json.dump({'random':r,'developmental_v2':d},f,indent=2,sort_keys=True)
    if d['won_first_level']: print('VERIFIED_EXTERNAL_ARC3_LEVEL_ACQUISITION_AFTER_CONSEQUENCE_EARNED_SCENE_QUOTIENT')
    elif d['reachable_graph_exhausted_without_goal']: print('CERTIFIED_NEXT_OBSTRUCTION_AFTER_SCENE_QUOTIENT')
    else: print('BOUNDED_UNKNOWN_SEARCH_AFTER_SCENE_QUOTIENT')
if __name__=='__main__': main()
