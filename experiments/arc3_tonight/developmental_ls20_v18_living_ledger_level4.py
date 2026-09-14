from __future__ import annotations
import hashlib, heapq, json, math
from collections import defaultdict, Counter
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
L3=[1,1,1,1,1,1,1,1,3,2,2,2,2,2,2,2,2,1,1,1,3,3,1,4,4,4,4,4,4,4,1,1,1,3,1,2,1,4,2]
PREFIX=[L1,L2,L3]
RETAINED=(53,63,1,11)
TARGET_LEVEL=3
ACTIONS=(1,2,3,4)

def grid(o):
    f=o.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)
def sname(o):
    s=o.state
    return s.name if hasattr(s,'name') else str(s)
def amap(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}
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
def hregions(a,regions):
    h=hashlib.blake2b(digest_size=12)
    for b in regions:
        y0,y1,x0,x1=b
        h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

class SuccessPrior:
    def __init__(self,seqs):
        self.bi=defaultdict(Counter); self.uni=Counter()
        for seq in seqs:
            prev=0
            for a in seq:
                self.uni[a]+=1; self.bi[prev][a]+=1; prev=a
    def order(self,path):
        prev=path[-1] if path else 0
        ctr=self.bi[prev]
        return sorted(ACTIONS,key=lambda a:(-(ctr[a]+1)/(sum(ctr.values())+4),a))

class Authority:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        e=self.arc.make('ls20'); am=amap(e)
        o,ok,acts=self.to_level(e,am)
        if not ok: raise RuntimeError('compiled self failed')
        self.scene=largest_bbox(grid(o)); self.aids=sorted(am)
        self.prefix_cost=acts
        self.total_actions=acts
        self.episodes=1
    def to_level(self,e,am):
        o=e.reset(); n=0
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                n+=1
                if o is None or sname(o)=='GAME_OVER': return o,False,n
                if o.levels_completed>before:
                    if i!=len(seq)-1: return o,False,n
                    break
            if o is None or o.levels_completed<=before: return o,False,n
        return o,o.levels_completed==TARGET_LEVEL,n
    def fresh(self,path=()):
        e=self.arc.make('ls20'); am=amap(e); o,ok,n=self.to_level(e,am)
        self.total_actions+=n; self.episodes+=1
        if not ok: return e,am,o,{'kind':'BROKEN_PREFIX'}
        for j,a in enumerate(path):
            o=e.step(am[a],data={},reasoning={'mode':'frontier_replay','depth':j+1})
            self.total_actions+=1
            if o is None or sname(o)=='GAME_OVER':
                return e,am,o,{'kind':'TERM','depth':j+1}
            if o.levels_completed>TARGET_LEVEL:
                return e,am,o,{'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
        return e,am,o,{'kind':'STATE','depth':len(path),'sig':self.sig(o)}
    def sig(self,o):
        return hregions(grid(o),(self.scene,RETAINED))
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except: return None

def verify(seq):
    A=Authority()
    e,am,o,r=A.fresh(tuple(seq))
    score=A.close()
    return {'ok':r.get('kind')=='GOAL' and r.get('depth')==len(seq),
            'result':r,'score':score,'actions':len(seq)}

def main():
    A=Authority(); P=SuccessPrior(PREFIX)
    e0,am0,o0,r0=A.fresh(())
    if r0['kind']!='STATE': raise RuntimeError(r0)
    root=r0['sig']

    best={root:(0,())}
    edges=defaultdict(dict)
    frontier=[(0,(),root)]
    queued={root}
    expanded_actions=0; dominated=0; collisions=0; terminals=0
    stale_replays=0; goal=None
    max_episodes=2500; max_cost=180; walk_limit=200

    def has_untried(s):
        return any(a not in edges[s] for a in ACTIONS)
    def push(s):
        if s in best and has_untried(s):
            c,p=best[s]
            heapq.heappush(frontier,(c,p,s))

    while frontier and A.episodes<max_episodes and goal is None:
        cost,path,s=heapq.heappop(frontier)
        if best.get(s)!=(cost,path) or not has_untried(s): continue

        e,am,o,r=A.fresh(path)
        if r['kind']!='STATE' or r['sig']!=s:
            stale_replays+=1
            continue

        cur=s; cur_path=path; cur_cost=cost
        steps=0
        while steps<walk_limit and cur_cost<max_cost and goal is None:
            untried=[a for a in P.order(cur_path) if a not in edges[cur]]
            if not untried:
                break
            a=untried[0]
            before=cur
            z=e.step(am[a],data={},reasoning={'mode':'living_ledger_probe','depth':cur_cost+1})
            A.total_actions+=1; expanded_actions+=1; steps+=1
            npth=cur_path+(a,); ncost=cur_cost+1

            if z is None or sname(z)=='GAME_OVER':
                edges[before][a]='TERM'; terminals+=1
                break
            if z.levels_completed>TARGET_LEVEL:
                edges[before][a]='GOAL'; goal=npth
                print('GOAL_DISCOVERED',json.dumps({
                    'depth':len(goal),'episodes':A.episodes,'ledger_entries':len(best),
                    'expanded_actions':expanded_actions,'dominated_histories':dominated,
                    'sequence':goal},sort_keys=True))
                break

            ns=A.sig(z)
            old_edge=edges[before].get(a)
            if old_edge is not None and old_edge!=ns:
                collisions+=1
                print('COLLISION',json.dumps({'state':before,'action':a,'old':old_edge,'new':ns}))
                break
            edges[before][a]=ns

            old=best.get(ns)
            if old is None or ncost<old[0]:
                best[ns]=(ncost,npth)
                push(ns)
            else:
                dominated+=1

            # Current state may still have other untried actions; schedule its
            # cheapest representative for another grounded episode.
            push(before)

            # Continue living forward only while this exact history is the
            # cheapest representative of the new present. Otherwise the current
            # arrival is dominated and we return to the ledger frontier.
            if best.get(ns)!=(ncost,npth):
                break
            cur=ns; cur_path=npth; cur_cost=ncost

        if A.episodes%25==0:
            print('LEDGER',json.dumps({
                'episodes':A.episodes,'ledger_entries':len(best),
                'frontier':len(frontier),'expanded_actions':expanded_actions,
                'qualified_edges':sum(len(v) for v in edges.values()),
                'dominated_histories':dominated,'collisions':collisions,
                'max_cost':max(v[0] for v in best.values()),
                'environment_actions':A.total_actions},sort_keys=True))

        if collisions>0:
            # A structural collision is a certified representation residual.
            break

    discovery_score=A.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={'classification':'ARC3_LIVING_SELF_LEDGER_LEVEL4',
        'goal_found':goal is not None,'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'ledger_entries':len(best),'qualified_edges':sum(len(v) for v in edges.values()),
        'expanded_actions':expanded_actions,'dominated_histories':dominated,
        'collisions':collisions,'terminal_outcomes':terminals,
        'stale_replays':stale_replays,'episodes':A.episodes,
        'environment_actions':A.total_actions,'prefix_cost_per_episode':A.prefix_cost,
        'scene':list(A.scene),'discovery_score':discovery_score,
        'independent_verification':q}
    with open('arc3_developmental_v18_living_ledger_level4_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_LIVING_SELF_LEDGER_BREAKTHROUGH')
    elif collisions:
        print('CERTIFIED_LEVEL4_REPRESENTATION_RESIDUAL_FROM_LIVING_LEDGER')
    elif goal:
        print('LEVEL4_LIVING_LEDGER_FAILED_REPLAY')
    else:
        print('LEVEL4_LIVING_LEDGER_FRONTIER')

if __name__=='__main__': main()
