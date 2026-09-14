from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)

def grid(o):
    f=o.frame; return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)
def sname(o):
    s=o.state; return s.name if hasattr(s,'name') else str(s)
def amap(env):
    xs=list(env.action_space); return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def components(a):
    vals,cnt=np.unique(a,return_counts=True); bg=int(vals[np.argmax(cnt)])
    m=a!=bg; H,W=m.shape; seen=np.zeros_like(m,bool); cc=[]
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
            ys=[p[0] for p in pts]; xs=[p[1] for p in pts]
            b=(min(ys),max(ys)+1,min(xs),max(xs)+1)
            cc.append({'size':len(pts),'bbox':b,'area':(b[1]-b[0])*(b[3]-b[2])})
    cc.sort(key=lambda z:(-z['size'],z['bbox']))
    return bg,cc

def inter_area(a,b):
    y0=max(a[0],b[0]); y1=min(a[1],b[1]); x0=max(a[2],b[2]); x1=min(a[3],b[3])
    return max(0,y1-y0)*max(0,x1-x0)

def reach_level2(env,am):
    o=env.reset()
    before=o.levels_completed
    for i,aid in enumerate(L1):
        o=env.step(am[aid],data={},reasoning={'mode':'retained_level1'})
        if o is None or sname(o)=='GAME_OVER': return o,False
        if o.levels_completed>before:
            return o,i==len(L1)-1
    return o,False

class Projector:
    def __init__(self,scene,extras):
        self.scene=tuple(scene); self.extras=tuple(tuple(x) for x in extras)
    def sig(self,o):
        a=grid(o); h=hashlib.blake2b(digest_size=12)
        for b in (self.scene,)+self.extras:
            y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
        return h.hexdigest()

def qualify_l2(seq):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env)
    o,ok=reach_level2(env,am)
    if not ok:
        try: arc.close_scorecard()
        except: pass
        return {'ok':False,'where':'L1'}
    before=o.levels_completed
    for i,aid in enumerate(seq):
        o=env.step(am[aid],data={},reasoning={'mode':'independent_level2_qualification'})
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':'L2_terminal','actions':i+1}
        if o.levels_completed>before:
            exact=i==len(seq)-1
            score=None
            try: score=arc.close_scorecard().score
            except: pass
            return {'ok':exact,'where':'L2_goal','actions':i+1,'levels_completed':o.levels_completed,'score':score}
    try: arc.close_scorecard()
    except: pass
    return {'ok':False,'where':'L2_no_goal','actions':len(seq),'levels_completed':o.levels_completed}

