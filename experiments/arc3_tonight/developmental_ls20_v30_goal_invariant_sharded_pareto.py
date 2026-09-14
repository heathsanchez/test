from __future__ import annotations
import hashlib, heapq, json, os, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
L3=[1,1,1,1,1,1,1,1,3,2,2,2,2,2,2,2,2,1,1,1,3,3,1,4,4,4,4,4,4,4,1,1,1,3,1,2,1,4,2]
PREFIX=[L1,L2,L3]
RETAINED=(53,63,1,11)
TARGET_LEVEL=3
ACTIONS=(1,2,3,4)
SHARD=int(os.environ["ARC_SHARD_ACTION"])
MAX_DEPTH=84
MAX_EXPANSIONS=8000

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
def struct_sig(a,scene):
    h=hashlib.blake2b(digest_size=12)
    for b in (scene,RETAINED):
        y0,y1,x0,x1=b
        h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()
def resources(a):
    return (int(np.sum(a[61:63,:] == 11)), int(np.sum(a[61:63,:] == 8)))

class Authority:
    def __init__(self,workers=4):
        self.arc=arc_agi.Arcade()
        self.make_lock=threading.Lock()
        self.count_lock=threading.Lock()
        self.local=threading.local()
        self.pool=ThreadPoolExecutor(max_workers=workers)
        self.calls=0; self.replayed=0; self.resets=0; self.envs_created=0
        # Freeze scene from independently established Level4 root.
        with self.make_lock:
            e=self.arc.make('ls20')
        am=amap(e)
        o,ok,n=self._prefix(e,am)
        if not ok or o.levels_completed!=TARGET_LEVEL:
            raise RuntimeError('compiled prefix failed')
        self.scene=largest_bbox(grid(o))
        self.aids=sorted(am)

    def _thread_env(self):
        if not hasattr(self.local,'env'):
            with self.make_lock:
                self.local.env=self.arc.make('ls20')
                self.envs_created+=1
            self.local.am=amap(self.local.env)
        return self.local.env,self.local.am

    def _prefix(self,e,am):
        o=e.reset(); n=0
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                n+=1
                if o is None or sname(o)=='GAME_OVER':
                    return o,False,n
                if o.levels_completed>before:
                    if i!=len(seq)-1: return o,False,n
                    break
            if o is None or o.levels_completed<=before:
                return o,False,n
        return o,o.levels_completed==TARGET_LEVEL,n

    def describe(self,o):
        a=grid(o)
        return struct_sig(a,self.scene),resources(a)

    def eval(self,path):
        e,am=self._thread_env()
        o,ok,n=self._prefix(e,am)
        local=n
        if not ok:
            with self.count_lock:
                self.calls+=1; self.replayed+=local; self.resets+=1
            return {'kind':'BROKEN_PREFIX'}
        for j,a in enumerate(path):
            o=e.step(am[a],data={},reasoning={'mode':'goal_invariant_pareto','depth':j+1,'shard':SHARD})
            local+=1
            if o is None or sname(o)=='GAME_OVER':
                with self.count_lock:
                    self.calls+=1; self.replayed+=local; self.resets+=1
                return {'kind':'TERM','depth':j+1}
            if o.levels_completed>TARGET_LEVEL:
                with self.count_lock:
                    self.calls+=1; self.replayed+=local; self.resets+=1
                return {'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
        ss,rr=self.describe(o)
        with self.count_lock:
            self.calls+=1; self.replayed+=local; self.resets+=1
        return {'kind':'STATE','depth':len(path),'struct':ss,'res':rr}

    def eval_children(self,path):
        fut={a:self.pool.submit(self.eval,path+(a,)) for a in ACTIONS}
        return [(a,fut[a].result()) for a in ACTIONS]

    def close(self):
        self.pool.shutdown(wait=True)
        try:
            sc=self.arc.close_scorecard()
            return None if sc is None else sc.score
        except Exception:
            return None

def verify(seq):
    arc=arc_agi.Arcade(); e=arc.make('ls20'); am=amap(e); o=e.reset()
    total=0
    for li,base in enumerate(PREFIX):
        before=o.levels_completed
        for i,a in enumerate(base):
            o=e.step(am[a],data={},reasoning={'mode':'independent_prefix','level':li})
            total+=1
            if o is None or sname(o)=='GAME_OVER':
                try: arc.close_scorecard()
                except: pass
                return {'ok':False,'where':'prefix_terminal','total_actions':total}
            if o.levels_completed>before:
                if i!=len(base)-1:
                    try: arc.close_scorecard()
                    except: pass
                    return {'ok':False,'where':'prefix_early','total_actions':total}
                break
    before=o.levels_completed
    for i,a in enumerate(seq):
        o=e.step(am[a],data={},reasoning={'mode':'independent_goal_verification'})
        total+=1
        if o is None or sname(o)=='GAME_OVER':
            try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: score=None
            return {'ok':False,'where':'terminal','at':i+1,'score':score}
        if o.levels_completed>before:
            exact=i==len(seq)-1
            try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: score=None
            return {'ok':exact,'where':'goal','at':i+1,'levels_completed':o.levels_completed,'score':score}
    try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except: score=None
    return {'ok':False,'where':'no_goal','levels_completed':o.levels_completed,'score':score}

def main():
    A=Authority(workers=4)
    first=(SHARD,)
    root=A.eval(first)
    if root['kind']=='GOAL':
        goal=first
    elif root['kind']!='STATE':
        goal=None
    else:
        labels=defaultdict(list)
        labels[root['struct']].append((1,root['res'][0],root['res'][1],first))
        pq=[(1,first,root['struct'],root['res'][0],root['res'][1])]
        expanded=set(); pareto_pruned=0; labels_removed=0; terminals=0; goal=None

        def alive(s,c,r11,r8,p):
            return any(x[0]==c and x[1]==r11 and x[2]==r8 and x[3]==p for x in labels.get(s,[]))

        while pq and len(expanded)<MAX_EXPANSIONS:
            cost,path,s,r11,r8=heapq.heappop(pq)
            lid=(s,cost,r11,r8,path)
            if lid in expanded or not alive(s,cost,r11,r8,path):
                continue
            expanded.add(lid)
            if cost>=MAX_DEPTH:
                continue
            for a,z in A.eval_children(path):
                npth=path+(a,)
                if z['kind']=='GOAL':
                    goal=npth
                    print('GOAL_DISCOVERED',json.dumps({
                        'shard':SHARD,'depth':len(goal),'expanded_labels':len(expanded),
                        'structural_states':len(labels),'pareto_pruned':pareto_pruned,
                        'sequence':goal},sort_keys=True))
                    break
                if z['kind']=='TERM':
                    terminals+=1; continue
                if z['kind']!='STATE':
                    raise RuntimeError(z)
                ns=z['struct']; nr11,nr8=z['res']; nc=cost+1
                existing=labels[ns]
                if any(x[0] <= nc and x[1] >= nr11 and x[2] >= nr8 for x in existing):
                    pareto_pruned+=1
                    continue
                kept=[]
                for x in existing:
                    if nc <= x[0] and nr11 >= x[1] and nr8 >= x[2]:
                        labels_removed+=1
                    else:
                        kept.append(x)
                kept.append((nc,nr11,nr8,npth)); labels[ns]=kept
                heapq.heappush(pq,(nc,npth,ns,nr11,nr8))
            if goal is not None:
                break
            if len(expanded)%100==0:
                print('LEDGER',json.dumps({
                    'shard':SHARD,'expanded_labels':len(expanded),'frontier':len(pq),
                    'structural_states':len(labels),
                    'retained_pareto_labels':sum(len(v) for v in labels.values()),
                    'pareto_pruned':pareto_pruned,'max_cost':cost,
                    'authority_calls':A.calls,'authority_replayed_actions':A.replayed
                },sort_keys=True))

    score=A.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={
        'classification':'ARC3_LEVEL4_GOAL_INVARIANT_SHARDED_PARETO',
        'shard_first_action':SHARD,
        'goal_found':goal is not None,
        'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'max_depth':MAX_DEPTH,'max_expansions':MAX_EXPANSIONS,
        'authority_calls':A.calls,'authority_replayed_actions':A.replayed,
        'authority_resets':A.resets,'worker_envs_created':A.envs_created,
        'discovery_score':score,'independent_verification':q
    }
    fn=f'arc3_v30_goal_invariant_shard_{SHARD}.json'
    with open(fn,'w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_GOAL_INVARIANT_BREAKTHROUGH')
    elif goal:
        print('GOAL_INVARIANT_DISCOVERY_FAILED_REPLAY')
    else:
        print('GOAL_INVARIANT_SHARD_FRONTIER')

if __name__=='__main__':
    main()
