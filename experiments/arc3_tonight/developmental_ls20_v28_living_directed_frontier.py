from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
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

def sig(o,scene):
    a=grid(o); h=hashlib.blake2b(digest_size=12)
    for b in (scene,RETAINED):
        y0,y1,x0,x1=b
        h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    r11=int(np.sum(a[61:63,:] == 11))
    r8=int(np.sum(a[61:63,:] == 8))
    h.update(r11.to_bytes(2,'little',signed=False))
    h.update(r8.to_bytes(2,'little',signed=False))
    return h.hexdigest()

class Kernel:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        self.scene=None; self.root=None
        self.env_actions=0; self.episodes=0
    def fresh(self):
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); self.episodes+=1
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                self.env_actions+=1
                if o is None or sname(o)=='GAME_OVER': return e,am,o,False
                if o.levels_completed>before:
                    if i!=len(seq)-1: return e,am,o,False
                    break
            if o is None or o.levels_completed<=before: return e,am,o,False
        if o.levels_completed!=TARGET_LEVEL: return e,am,o,False
        if self.scene is None:
            self.scene=largest_bbox(grid(o)); self.root=sig(o,self.scene)
        return e,am,o,True
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except: return None

def shortest_path(start,pred,edges):
    if start==pred: return []
    q=deque([start]); prev={start:None}; pa={}
    while q:
        s=q.popleft()
        for a,t in edges.get(s,{}).items():
            if t in ('TERM','GOAL') or not isinstance(t,str): continue
            if t not in prev:
                prev[t]=s; pa[t]=a
                if t==pred:
                    out=[]; c=t
                    while prev[c] is not None:
                        out.append(pa[c]); c=prev[c]
                    return list(reversed(out))
                q.append(t)
    return None

def path_to_nearest_frontier(start,edges,states):
    q=deque([start]); prev={start:None}; pa={}
    while q:
        s=q.popleft()
        if any(a not in edges[s] for a in ACTIONS):
            out=[]; c=s
            while prev[c] is not None:
                out.append(pa[c]); c=prev[c]
            return list(reversed(out)),s
        for a,t in edges.get(s,{}).items():
            if t in ('TERM','GOAL') or not isinstance(t,str): continue
            if t not in prev:
                prev[t]=s; pa[t]=a; q.append(t)
    return None,None

def verify(seq):
    K=Kernel(); e,am,o,ok=K.fresh()
    if not ok:
        K.close(); return {'ok':False,'where':'prefix'}
    before=o.levels_completed
    for i,a in enumerate(seq):
        o=e.step(am[a],data={},reasoning={'mode':'independent_level4_verification'})
        K.env_actions+=1
        if o is None or sname(o)=='GAME_OVER':
            score=K.close(); return {'ok':False,'where':'terminal','at':i+1,'score':score}
        if o.levels_completed>before:
            score=K.close()
            return {'ok':i==len(seq)-1,'where':'goal','at':i+1,
                    'levels_completed':o.levels_completed,'score':score}
    score=K.close()
    return {'ok':False,'where':'no_goal','levels_completed':o.levels_completed,'score':score}

