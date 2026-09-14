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
        if o.levels_completed>b: return o,(i==len(L1)-1)
    return o,False
def bbox(a):
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
def hregions(a,regions):
    h=hashlib.blake2b(digest_size=12)
    for b in regions:
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()
def bottom_features(a):
    y0,y1,x0,x1=BOTTOM; z=a[y0:y1,x0:x1]
    vals,cnt=np.unique(z,return_counts=True)
    return hregions(a,(BOTTOM,)), tuple((int(v),int(n)) for v,n in zip(vals,cnt))

def collect(max_actions=7500):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
    if not ok: raise RuntimeError('L1 failed')
    scene=bbox(grid(o)); level=o.levels_completed; acts=sorted(am)
    def fs(z): return hregions(grid(z),(scene,RETAINED,BOTTOM))
    def ss(z): return hregions(grid(z),(scene,RETAINED))
    edges=defaultdict(dict); states=set(); trace=[]; t=0; actions=0; resets=0
    cur=fs(o); root=cur; states.add(cur)
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
                if isinstance(x,str) and x not in ('TERM','GOAL') and x not in prev:
                    prev[x]=s; pa[x]=a; q.append(x)
        return None
    def reset():
        nonlocal o,t,cur,resets
        o=env.reset(); resets+=1; t=0; cur=fs(o); states.add(cur)
    def record_before(aid):
        bh,bc=bottom_features(grid(o))
        return {'s':ss(o),'t':t,'a':aid,'bottom':bh,'bottom_counts':bc}
    def step(aid,mode):
        nonlocal o,t,cur,actions
        r=record_before(aid)
        z=env.step(am[aid],data={},reasoning={'mode':mode}); actions+=1; t+=1
        if z is None:
            r['out']='NONE'; trace.append(r); return 'none'
        if z.levels_completed>level:
            r['out']='GOAL'; trace.append(r); o=z; return 'goal'
        if sname(z)=='GAME_OVER':
            r['out']='TERM'; trace.append(r); return 'term'
        r['out']=ss(z); trace.append(r)
        nxt=fs(z); o=z; cur=nxt; states.add(nxt); return nxt
    while actions<max_actions and o.levels_completed==level:
        u=untried(cur)
        if u:
            aid=u[0]; before=cur; x=step(aid,'window_trace_probe')
            if x=='goal': break
            if x in ('term','none'):
                edges[before][aid]='TERM'; reset(); continue
            edges[before][aid]=x; continue
        fp=frontier(cur)
        if fp and fp[0]:
            aid=fp[0][0]; before=cur; expected=edges[before].get(aid)
            x=step(aid,'window_trace_nav')
            if x=='goal': break
            if x in ('term','none'):
                edges[before].pop(aid,None); reset(); continue
            if expected!=x: edges[before].pop(aid,None)
            continue
        rfp=frontier(root)
        if rfp is None: break
        seq,_=rfp; reset()
        for aid in seq:
            if actions>=max_actions: break
            before=cur; expected=edges[before].get(aid)
            x=step(aid,'window_trace_replay')
            if x=='goal': break
            if x in ('term','none'):
                edges[before].pop(aid,None); reset(); break
            if expected!=x:
                edges[before].pop(aid,None); break
        if o.levels_completed>level: break
    try: arc.close_scorecard()
    except: pass
    return {'scene':scene,'trace':trace,'actions':actions,'full_states':len(states),
            'goal':o.levels_completed>level,'resets':resets}

def outcome_at_time(trace):
    by=defaultdict(lambda:defaultdict(set))
    for r in trace: by[(r['s'],r['a'])][r['t']].add(r['out'])
    return by

def min_hitting_cuts(intervals):
    # intervals are integer boundary choices [lo,hi], inclusive
    cuts=[]; last=None
    for lo,hi in sorted(intervals,key=lambda x:(x[1],x[0])):
        if last is None or not (lo<=last<=hi):
            last=hi; cuts.append(last)
    return cuts

def learn_windows(trace,local=False):
    by=outcome_at_time(trace)
    constraints=defaultdict(list)
    same_time_conflicts=0
    for (s,a),tm in by.items():
        ts=sorted(tm)
        for t in ts:
            if len(tm[t])>1: same_time_conflicts+=1
        for u,v in zip(ts,ts[1:]):
            if tm[u] != tm[v]:
                constraints[s if local else '*'].append((u+1,v))
    cuts={}
    for k,ints in constraints.items(): cuts[k]=min_hitting_cuts(ints)
    return cuts,same_time_conflicts

def bucket(cuts,t):
    # number of learned event boundaries already crossed
    lo=0; hi=len(cuts)
    while lo<hi:
        mid=(lo+hi)//2
        if cuts[mid]<=t: lo=mid+1
        else: hi=mid
    return lo

def eval_windows(trace,cuts,local=False):
    mp={}; conflicts=0; represented=set()
    for r in trace:
        cs=cuts.get(r['s'],[]) if local else cuts.get('*',[])
        b=bucket(cs,r['t']); key=(r['s'],b,r['a']); represented.add((r['s'],b))
        val=r['out']
        if key in mp and mp[key]!=val: conflicts+=1
        else: mp[key]=val
    return {'conflicts':conflicts,'mapped_transitions':len(mp),'represented_states':len(represented),
            'cut_count':sum(len(x) for x in cuts.values()),'structures_with_cuts':sum(bool(x) for x in cuts.values())}

