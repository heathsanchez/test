from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)
BOTTOM=(60,64,12,64)

def grid(o):
    f=o.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)

def sname(o):
    s=o.state
    return s.name if hasattr(s,'name') else str(s)

def amap(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def to_l2(env,am):
    o=env.reset(); b=o.levels_completed
    for i,a in enumerate(L1):
        o=env.step(am[a],data={},reasoning={'mode':'retained_l1'})
        if o is None or sname(o)=='GAME_OVER': return o,False
        if o.levels_completed>b:
            return o,(i==len(L1)-1)
    return o,False

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

def hash_regions(a,regions):
    h=hashlib.blake2b(digest_size=12)
    for b in regions:
        y0,y1,x0,x1=b
        h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

class FullExplorer:
    def __init__(self,max_actions=6500):
        self.max_actions=max_actions
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
        if not ok: raise RuntimeError('L1 route failed')
        scene=largest_bbox(grid(o)); level=o.levels_completed
        edges=defaultdict(dict); states=set(); trace=[]; acts=sorted(am)
        t=0; actions=0; resets=0
        def fullsig(z):
            return hash_regions(grid(z),(scene,RETAINED,BOTTOM))
        def structsig(z):
            return hash_regions(grid(z),(scene,RETAINED))
        cur=fullsig(o); root=cur; states.add(cur)
        def untried(s): return [a for a in acts if a not in edges[s]]
        def frontier(st):
            q=deque([st]); prev={st:None}; pa={}
            while q:
                s=q.popleft()
                if untried(s):
                    seq=[]; c=s
                    while prev[c] is not None: seq.append(pa[c]); c=prev[c]
                    return list(reversed(seq)),s
                for a,x in edges[s].items():
                    if x is not None and x not in prev:
                        prev[x]=s; pa[x]=a; q.append(x)
            return None
        def reset():
            nonlocal o,cur,t,resets
            o=env.reset(); resets+=1; t=0; cur=fullsig(o); states.add(cur)
        while actions<self.max_actions:
            if o.levels_completed>level: break
            u=untried(cur)
            if u:
                aid=u[0]; sf=cur; ss=structsig(o); st=t
                z=env.step(am[aid],data={},reasoning={'mode':'full_trace_probe'})
                actions+=1; t+=1
                if z is None:
                    edges[sf][aid]=None
                    trace.append((ss,st,aid,'NONE',None))
                    continue
                if z.levels_completed>level:
                    trace.append((ss,st,aid,'GOAL',None)); o=z; break
                if sname(z)=='GAME_OVER':
                    edges[sf][aid]=None
                    trace.append((ss,st,aid,'TERM',None)); reset(); continue
                tf=fullsig(z); ts=structsig(z)
                edges[sf][aid]=tf; states.add(tf)
                trace.append((ss,st,aid,ts,t))
                o=z; cur=tf; continue
            fp=frontier(cur)
            if fp and fp[0]:
                aid=fp[0][0]; sf=cur; ss=structsig(o); st=t
                z=env.step(am[aid],data={},reasoning={'mode':'full_trace_nav'})
                actions+=1; t+=1
                if z is None or sname(z)=='GAME_OVER':
                    edges[sf].pop(aid,None)
                    trace.append((ss,st,aid,'TERM',None)); reset(); continue
                if z.levels_completed>level:
                    trace.append((ss,st,aid,'GOAL',None)); o=z; break
                tf=fullsig(z); ts=structsig(z)
                if edges[sf].get(aid)!=tf: edges[sf].pop(aid,None)
                trace.append((ss,st,aid,ts,t)); o=z; cur=tf; states.add(tf); continue
            rfp=frontier(root)
            # Use level-local reset + root search when current component frontier exhausted.
            if rfp is None:
                reset()
                rfp=frontier(cur)
                if rfp is None: break
            seq,target=rfp; reset()
            for aid in seq:
                if actions>=self.max_actions: break
                sf=cur; ss=structsig(o); st=t
                z=env.step(am[aid],data={},reasoning={'mode':'full_trace_replay'})
                actions+=1; t+=1
                if z is None or sname(z)=='GAME_OVER':
                    edges[sf].pop(aid,None); trace.append((ss,st,aid,'TERM',None)); reset(); break
                if z.levels_completed>level:
                    trace.append((ss,st,aid,'GOAL',None)); o=z; break
                tf=fullsig(z); ts=structsig(z)
                trace.append((ss,st,aid,ts,t))
                if edges[sf].get(aid)!=tf: edges[sf].pop(aid,None)
                o=z; cur=tf; states.add(tf)
            if o.levels_completed>level: break
        try: arc.close_scorecard()
        except: pass
        return {'scene':scene,'trace':trace,'actions':actions,'full_states':len(states),'goal':o.levels_completed>level,'resets':resets}

def phase_conflicts(trace,k):
    mp={}; conflicts=0; samples=0
    for ss,t,a,out,t2 in trace:
        key=(ss,t%k,a)
        if out in ('TERM','GOAL','NONE'): val=out
        else: val=(out,(t+1)%k)
        samples+=1
        if key in mp and mp[key]!=val: conflicts+=1
        else: mp[key]=val
    return conflicts,len(mp),samples

class PhaseExplorer:
    def __init__(self,k,max_actions=9000):
        self.k=k; self.max_actions=max_actions
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
        if not ok: raise RuntimeError('L1 route failed')
        scene=largest_bbox(grid(o)); level=o.levels_completed; acts=sorted(am)
        edges=defaultdict(dict); states=set(); t=0; actions=0; resets=0; nondet=0; episode=[]
        def ssig(z,tt):
            s=hash_regions(grid(z),(scene,RETAINED))
            return (s,tt%self.k)
        cur=ssig(o,t); root=cur; states.add(cur)
        def untried(s): return [a for a in acts if a not in edges[s]]
        def frontier(st):
            q=deque([st]); prev={st:None}; pa={}
            while q:
                s=q.popleft()
                if untried(s):
                    seq=[]; c=s
                    while prev[c] is not None: seq.append(pa[c]); c=prev[c]
                    return list(reversed(seq)),s
                for a,x in edges[s].items():
                    if x is not None and isinstance(x,tuple) and x not in prev:
                        prev[x]=s; pa[x]=a; q.append(x)
            return None
        def reset():
            nonlocal o,t,cur,resets,episode
            o=env.reset(); t=0; cur=ssig(o,t); states.add(cur); resets+=1; episode=[]
        while actions<self.max_actions:
            if o.levels_completed>level:
                break
            u=untried(cur)
            if u:
                aid=u[0]; before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'phase_probe','k':self.k})
                actions+=1; t+=1; episode.append(aid)
                if z is None:
                    edges[before][aid]=None; continue
                if z.levels_completed>level:
                    o=z; break
                if sname(z)=='GAME_OVER':
                    edges[before][aid]='TERM'; reset(); continue
                nxt=ssig(z,t)
                old=edges[before].get(aid)
                if old is not None and old!=nxt: nondet+=1
                edges[before][aid]=nxt; states.add(nxt); o=z; cur=nxt; continue
            fp=frontier(cur)
            if fp and fp[0]:
                aid=fp[0][0]; before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'phase_nav','k':self.k})
                actions+=1; t+=1; episode.append(aid)
                if z is None or sname(z)=='GAME_OVER':
                    edges[before].pop(aid,None); reset(); continue
                if z.levels_completed>level: o=z; break
                nxt=ssig(z,t)
                if edges[before].get(aid)!=nxt:
                    nondet+=1; edges[before].pop(aid,None)
                states.add(nxt); o=z; cur=nxt; continue
            rfp=frontier(root)
            if rfp is None: break
            seq,target=rfp; reset()
            for aid in seq:
                if actions>=self.max_actions: break
                before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'phase_replay','k':self.k})
                actions+=1; t+=1; episode.append(aid)
                if z is None or sname(z)=='GAME_OVER':
                    edges[before].pop(aid,None); reset(); break
                if z.levels_completed>level: o=z; break
                nxt=ssig(z,t)
                if edges[before].get(aid)!=nxt:
                    nondet+=1; edges[before].pop(aid,None); o=z; cur=nxt; break
                o=z; cur=nxt; states.add(nxt)
            if o.levels_completed>level: break
        won=o.levels_completed>level
        result={'k':self.k,'won':won,'actions':actions,'states':len(states),
                'edges':sum(len(v) for v in edges.values()),'nondet':nondet,'resets':resets}
        if won: result['candidate_sequence']=episode; result['candidate_actions']=len(episode)
        try: sc=arc.close_scorecard(); result['score']=None if sc is None else sc.score
        except: pass
        return result