def explore(extras,max_actions=4500):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=reach_level2(env,am)
    if not ok: raise RuntimeError('retained L1 failed')
    level=1
    bg,cc=components(grid(o)); scene=cc[0]['bbox']; p=Projector(scene,extras)
    root=p.sig(o); cur=root; edges=defaultdict(dict); states={root}; aids=sorted(am)
    dev=0; resets=0; terminals=0; nondet=0; episode=[]
    def untried(s): return [a for a in aids if a not in edges[s]]
    def frontier(st):
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
        nonlocal resets,episode
        ro=env.reset(); resets+=1; episode=[]
        if ro is None or ro.levels_completed!=level:
            raise RuntimeError(f'level-local reset failed lc={None if ro is None else ro.levels_completed}')
        return ro
    def take(aid,mode):
        nonlocal dev,episode
        z=env.step(am[aid],data={},reasoning={'mode':mode,'level':1}); dev+=1; episode.append(aid); return z

    winner=None
    while dev<max_actions:
        u=untried(cur)
        if u:
            aid=u[0]; before=cur; z=take(aid,'probe')
            if z is None: edges[before][aid]=None; continue
            if z.levels_completed>level: o=z; winner=list(episode); break
            if sname(z)=='GAME_OVER':
                edges[before][aid]=None; terminals+=1; o=restore(); cur=p.sig(o); states.add(cur); continue
            t=p.sig(z)
            old=edges[before].get(aid)
            if old is not None and old!=t: nondet+=1
            edges[before][aid]=t; states.add(t); o=z; cur=t; continue
        fp=frontier(cur)
        if fp and fp[0]:
            aid=fp[0][0]; before=cur; z=take(aid,'navigate')
            if z is None or sname(z)=='GAME_OVER':
                edges[before].pop(aid,None); o=restore(); cur=p.sig(o); continue
            if z.levels_completed>level: o=z; winner=list(episode); break
            t=p.sig(z)
            if edges[before].get(aid)!=t: nondet+=1; edges[before].pop(aid,None)
            o=z; cur=t; states.add(t); continue
        rfp=frontier(root)
        if rfp is None: break
        seq,target=rfp; o=restore(); cur=p.sig(o)
        for aid in seq:
            if dev>=max_actions: break
            before=cur; z=take(aid,'replay')
            if z is None or sname(z)=='GAME_OVER':
                edges[before].pop(aid,None); o=restore(); cur=p.sig(o); break
            if z.levels_completed>level: o=z; winner=list(episode); break
            t=p.sig(z)
            if edges[before].get(aid)!=t: nondet+=1; edges[before].pop(aid,None); o=z; cur=t; break
            o=z; cur=t; states.add(t)
        if winner is not None: break

    out={'won_online':winner is not None,'actions':dev,'states':len(states),'edges':sum(len(v) for v in edges.values()),
         'nondet':nondet,'terminals':terminals,'resets':resets,'scene':list(scene),'extras':[list(x) for x in extras],
         'exhausted':frontier(root) is None if winner is None else False}
    if winner is not None:
        q=qualify_l2(winner); out['candidate_actions']=len(winner); out['qualification']=q; out['won']=q['ok']
        if q['ok']: out['candidate_sequence']=winner
    else: out['won']=False
    try: arc.close_scorecard()
    except: pass
    return out,cc

def main():
    # Get the Level-2 root components after replaying the retained L1 capability.
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=reach_level2(env,am)
    if not ok: raise RuntimeError('L1 retained route did not reach L2')
    bg,cc=components(grid(o)); scene=cc[0]['bbox']
    try: arc.close_scorecard()
    except: pass

    cand=[]
    for z in cc[1:]:
        b=tuple(z['bbox'])
        if z['size']<3: continue
        # skip components already mostly represented by the retained channel
        if inter_area(b,RETAINED) >= 0.5*z['area']: continue
        # skip components mostly inside the scene crop
        if inter_area(b,scene) >= 0.8*z['area']: continue
        cand.append({'bbox':b,'size':z['size'],'area':z['area']})
    cand.sort(key=lambda z:(z['area'],z['size'],z['bbox']))
    cand=cand[:10]
    print('L2_ROOT',json.dumps({'background':bg,'scene':scene,'retained':RETAINED,'candidates':cand},default=list,sort_keys=True))

    base,_=explore([RETAINED],max_actions=1800)
    print('BASE',json.dumps(base,sort_keys=True))
    results=[]; winners=[]
    for i,c in enumerate(cand):
        r,_=explore([RETAINED,c['bbox']],max_actions=4500)
        r.update({'candidate_index':i,'candidate_bbox':list(c['bbox']),'candidate_area':c['area']})
        results.append(r); print('CANDIDATE',json.dumps(r,sort_keys=True))
        if r['won']: winners.append((c['area'],r['candidate_actions'],i,r))
    selected=None
    if winners:
        winners.sort(); _,_,i,r=winners[0]; selected={'index':i,'bbox':list(cand[i]['bbox']),'result':r}
    result={'classification':'ARC3_LEVEL2_CONSEQUENCE_DRIVEN_OBSERVATION_GENESIS','retained_level1_channel':list(RETAINED),
            'scene':list(scene),'candidates':cand,'base':base,'results':results,'selected':selected}
    with open('arc3_developmental_v5_result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True,default=list)
    if selected:
        print('VERIFIED_EXTERNAL_ARC3_LEVEL2_ADDITIONAL_OBSERVATION_GENESIS')
    else:
        best=min(results,key=lambda r:(r['nondet'],r['states'],r['actions'])) if results else base
        print('NO_LEVEL2_SINGLE_CHANNEL_SOLVE',json.dumps(best,sort_keys=True))

if __name__=='__main__': main()