class WindowExplorer:
    def __init__(self,cuts,local,max_actions=14000):
        self.cuts=cuts; self.local=local; self.max_actions=max_actions
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
        if not ok: raise RuntimeError('L1 failed')
        scene=bbox(grid(o)); level=o.levels_completed; acts=sorted(am)
        def struct(z): return hregions(grid(z),(scene,RETAINED))
        def state(z,t):
            s=struct(z); cs=self.cuts.get(s,[]) if self.local else self.cuts.get('*',[])
            return (s,bucket(cs,t))
        edges=defaultdict(dict); states=set(); t=0; actions=0; resets=0; nondet=0; episode=[]
        cur=state(o,t); root=cur; states.add(cur)
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
                    if isinstance(x,tuple) and x not in prev:
                        prev[x]=s; pa[x]=a; q.append(x)
            return None
        def reset():
            nonlocal o,t,cur,resets,episode
            o=env.reset(); t=0; cur=state(o,t); states.add(cur); resets+=1; episode=[]
        while actions<self.max_actions and o.levels_completed==level:
            u=untried(cur)
            if u:
                aid=u[0]; before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'event_window_probe','local':self.local})
                actions+=1; t+=1; episode.append(aid)
                if z is None: edges[before][aid]='TERM'; continue
                if z.levels_completed>level: o=z; break
                if sname(z)=='GAME_OVER': edges[before][aid]='TERM'; reset(); continue
                nxt=state(z,t); old=edges[before].get(aid)
                if old is not None and old!=nxt: nondet+=1
                edges[before][aid]=nxt; states.add(nxt); o=z; cur=nxt; continue
            fp=frontier(cur)
            if fp and fp[0]:
                aid=fp[0][0]; before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'event_window_nav','local':self.local})
                actions+=1; t+=1; episode.append(aid)
                if z is None or sname(z)=='GAME_OVER': edges[before].pop(aid,None); reset(); continue
                if z.levels_completed>level: o=z; break
                nxt=state(z,t)
                if edges[before].get(aid)!=nxt: nondet+=1; edges[before].pop(aid,None)
                states.add(nxt); o=z; cur=nxt; continue
            rfp=frontier(root)
            if rfp is None: break
            seq,_=rfp; reset()
            for aid in seq:
                if actions>=self.max_actions: break
                before=cur
                z=env.step(am[aid],data={},reasoning={'mode':'event_window_replay','local':self.local})
                actions+=1; t+=1; episode.append(aid)
                if z is None or sname(z)=='GAME_OVER': edges[before].pop(aid,None); reset(); break
                if z.levels_completed>level: o=z; break
                nxt=state(z,t)
                if edges[before].get(aid)!=nxt: nondet+=1; edges[before].pop(aid,None); o=z; cur=nxt; break
                o=z; cur=nxt; states.add(nxt)
            if o.levels_completed>level: break
        won=o.levels_completed>level
        out={'kind':'local' if self.local else 'global','won':won,'actions':actions,'states':len(states),
             'edges':sum(len(v) for v in edges.values()),'nondet':nondet,'resets':resets}
        if won: out['candidate_actions']=len(episode); out['candidate_sequence']=episode
        try: sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
        except: pass
        return out

def main():
    c=collect()
    tr=c['trace']
    # Test whether the formerly retained 208-pixel component is just a clock/resource display.
    t2b=defaultdict(set); b2t=defaultdict(set); count_vectors=defaultdict(set)
    for r in tr:
        t2b[r['t']].add(r['bottom']); b2t[r['bottom']].add(r['t']); count_vectors[r['t']].add(tuple(r['bottom_counts']))
    clock_diag={'observed_times':len(t2b),'bottom_hashes':len(b2t),
                'times_with_multiple_bottom_hashes':sum(len(v)>1 for v in t2b.values()),
                'bottom_hashes_seen_at_multiple_times':sum(len(v)>1 for v in b2t.values()),
                'times_with_multiple_color_count_vectors':sum(len(v)>1 for v in count_vectors.values())}
    print('TRACE',json.dumps({k:v for k,v in c.items() if k!='trace'},default=list,sort_keys=True))
    print('CLOCK_DIAG',json.dumps(clock_diag,sort_keys=True))

    gcuts,g_same=learn_windows(tr,local=False)
    lcuts,l_same=learn_windows(tr,local=True)
    ge=eval_windows(tr,gcuts,False); le=eval_windows(tr,lcuts,True)
    print('GLOBAL_WINDOWS',json.dumps({'cuts':gcuts.get('*',[]),'same_time_conflicts':g_same,**ge},sort_keys=True))
    local_summary={'same_time_conflicts':l_same,**le,
                   'max_cuts_per_structure':max([len(x) for x in lcuts.values()] or [0]),
                   'structures':len(set(r['s'] for r in tr))}
    print('LOCAL_WINDOWS',json.dumps(local_summary,sort_keys=True))

    trials=[]
    order=[]
    if le['conflicts']<=ge['conflicts']: order=[(lcuts,True),(gcuts,False)]
    else: order=[(gcuts,False),(lcuts,True)]
    for cuts,islocal in order:
        r=WindowExplorer(cuts,islocal).run(); trials.append(r); print('WINDOW_TRIAL',json.dumps(r,sort_keys=True))
        if r['won']: break
    result={'classification':'ARC3_CONSEQUENCE_EARNED_EVENT_WINDOW_REALIZATION',
            'trace_summary':{k:v for k,v in c.items() if k!='trace'},'clock_diagnostic':clock_diag,
            'global_window_eval':{'cuts':gcuts.get('*',[]),'same_time_conflicts':g_same,**ge},
            'local_window_eval':local_summary,'local_cuts':lcuts,'trials':trials}
    with open('arc3_developmental_v7_windows_result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True,default=list)
    wins=[x for x in trials if x['won']]
    if wins: print('VERIFIED_EXTERNAL_ARC3_LEVEL2_EVENT_WINDOW_REALIZATION',json.dumps(wins[0],sort_keys=True))
    else: print('EVENT_WINDOW_FRONTIER_IDENTIFIED')

if __name__=='__main__': main()
