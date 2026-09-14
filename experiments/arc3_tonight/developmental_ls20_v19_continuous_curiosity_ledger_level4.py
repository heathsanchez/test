from __future__ import annotations
import hashlib, json
from collections import defaultdict, Counter, deque
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

class Prior:
    def __init__(self,seqs):
        self.bi=defaultdict(Counter)
        for seq in seqs:
            prev=0
            for a in seq:
                self.bi[prev][a]+=1; prev=a
    def rank(self,prev,a):
        c=self.bi[prev]; return (c[a]+1)/(sum(c.values())+4)

class Kernel:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        self.P=Prior(PREFIX)
        self.total_env_actions=0
        self.episodes=0
        self.scene=None
        self.root=None
    def fresh(self):
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); self.episodes+=1
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                self.total_env_actions+=1
                if o is None or sname(o)=='GAME_OVER': return e,am,o,False
                if o.levels_completed>before:
                    if i!=len(seq)-1: return e,am,o,False
                    break
            if o is None or o.levels_completed<=before: return e,am,o,False
        if o.levels_completed!=TARGET_LEVEL: return e,am,o,False
        if self.scene is None:
            self.scene=largest_bbox(grid(o))
            self.root=self.sig(o)
        return e,am,o,True
    def sig(self,o):
        return hregions(grid(o),(self.scene,RETAINED))
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except: return None

def shortest_graph_path(root,target,edges):
    q=deque([root]); prev={root:None}; pa={}
    while q:
        s=q.popleft()
        if s==target: break
        for a,t in edges.get(s,{}).items():
            if not isinstance(t,str) or t in ('TERM','GOAL'): continue
            if t not in prev:
                prev[t]=s; pa[t]=a; q.append(t)
    if target not in prev: return None
    out=[]; c=target
    while prev[c] is not None:
        out.append(pa[c]); c=prev[c]
    return list(reversed(out))

def verify(seq):
    K=Kernel(); e,am,o,ok=K.fresh()
    if not ok:
        K.close(); return {'ok':False,'where':'prefix'}
    before=o.levels_completed
    for i,a in enumerate(seq):
        o=e.step(am[a],data={},reasoning={'mode':'independent_continuous_ledger_verification'})
        K.total_env_actions+=1
        if o is None or sname(o)=='GAME_OVER':
            score=K.close(); return {'ok':False,'where':'terminal','at':i+1,'score':score}
        if o.levels_completed>before:
            score=K.close()
            return {'ok':i==len(seq)-1,'where':'goal','at':i+1,
                    'levels_completed':o.levels_completed,'score':score}
    score=K.close()
    return {'ok':False,'where':'no_goal','levels_completed':o.levels_completed,'score':score}

def main():
    K=Kernel()
    e,am,o,ok=K.fresh()
    if not ok: raise RuntimeError('compiled self failed')
    root=K.root; cur=root
    edges=defaultdict(dict)
    edge_visits=Counter(); state_visits=Counter({root:1})
    best={root:(0,())}
    collisions=0; terminal_events=0; goal_edge=None
    actual_path=[]
    prev_action=0

    max_steps=120000
    restart_after=12000
    since_restart=0

    for step in range(1,max_steps+1):
        # Curiosity: unqualified consequences first. Once all four are known,
        # traverse the least-used/least-visited known consequence. Prior success
        # grammar breaks ties only; it cannot override evidence.
        unknown=[a for a in ACTIONS if a not in edges[cur]]
        if unknown:
            a=min(unknown,key=lambda x:(-K.P.rank(prev_action,x),x))
        else:
            def score(a):
                t=edges[cur][a]
                if t in ('TERM','GOAL'):
                    return (10**12,10**12,-K.P.rank(prev_action,a),a)
                return (edge_visits[(cur,a)],state_visits[t],-K.P.rank(prev_action,a),a)
            a=min(ACTIONS,key=score)

        before=cur
        z=e.step(am[a],data={},reasoning={'mode':'continuous_curiosity_ledger','step':step})
        K.total_env_actions+=1; since_restart+=1
        edge_visits[(before,a)]+=1
        actual_path.append(a)

        if z is None or sname(z)=='GAME_OVER':
            edges[before][a]='TERM'; terminal_events+=1
            e,am,o,ok=K.fresh()
            if not ok: break
            cur=root; actual_path=[]; prev_action=0; since_restart=0
            continue

        if z.levels_completed>TARGET_LEVEL:
            edges[before][a]='GOAL'; goal_edge=(before,a)
            print('GOAL_OBSERVED',json.dumps({'step':step,'episodes':K.episodes,
                'ledger_entries':len(best),'qualified_edges':sum(len(v) for v in edges.values()),
                'actual_episode_actions':len(actual_path)},sort_keys=True))
            break

        ns=K.sig(z)
        old=edges[before].get(a)
        if old is not None and old!=ns:
            collisions+=1
            print('COLLISION',json.dumps({'step':step,'state':before,'action':a,'old':old,'new':ns}))
            break
        edges[before][a]=ns
        state_visits[ns]+=1

        # Retained self uses cheapest known graph path, independent of the
        # potentially expensive exploratory walk that happened to reveal it.
        candidate=shortest_graph_path(root,ns,edges)
        if candidate is not None:
            oldbest=best.get(ns)
            if oldbest is None or len(candidate)<oldbest[0]:
                best[ns]=(len(candidate),tuple(candidate))

        cur=ns; o=z; prev_action=a

        if step%1000==0:
            print('LEDGER',json.dumps({'step':step,'episodes':K.episodes,
                'ledger_entries':len(best),'observed_states':len(state_visits),
                'qualified_edges':sum(len(v) for v in edges.values()),
                'unqualified_edges':sum(4-len(edges[s]) for s in state_visits),
                'collisions':collisions,'environment_actions':K.total_env_actions},sort_keys=True))

        # Periodic true rewind prevents an ever-increasing resource coordinate
        # from poisoning discovery, while the learned ledger survives.
        if since_restart>=restart_after:
            e,am,o,ok=K.fresh()
            if not ok: break
            cur=root; actual_path=[]; prev_action=0; since_restart=0

    discovery_score=K.close()

    candidate=None
    if goal_edge is not None:
        s,a=goal_edge
        p=shortest_graph_path(root,s,edges)
        if p is not None: candidate=p+[a]

    q=verify(candidate) if candidate is not None else {'ok':False}
    result={'classification':'ARC3_CONTINUOUS_CURIOSITY_SELF_LEDGER_LEVEL4',
        'goal_observed':goal_edge is not None,
        'candidate_depth':None if candidate is None else len(candidate),
        'candidate_sequence':candidate,
        'ledger_entries':len(best),'observed_states':len(state_visits),
        'qualified_edges':sum(len(v) for v in edges.values()),
        'collisions':collisions,'terminal_events':terminal_events,
        'episodes':K.episodes,'environment_actions':K.total_env_actions,
        'discovery_score':discovery_score,'independent_verification':q,
        'scene':list(K.scene)}
    with open('arc3_developmental_v19_continuous_curiosity_ledger_level4_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_CONTINUOUS_CURIOSITY_LEDGER_BREAKTHROUGH')
    elif collisions:
        print('CERTIFIED_LEVEL4_REPRESENTATION_RESIDUAL_FROM_CONTINUOUS_LIFE')
    elif goal_edge:
        print('LEVEL4_CONTINUOUS_GOAL_GRAPH_COMPRESSION_FAILED_REPLAY')
    else:
        print('LEVEL4_CONTINUOUS_CURIOSITY_FRONTIER')

if __name__=='__main__': main()
