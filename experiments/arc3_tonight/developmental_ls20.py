from __future__ import annotations
import hashlib, json, random
from collections import defaultdict, deque
from typing import Dict, Optional

import numpy as np
import arc_agi

def grid(obs):
    f = obs.frame
    a = f[-1] if isinstance(f, list) else f
    return np.asarray(a, dtype=np.uint8)

def sig(obs):
    return hashlib.blake2b(grid(obs).tobytes(), digest_size=12).hexdigest()

def state_name(obs):
    s=obs.state
    return s.name if hasattr(s,'name') else str(s)

def run_random(max_actions=400, seed=20260914):
    rng=random.Random(seed)
    arc=arc_agi.Arcade()
    env=arc.make('ls20')
    obs=env.reset()
    start=obs.levels_completed
    actions=0
    while actions<max_actions and obs is not None and obs.levels_completed==start:
        a=rng.choice(list(env.action_space))
        obs=env.step(a, data={})
        actions+=1
        if obs is None: break
        if state_name(obs)=='GAME_OVER':
            obs=env.reset()
    out={'kind':'random','actions':actions,'levels_completed':0 if obs is None else obs.levels_completed,
         'won_first_level': bool(obs is not None and obs.levels_completed>start)}
    try:
        sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
    except Exception: pass
    return out