def main():
    K=Kernel(); e,am,o,ok=K.fresh()
    if not ok: raise RuntimeError('compiled self failed')
    root=K.root; cur=root
    edges=defaultdict(dict); states={root}
    exploratory_edges=0; navigation_edges=0; collisions=0; terminal_events=0
    resets=0; goal_source=None; goal_action=None
    max_steps=250000

    for step in range(1,max_steps+1):
        unknown=[a for a in ACTIONS if a not in edges[cur]]
        exploratory=bool(unknown)

        if exploratory:
            a=unknown[0]
        else:
            nav,target=path_to_nearest_frontier(cur,edges,states)
            if nav:
                a=nav[0]
            else:
                # No reachable frontier from the current present. Re-enter from
                # the protected compiled self and continue graph closure there.
                e,am,o,ok=K.fresh(); resets+=1
                if not ok: break
                cur=root
                nav,target=path_to_nearest_frontier(cur,edges,states)
                if target is None:
                    print('GRAPH_FRONTIER_CLOSED',json.dumps({'step':step,'states':len(states),
                        'qualified_edges':sum(len(v) for v in edges.values())},sort_keys=True))
                    break
                if not nav:
                    continue
                a=nav[0]

        before=cur
        predicted=edges[before].get(a)
        z=e.step(am[a],data={},reasoning={'mode':'directed_living_frontier',
                                          'exploratory':exploratory,'step':step})
        K.env_actions+=1

        if z is None or sname(z)=='GAME_OVER':
            outcome='TERM'
            if predicted is not None and predicted!=outcome:
                collisions+=1
                print('COLLISION',json.dumps({'step':step,'state':before,'action':a,
                    'old':predicted,'new':'TERM'},sort_keys=True))
                break
            if predicted is None:
                edges[before][a]='TERM'; exploratory_edges+=1; terminal_events+=1
            else:
                navigation_edges+=1
            e,am,o,ok=K.fresh(); resets+=1
            if not ok: break
            cur=root
            continue

        if z.levels_completed>TARGET_LEVEL:
            if predicted is not None and predicted!='GOAL':
                collisions+=1
                print('COLLISION',json.dumps({'step':step,'state':before,'action':a,
                    'old':predicted,'new':'GOAL'},sort_keys=True))
                break
            edges[before][a]='GOAL'
            goal_source=before; goal_action=a
            print('GOAL_OBSERVED',json.dumps({'step':step,'states':len(states),
                'qualified_edges':sum(len(v) for v in edges.values()),
                'exploratory_edges':exploratory_edges+1,'navigation_edges':navigation_edges},sort_keys=True))
            break

        ns=sig(z,K.scene)
        if predicted is not None and predicted!=ns:
            collisions+=1
            print('COLLISION',json.dumps({'step':step,'state':before,'action':a,
                'old':predicted,'new':ns},sort_keys=True))
            break

        if predicted is None:
            edges[before][a]=ns; exploratory_edges+=1; states.add(ns)
        else:
            navigation_edges+=1
        cur=ns; o=z

        if step%2000==0:
            totalq=sum(len(v) for v in edges.values())
            frontier=sum(4-len(edges[s]) for s in states)
            print('LEDGER',json.dumps({'step':step,'states':len(states),
                'qualified_edges':totalq,'unqualified_edges':frontier,
                'exploratory_edges':exploratory_edges,'navigation_edges':navigation_edges,
                'collisions':collisions,'episodes':K.episodes,'resets':resets,
                'environment_actions':K.env_actions},sort_keys=True))

    candidate=None
    if goal_source is not None:
        p=shortest_path(root,goal_source,edges)
        if p is not None: candidate=p+[goal_action]

    discovery_score=K.close()
    q=verify(candidate) if candidate is not None else {'ok':False}
    result={'classification':'ARC3_LEVEL4_LIVING_DIRECTED_TWO_SCALAR_LEDGER',
        'goal_observed':goal_source is not None,
        'candidate_depth':None if candidate is None else len(candidate),
        'candidate_sequence':candidate,'states':len(states),
        'qualified_edges':sum(len(v) for v in edges.values()),
        'unqualified_edges':sum(4-len(edges[s]) for s in states),
        'exploratory_edges':exploratory_edges,'navigation_edges':navigation_edges,
        'collisions':collisions,'terminal_events':terminal_events,
        'episodes':K.episodes,'resets':resets,'environment_actions':K.env_actions,
        'discovery_score':discovery_score,'independent_verification':q,
        'scene':list(K.scene)}
    with open('arc3_developmental_v28_living_directed_frontier_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_LIVING_DIRECTED_LEDGER_BREAKTHROUGH')
    elif collisions:
        print('CERTIFIED_NEXT_LEVEL4_CAUSAL_RESIDUAL_FROM_DIRECTED_LEDGER')
    elif goal_source is not None:
        print('LEVEL4_DIRECTED_LEDGER_GOAL_FAILED_REPLAY')
    else:
        print('LEVEL4_DIRECTED_LEDGER_FRONTIER')

if __name__=='__main__': main()
