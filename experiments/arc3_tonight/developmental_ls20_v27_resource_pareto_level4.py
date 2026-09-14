from __future__ import annotations
import hashlib, heapq, json, threading
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
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()
def resources(a):
    return (int(np.sum(a[61:63,:] == 11)), int(np.sum(a[61:63,:] == 8)))

class Authority:
    def __init__(self,workers=6):
        self.arc=arc_agi.Arcade()
        self.make_lock=threading.Lock(); self.count_lock=threading.Lock()
        e=self.arc.make('ls20'); am=amap(e)
        o,ok=self._prefix(e,am,False)
        if not ok or o.levels_completed!=TARGET_LEVEL: raise RuntimeError('prefix failed')
        self.scene=largest_bbox(grid(o)); self.aids=sorted(am)
        self.calls=0; self.replayed=0
        self.pool=ThreadPoolExecutor(max_workers=workers)
    def _prefix(self,e,am,count=True):
        o=e.reset(); local=0
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                local+=1
                if o is None or sname(o)=='GAME_OVER':
                    if count:
                        with self.count_lock: self.replayed+=local
                    return o,False
                if o.levels_completed>before:
                    if i!=len(seq)-1:
                        if count:
                            with self.count_lock: self.replayed+=local
                        return o,False
                    break
            if o is None or o.levels_completed<=before:
                if count:
                    with self.count_lock: self.replayed+=local
                return o,False
        if count:
            with self.count_lock: self.replayed+=local
        return o,True
    def describe(self,o):
        a=grid(o)
        return struct_sig(a,self.scene), resources(a)
    def eval(self,path):
        with self.make_lock:
            e=self.arc.make('ls20')
        am=amap(e); o,ok=self._prefix(e,am,True)
        if not ok: return {'kind':'BROKEN_PREFIX'}
        local=0
        for j,a in enumerate(path):
            o=e.step(am[a],data={},reasoning={'mode':'resource_pareto_ledger','depth':j+1})
            local+=1
            if o is None or sname(o)=='GAME_OVER':
                with self.count_lock: self.calls+=1; self.replayed+=local
                return {'kind':'TERM','depth':j+1}
            if o.levels_completed>TARGET_LEVEL:
                with self.count_lock: self.calls+=1; self.replayed+=local
                return {'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
        ss,rr=self.describe(o)
        with self.count_lock: self.calls+=1; self.replayed+=local
        return {'kind':'STATE','depth':len(path),'struct':ss,'res':rr}
    def eval_children(self,path):
        fut={a:self.pool.submit(self.eval,path+(a,)) for a in self.aids}
        return [(a,fut[a].result()) for a in self.aids]
    def close(self):
        self.pool.shutdown(wait=True)
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except: return None

def dominates(A,B):
    # A=(cost,r11,r8), B=(cost,r11,r8)
    return A[0] <= B[0] and A[1] >= B[1] and A[2] >= B[2] and A != B

def verify(seq):
    A=Authority(workers=1); r=A.eval(tuple(seq)); score=A.close()
    return {'ok':r.get('kind')=='GOAL' and r.get('depth')==len(seq),
            'result':r,'score':score,'actions':len(seq)}

def main():
    A=Authority(workers=6)
    root=A.eval(())
    if root['kind']!='STATE': raise RuntimeError(root)
    # labels[struct] contains nondominated retained labels keyed by (cost,r11,r8,path)
    labels=defaultdict(list)
    rootlab=(0,root['res'][0],root['res'][1],())
    labels[root['struct']].append(rootlab)
    pq=[(0,(),root['struct'],root['res'][0],root['res'][1])]
    expanded=set()
    pareto_pruned=0; labels_removed=0; terminals=0; goal=None
    max_depth=120; max_expansions=9000

    def alive(struct,cost,r11,r8,path):
        return any(x[0]==cost and x[1]==r11 and x[2]==r8 and x[3]==path for x in labels.get(struct,[]))

    while pq and len(expanded)<max_expansions:
        cost,path,s,r11,r8=heapq.heappop(pq)
        lid=(s,cost,r11,r8,path)
        if lid in expanded or not alive(s,cost,r11,r8,path): continue
        expanded.add(lid)
        if cost>=max_depth: continue

        for a,z in A.eval_children(path):
            npth=path+(a,)
            if z['kind']=='GOAL':
                goal=npth
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'expanded_labels':len(expanded),
                    'structural_states':len(labels),'pareto_pruned':pareto_pruned,
                    'sequence':goal},sort_keys=True))
                break
            if z['kind']=='TERM':
                terminals+=1; continue
            if z['kind']!='STATE': raise RuntimeError(z)

            ns=z['struct']; nr11,nr8=z['res']; nc=cost+1
            candidate=(nc,nr11,nr8,npth)
            triple=(nc,nr11,nr8)
            existing=labels[ns]
            if any((x[0] <= nc and x[1] >= nr11 and x[2] >= nr8) for x in existing):
                pareto_pruned+=1
                continue
            kept=[]
            for x in existing:
                if nc <= x[0] and nr11 >= x[1] and nr8 >= x[2]:
                    labels_removed+=1
                else:
                    kept.append(x)
            kept.append(candidate); labels[ns]=kept
            heapq.heappush(pq,(nc,npth,ns,nr11,nr8))
        if goal is not None: break

        if len(expanded)%50==0:
            nlabels=sum(len(v) for v in labels.values())
            print('LEDGER',json.dumps({'expanded_labels':len(expanded),'frontier':len(pq),
                'structural_states':len(labels),'retained_pareto_labels':nlabels,
                'pareto_pruned':pareto_pruned,'labels_removed':labels_removed,
                'max_cost':max((x[0] for vs in labels.values() for x in vs),default=0),
                'authority_calls':A.calls},sort_keys=True))

    discovery_score=A.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={'classification':'ARC3_LEVEL4_RESOURCE_PARETO_SELF_LEDGER',
        'assumption':'componentwise more of both collision-earned resources is treated as non-worse when action cost is no greater; final path independently replayed',
        'goal_found':goal is not None,'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'expanded_labels':len(expanded),'structural_states':len(labels),
        'retained_pareto_labels':sum(len(v) for v in labels.values()),
        'pareto_pruned':pareto_pruned,'labels_removed':labels_removed,
        'terminal_outcomes':terminals,'authority_calls':A.calls,
        'authority_replayed_actions':A.replayed,'scene':list(A.scene),
        'discovery_score':discovery_score,'independent_verification':q}
    with open('arc3_developmental_v27_resource_pareto_level4_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_RESOURCE_PARETO_BREAKTHROUGH')
    elif goal:
        print('LEVEL4_RESOURCE_PARETO_DISCOVERY_FAILED_REPLAY')
    else:
        print('LEVEL4_RESOURCE_PARETO_FRONTIER')

if __name__=='__main__': main()