class ConsequenceExplorer:
    def __init__(self,max_actions=2500):
        self.max_actions=max_actions
        self.edges: Dict[str,Dict[int,Optional[str]]]=defaultdict(dict)
        self.frames={}
        self.levels={}
        self.terminal_edges=[]
        self.trace=[]
        self.actions_taken=0
        self.resets=0
        self.replays=0
        self.frontier_relocations=0
        self.action_ids=[]

    def untried(self,s):
        return [a for a in self.action_ids if a not in self.edges[s]]

    def shortest_to_frontier(self,start):
        q=deque([start]); prev={start:None}; prev_a={}
        target=None
        while q:
            s=q.popleft()
            if self.untried(s): target=s; break
            for a,t in self.edges.get(s,{}).items():
                if t is not None and t not in prev:
                    prev[t]=s; prev_a[t]=a; q.append(t)
        if target is None: return None
        acts=[]; cur=target
        while prev[cur] is not None:
            acts.append(prev_a[cur]); cur=prev[cur]
        return list(reversed(acts)), target

    def choose_action_obj(self, env, aid):
        for a in env.action_space:
            if getattr(a,'value',None)==aid or getattr(a,'name','')==f'ACTION{aid}':
                return a
        raise KeyError(aid)

    def run(self):
        arc=arc_agi.Arcade()
        env=arc.make('ls20')
        obs=env.reset()
        if obs is None: raise RuntimeError('reset returned None')
        start_level=obs.levels_completed
        self.action_ids=[getattr(a,'value',i+1) for i,a in enumerate(env.action_space)]
        root=sig(obs); cur=root
        self.frames[cur]=grid(obs); self.levels[cur]=obs.levels_completed

        while self.actions_taken<self.max_actions:
            if obs.levels_completed>start_level:
                return self.finish(arc, True, obs, root)
            if state_name(obs)=='GAME_OVER':
                obs=env.reset(); self.resets+=1; cur=sig(obs)
                self.frames[cur]=grid(obs); self.levels[cur]=obs.levels_completed
                continue

            choices=self.untried(cur)
            if choices:
                aid=choices[0]
                a=self.choose_action_obj(env,aid)
                before=cur
                nxt=env.step(a,data={}, reasoning={'mode':'probe','state':before,'action_id':aid})
                self.actions_taken+=1
                if nxt is None:
                    self.edges[before][aid]=None
                    self.trace.append({'n':self.actions_taken,'mode':'probe','s':before,'a':aid,'t':None})
                    continue
                if nxt.levels_completed>start_level:
                    self.trace.append({'n':self.actions_taken,'mode':'probe','s':before,'a':aid,'level_complete':True})
                    obs=nxt
                    return self.finish(arc,True,obs,root)
                if state_name(nxt)=='GAME_OVER':
                    self.edges[before][aid]=None
                    self.terminal_edges.append((before,aid))
                    self.trace.append({'n':self.actions_taken,'mode':'probe','s':before,'a':aid,'terminal':'GAME_OVER'})
                    obs=env.reset(); self.resets+=1; cur=sig(obs)
                    self.frames[cur]=grid(obs); self.levels[cur]=obs.levels_completed
                    continue
                t=sig(nxt)
                self.edges[before][aid]=t
                is_new=t not in self.frames
                self.frames.setdefault(t,grid(nxt)); self.levels[t]=nxt.levels_completed
                self.trace.append({'n':self.actions_taken,'mode':'probe','s':before,'a':aid,'t':t,'new':is_new})
                obs=nxt; cur=t
                continue

            plan=self.shortest_to_frontier(cur)
            if plan and plan[0]:
                acts,target=plan; self.frontier_relocations+=1
                aid=acts[0]
                a=self.choose_action_obj(env,aid)
                before=cur
                nxt=env.step(a,data={}, reasoning={'mode':'navigate_to_frontier','target':target})
                self.actions_taken+=1
                if nxt is None or state_name(nxt)=='GAME_OVER':
                    self.edges[before].pop(aid,None)
                    obs=env.reset(); self.resets+=1; cur=sig(obs)
                    continue
                if nxt.levels_completed>start_level:
                    obs=nxt; return self.finish(arc,True,obs,root)
                t=sig(nxt)
                if self.edges[before].get(aid)!=t:
                    self.edges[before].pop(aid,None)
                self.trace.append({'n':self.actions_taken,'mode':'navigate','s':before,'a':aid,'t':t})
                obs=nxt; cur=t
                continue

            rootplan=self.shortest_to_frontier(root)
            if rootplan is None:
                return self.finish(arc,False,obs,root, exhausted=True)
            acts,target=rootplan
            obs=env.reset(); self.resets+=1; cur=sig(obs); self.frontier_relocations+=1
            for aid in acts:
                if self.actions_taken>=self.max_actions: break
                a=self.choose_action_obj(env,aid)
                before=cur
                nxt=env.step(a,data={}, reasoning={'mode':'replay','target':target})
                self.actions_taken+=1; self.replays+=1
                if nxt is None or state_name(nxt)=='GAME_OVER':
                    self.edges[before].pop(aid,None)
                    break
                if nxt.levels_completed>start_level:
                    obs=nxt; return self.finish(arc,True,obs,root)
                t=sig(nxt); obs=nxt; cur=t
        return self.finish(arc,False,obs,root, exhausted=False)

    def finish(self,arc,won,obs,root,exhausted=False):
        edge_count=sum(len(v) for v in self.edges.values())
        noop=sum(1 for s,m in self.edges.items() for a,t in m.items() if t==s)
        result={
            'kind':'consequence_explorer','won_first_level':won,
            'levels_completed':obs.levels_completed if obs is not None else None,
            'actions':self.actions_taken,'resets':self.resets,'replay_actions':self.replays,
            'unique_states':len(self.frames),'qualified_edges':edge_count,'noop_edges':noop,
            'terminal_edges':len(self.terminal_edges),'frontier_relocations':self.frontier_relocations,
            'reachable_graph_exhausted_without_goal':exhausted,'root':root,
            'trace_tail':self.trace[-30:],
        }
        try:
            sc=arc.close_scorecard(); result['score']=None if sc is None else sc.score
        except Exception: pass
        return result

def main():
    random_result=run_random()
    print('RANDOM_RESULT',json.dumps(random_result,sort_keys=True))
    dev=ConsequenceExplorer().run()
    print('DEVELOPMENTAL_RESULT',json.dumps(dev,sort_keys=True))
    with open('arc3_developmental_result.json','w') as f:
        json.dump({'random':random_result,'developmental':dev},f,indent=2,sort_keys=True)
    if dev['won_first_level']:
        print('VERIFIED_EXTERNAL_ARC3_LEVEL_ACQUISITION_FROM_CONSEQUENCE_GRAPH')
    elif dev['reachable_graph_exhausted_without_goal']:
        print('CERTIFIED_REPRESENTATION_OR_ACTION_INADEQUACY_ON_ARC3_LEVEL1')
    else:
        print('BOUNDED_UNKNOWN_SEARCH')

if __name__=='__main__': main()
