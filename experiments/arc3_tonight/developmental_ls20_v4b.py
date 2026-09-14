from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

EXTRA=(53,63,1,11)

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
    return (min(ys),max(ys)+1,min(xs),max(xs)+1)

class Projector:
    def __init__(self,obs): self.scene=largest_bbox(grid(obs))
    def sig(self,obs):
        a=grid(obs); h=hashlib.blake2b(digest_size=12)
        for b in (self.scene,EXTRA):
            y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
        return h.hexdigest()

def action_map(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def execute_sequences(env,amap,solutions,reason='compiled_replay'):
    obs=env.reset(); n=0
    for li,seq in enumerate(solutions):
        before=obs.levels_completed
        for aid in seq:
            obs=env.step(amap[aid],data={},reasoning={'mode':reason,'compiled_level':li})
            n+=1
            if obs is None or sname(obs)=='GAME_OVER':
                return obs,n,False
            if obs.levels_completed>before:
                # A compiled level sequence must end exactly at the consequence it certifies.
                if aid != seq[-1]:
                    return obs,n,False
                break
        if obs is None or obs.levels_completed<=before:
            return obs,n,False
    return obs,n,True

def qualify(solutions):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); amap=action_map(env)
    obs,n,ok=execute_sequences(env,amap,solutions,'independent_compiled_qualification')
    expected=len(solutions)
    ok=bool(ok and obs is not None and obs.levels_completed==expected)
    score=None
    try:
        sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except Exception: pass
    return {'ok':ok,'levels_completed':None if obs is None else obs.levels_completed,'actions':n,'score':score}

def explore_level(env,obs,amap,prior,max_actions=7000):
    level=obs.levels_completed; p=Projector(obs); root=p.sig(obs); cur=root
    aids=sorted(amap); edges=defaultdict(dict); states={root}
    dev=0; recovery=0; resets=0; terminals=0; nondet=0; episode=[]

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
        nonlocal recovery,resets,episode
        ro,n,ok=execute_sequences(env,amap,prior,'recovery_compiled_prefix')
        recovery+=n; resets+=1; episode=[]
        if not ok or ro is None or ro.levels_completed!=level:
            raise RuntimeError(f'failed verified restore level={level} ok={ok} lc={None if ro is None else ro.levels_completed}')
        return ro

    def take(aid,mode):
        nonlocal dev,episode
        nxt=env.step(amap[aid],data={},reasoning={'mode':mode,'level':level})
        dev+=1; episode.append(aid)
        return nxt

    while dev<max_actions:
        if obs.levels_completed>level:
            break
        if sname(obs)=='GAME_OVER':
            obs=restore(); cur=p.sig(obs); states.add(cur); continue
        u=untried(cur)
        if u:
            aid=u[0]; before=cur; nxt=take(aid,'development_probe')
            if nxt is None:
                edges[before][aid]=None; continue
            if nxt.levels_completed>level:
                obs=nxt; candidate=list(episode); break
            if sname(nxt)=='GAME_OVER':
                edges[before][aid]=None; terminals+=1; obs=restore(); cur=p.sig(obs); states.add(cur); continue
            t=p.sig(nxt); edges[before][aid]=t; states.add(t); obs=nxt; cur=t; continue

        fp=frontier_path(cur)
        if fp and fp[0]:
            aid=fp[0][0]; before=cur; nxt=take(aid,'frontier_navigation')
            if nxt is None or sname(nxt)=='GAME_OVER':
                edges[before].pop(aid,None); obs=restore(); cur=p.sig(obs); continue
            if nxt.levels_completed>level:
                obs=nxt; candidate=list(episode); break
            t=p.sig(nxt)
            if edges[before].get(aid)!=t:
                nondet+=1; edges[before].pop(aid,None)
            obs=nxt; cur=t; states.add(t); continue

        rfp=frontier_path(root)
        if rfp is None:
            rec={'solved':False,'exhausted':True,'level':level,'development_actions':dev,'recovery_actions':recovery,
                 'states':len(states),'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
                 'scene':list(p.scene),'extra':list(EXTRA)}
            return rec,obs,None
        seq,target=rfp; obs=restore(); cur=p.sig(obs)
        for aid in seq:
            if dev>=max_actions: break
            before=cur; nxt=take(aid,'graph_replay')
            if nxt is None or sname(nxt)=='GAME_OVER':
                edges[before].pop(aid,None); obs=restore(); cur=p.sig(obs); break
            if nxt.levels_completed>level:
                obs=nxt; candidate=list(episode); break
            t=p.sig(nxt)
            if edges[before].get(aid)!=t:
                nondet+=1; edges[before].pop(aid,None); obs=nxt; cur=t; break
            obs=nxt; cur=t; states.add(t)
        if obs.levels_completed>level:
            break
    else:
        candidate=None

    if obs.levels_completed<=level:
        rec={'solved':False,'exhausted':False,'level':level,'development_actions':dev,'recovery_actions':recovery,
             'states':len(states),'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
             'scene':list(p.scene),'extra':list(EXTRA)}
        return rec,obs,None

    candidate=list(episode)
    q=qualify(prior+[candidate])
    rec={'solved':q['ok'],'level':level,'development_actions':dev,'recovery_actions':recovery,
         'states':len(states),'edges':sum(len(v) for v in edges.values()),'terminals':terminals,'nondet':nondet,
         'candidate_actions':len(candidate),'candidate_sequence':candidate,'qualification':q,
         'compression_vs_development':1.0-len(candidate)/max(1,dev),'scene':list(p.scene),'extra':list(EXTRA)}
    if not q['ok']:
        rec['rejected_reason']='successful-online-trajectory-failed-independent-replay'
        return rec,obs,None
    return rec,obs,candidate

def main():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); amap=action_map(env); obs=env.reset()
    sols=[]; records=[]
    while obs is not None and obs.levels_completed<obs.win_levels and len(records)<7:
        rec,obs,sol=explore_level(env,obs,amap,sols)
        records.append(rec); print('LEVEL',json.dumps(rec,sort_keys=True))
        if not rec['solved'] or sol is None: break
        sols.append(sol)
    try:
        sc=arc.close_scorecard(); discovery_score=None if sc is None else sc.score
    except Exception: discovery_score=None

    final=qualify(sols) if sols else {'ok':False,'levels_completed':0,'actions':0,'score':None}
    result={'classification':'ARC3_REPLAY_QUALIFIED_DEVELOPMENTAL_COMPILATION','observation_channel':list(EXTRA),
            'levels_developed':len(sols),'records':records,'final_independent_replay':final,'discovery_score':discovery_score}
    with open('arc3_developmental_v4b_result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
    print('FINAL_REPLAY',json.dumps(final,sort_keys=True))
    if final['ok'] and final['levels_completed']==7:
        print('VERIFIED_EXTERNAL_ARC3_7_OF_7_REPLAY_QUALIFIED_DEVELOPMENTAL_COMPILATION')
    elif final['ok'] and final['levels_completed']>0:
        print(f"VERIFIED_EXTERNAL_ARC3_{final['levels_completed']}_LEVEL_REPLAY_QUALIFIED_COMPILATION")
    else:
        print('NO_REPLAY_QUALIFIED_COMPILED_TRANSFER')

if __name__=='__main__': main()
