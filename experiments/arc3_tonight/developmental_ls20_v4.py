from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

EXTRA=(53,63,1,11)  # consequence-selected in V3; semantic meaning intentionally unspecified

def grid(obs):
    f=obs.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)

def sname(obs):
    s=obs.state
    return s.name if hasattr(s,'name') else str(s)

def largest_bbox(a):
    vals,cnts=np.unique(a,return_counts=True); bg=int(vals[np.argmax(cnts)])
    m=a!=bg; H,W=m.shape; seen=np.zeros_like(m,bool); best=[]
    for y in range(H):
        for x in range(W):
            if not m[y,x] or seen[y,x]: continue
            q=[(y,x)]; seen[y,x]=1; pts=[]
            for cy,cx in q:
                pts.append((cy,cx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=cy+dy,cx+dx
                    if 0<=ny<H and 0<=nx<W and m[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1; q.append((ny,nx))
            if len(pts)>len(best): best=pts
    ys=[p[0] for p in best]; xs=[p[1] for p in best]
    return (min(ys),max(ys)+1,min(xs),max(xs)+1),bg,len(best)

class Projector:
    def __init__(self,obs):
        self.scene,self.bg,self.scene_size=largest_bbox(grid(obs))
    def sig(self,obs):
        a=grid(obs); h=hashlib.blake2b(digest_size=12)
        for b in (self.scene,EXTRA):
            y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
        return h.hexdigest()

def amap_for(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def bfs_path(edges,start,target):
    if start==target: return []
    q=deque([start]); prev={start:None}; pa={}
    while q:
        s=q.popleft()
        for a,t in edges.get(s,{}).items():
            if t is None or t in prev: continue
            prev[t]=s; pa[t]=a
            if t==target:
                seq=[]; c=t
                while prev[c] is not None:
                    seq.append(pa[c]); c=prev[c]
                return list(reversed(seq))
            q.append(t)
    return None

def replay_prefix(env, amap, solutions):
    obs=env.reset(); n=0
    for level,seq in enumerate(solutions):
        before=obs.levels_completed
        for aid in seq:
            obs=env.step(amap[aid],data={},reasoning={'mode':'compiled_prefix','level':level})
            n+=1
            if obs is None or sname(obs)=='GAME_OVER':
                return None,n,False
        if obs.levels_completed<=before:
            return obs,n,False
    return obs,n,True

def explore_level(env,obs,amap,prior_solutions,max_actions=5000):
    level=obs.levels_completed; p=Projector(obs); root=p.sig(obs); cur=root
    aids=sorted(amap)
    edges=defaultdict(dict); states={root}; development_actions=0; recovery_actions=0; resets=0
    terminals=0; nondet=0; goal_from=None; goal_action=None

    def untried(s): return [a for a in aids if a not in edges[s]]
    def frontier_path(st):
        q=deque([st]); prev={st:None}; pa={}
        while q:
            s=q.popleft()
            if untried(s):
                seq=[]; c=s
                while prev[c] is not None: seq.append(pa[c]); c=prev[c]
                return list(reversed(seq)),s
            for a,t in edges[s].items():
                if t is not None and t not in prev:
                    prev[t]=s; pa[t]=a; q.append(t)
        return None

    def restore():
        nonlocal recovery_actions,resets
        ro,n,ok=replay_prefix(env,amap,prior_solutions)
        recovery_actions+=n; resets+=1
        if not ok or ro is None or ro.levels_completed!=level:
            raise RuntimeError(f'failed restore to level {level}: ok={ok} lc={None if ro is None else ro.levels_completed}')
        return ro

    while development_actions<max_actions:
        if obs.levels_completed>level: break
        if sname(obs)=='GAME_OVER':
            obs=restore(); cur=p.sig(obs); states.add(cur); continue
        u=untried(cur)
        if u:
            aid=u[0]; before=cur
            nxt=env.step(amap[aid],data={},reasoning={'mode':'development_probe','level':level})
            development_actions+=1
            if nxt is None:
                edges[before][aid]=None; continue
            if nxt.levels_completed>level:
                goal_from=before; goal_action=aid; obs=nxt; break
            if sname(nxt)=='GAME_OVER':
                edges[before][aid]=None; terminals+=1; obs=restore(); cur=p.sig(obs); states.add(cur); continue
            t=p.sig(nxt); edges[before][aid]=t; states.add(t); obs=nxt; cur=t; continue
        fp=frontier_path(cur)
        if fp and fp[0]:
            aid=fp[0][0]; before=cur
            nxt=env.step(amap[aid],data={},reasoning={'mode':'frontier_navigation','level':level})
            development_actions+=1
            if nxt is None or sname(nxt)=='GAME_OVER':
                edges[before].pop(aid,None); obs=restore(); cur=p.sig(obs); continue
            if nxt.levels_completed>level:
                goal_from=before; goal_action=aid; obs=nxt; break
            t=p.sig(nxt)
            if edges[before].get(aid)!=t:
                nondet+=1; edges[before].pop(aid,None)
            obs=nxt; cur=t; states.add(t); continue
        rfp=frontier_path(root)
        if rfp is None:
            return {'solved':False,'exhausted':True,'level':level,'development_actions':development_actions,
                    'recovery_actions':recovery_actions,'resets':resets,'states':len(states),
                    'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
                    'scene':list(p.scene),'extra':list(EXTRA)},obs,None
        seq,target=rfp; obs=restore(); cur=p.sig(obs)
        for aid in seq:
            if development_actions>=max_actions: break
            before=cur; nxt=env.step(amap[aid],data={},reasoning={'mode':'graph_replay','level':level})
            development_actions+=1
            if nxt is None or sname(nxt)=='GAME_OVER':
                edges[before].pop(aid,None); obs=restore(); cur=p.sig(obs); break
            if nxt.levels_completed>level:
                goal_from=before; goal_action=aid; obs=nxt; break
            t=p.sig(nxt)
            if edges[before].get(aid)!=t:
                nondet+=1; edges[before].pop(aid,None); obs=nxt; cur=t; break
            obs=nxt; cur=t
        if goal_action is not None: break

    if goal_action is None:
        return {'solved':False,'exhausted':False,'level':level,'development_actions':development_actions,
                'recovery_actions':recovery_actions,'resets':resets,'states':len(states),
                'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
                'scene':list(p.scene),'extra':list(EXTRA)},obs,None

    prefix=bfs_path(edges,root,goal_from)
    if prefix is None: raise RuntimeError('goal predecessor lost from graph')
    solution=prefix+[goal_action]
    record={'solved':True,'exhausted':False,'level':level,'development_actions':development_actions,
            'recovery_actions':recovery_actions,'resets':resets,'states':len(states),
            'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
            'compiled_solution_actions':len(solution),'compiled_solution':solution,
            'compression_vs_development':1.0-len(solution)/max(1,development_actions),
            'scene':list(p.scene),'extra':list(EXTRA)}
    return record,obs,solution

def verify_all(solutions):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); amap=amap_for(env); obs=env.reset(); total=0
    per=[]
    for i,seq in enumerate(solutions):
        before=obs.levels_completed
        for aid in seq:
            obs=env.step(amap[aid],data={},reasoning={'mode':'compiled_verification','level':i})
            total+=1
            if obs is None or sname(obs)=='GAME_OVER': break
        ok=obs is not None and obs.levels_completed>before
        per.append({'level':i,'actions':len(seq),'verified':ok,'levels_completed':None if obs is None else obs.levels_completed})
        if not ok: break
    score=None
    try:
        sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except Exception: pass
    return {'verified_levels':sum(x['verified'] for x in per),'total_actions':total,'per_level':per,'score':score}

def main():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); amap=amap_for(env); obs=env.reset()
    solutions=[]; records=[]
    while obs is not None and obs.levels_completed<obs.win_levels and len(records)<7:
        rec,obs,sol=explore_level(env,obs,amap,solutions,max_actions=6000)
        records.append(rec); print('LEVEL_DEVELOPMENT',json.dumps(rec,sort_keys=True))
        if not rec['solved']: break
        solutions.append(sol)
    try:
        discovery_score=arc.close_scorecard().score
    except Exception: discovery_score=None
    verification=verify_all(solutions) if solutions else {'verified_levels':0,'total_actions':0,'per_level':[],'score':None}
    result={'classification':'ARC3_COMPILED_DEVELOPMENTAL_TRANSFER','observation_channel':list(EXTRA),
            'levels_developed':len(solutions),'records':records,'discovery_score':discovery_score,
            'compiled_verification':verification}
    with open('arc3_developmental_v4_result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
    print('COMPILED_VERIFICATION',json.dumps(verification,sort_keys=True))
    if verification['verified_levels']==7:
        print('VERIFIED_EXTERNAL_ARC3_7_OF_7_DEVELOPMENT_COMPILE_REPLAY')
    elif verification['verified_levels']>=1:
        print(f"VERIFIED_EXTERNAL_ARC3_{verification['verified_levels']}_LEVEL_COMPILED_TRANSFER")
    else:
        print('NO_COMPILED_TRANSFER_VERIFIED')

if __name__=='__main__': main()