def main():
    collected=FullExplorer().run()
    print('TRACE_SUMMARY',json.dumps({k:v for k,v in collected.items() if k!='trace'},default=list,sort_keys=True))
    ks=[1,2,3,4,5,6,7,8,10,12,16,20,24,30,32,40,48,60,64]
    sweep=[]
    for k in ks:
        c,n,s=phase_conflicts(collected['trace'],k)
        row={'k':k,'conflicts':c,'mapped_transitions':n,'samples':s}
        sweep.append(row); print('PHASE_OFFLINE',json.dumps(row,sort_keys=True))
    zero=[x['k'] for x in sweep if x['conflicts']==0]
    if zero:
        chosen=min(zero)
    else:
        chosen=min(sweep,key=lambda x:(x['conflicts'],x['mapped_transitions'],x['k']))['k']
    print('CHOSEN_PHASE',chosen)
    # Run chosen and nearby candidates, smallest first; stop on verified online goal.
    trialks=[]
    for k in [chosen, max(1,chosen//2), chosen*2]:
        if k not in trialks and k<=128: trialks.append(k)
    trials=[]
    for k in trialks:
        r=PhaseExplorer(k).run(); trials.append(r); print('PHASE_TRIAL',json.dumps(r,sort_keys=True))
        if r['won']: break
    result={'classification':'ARC3_TEMPORAL_PHASE_REALIZATION','trace_summary':{k:v for k,v in collected.items() if k!='trace'},
            'offline_phase_sweep':sweep,'chosen_phase':chosen,'trials':trials}
    with open('arc3_developmental_v6_phase_result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True,default=list)
    wins=[r for r in trials if r['won']]
    if wins:
        w=wins[0]
        print('VERIFIED_EXTERNAL_ARC3_LEVEL2_TEMPORAL_PHASE_REALIZATION',json.dumps(w,sort_keys=True))
    else:
        print('TEMPORAL_PHASE_REALIZATION_DIAGNOSIS_COMPLETE')

if __name__=='__main__': main()
