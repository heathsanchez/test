from __future__ import annotations
import hashlib, heapq, json
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
PREFIX=[L1,L2]
RETAINED=(53,63,1,11)
TARGET_LEVEL=2  # zero-based: begin on public Level 3

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

class FreshEvaluator:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        e=self.arc.make('ls20'); am=amap(e)
        o,ok=self.replay_prefix(e,am,count=False)
        if not ok or o.levels_completed!=TARGET_LEVEL:
            raise RuntimeError(f'prefix failed establishing Level3: {None if o is None else o.levels_completed}')
        self.scene=largest_bbox(grid(o))
        self.aids=sorted(am)
        self.calls=0; self.replayed_actions=0
    def replay_prefix(self,e,am,count=True):
        o=e.reset()
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_prefix','level':li})
                if count: self.replayed_actions+=1
                if o is None or sname(o)=='GAME_OVER': return o,False
                if o.levels_completed>before:
                    if i!=len(seq)-1: return o,False
                    break
            if o is None or o.levels_completed<=before: return o,False
        return o,True
    def sig(self,o):
        return hregions(grid(o),(self.scene,RETAINED))
    def eval(self,path):
        e=self.arc.make('ls20'); am=amap(e)
        o,ok=self.replay_prefix(e,am,count=True)
        if not ok: return {'kind':'BROKEN_PREFIX'}
        for j,a in enumerate(path):
            o=e.step(am[a],data={},reasoning={'mode':'level3_cost_dominance','depth':j+1})
            self.replayed_actions+=1
            if o is None or sname(o)=='GAME_OVER':
                self.calls+=1; return {'kind':'TERM','depth':j+1}
            if o.levels_completed>TARGET_LEVEL:
                self.calls+=1; return {'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
        self.calls+=1
        return {'kind':'STATE','depth':len(path),'sig':self.sig(o)}
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except Exception: return None

def verify(seq):
    E=FreshEvaluator()
    r=E.eval(tuple(seq)); score=E.close()
    return {'ok':r.get('kind')=='GOAL' and r.get('depth')==len(seq),
            'result':r,'score':score,'actions':len(seq)}

def main():
    E=FreshEvaluator()
    root=E.eval(())
    if root['kind']!='STATE': raise RuntimeError(root)
    root_sig=root['sig']
    best={root_sig:(0,())}
    pq=[(0,(),root_sig)]
    expanded=set()
    dominated=0; terminals=0; goal=None
    max_depth=120
    max_expansions=1000

    while pq and len(expanded)<max_expansions:
        d,path,sig=heapq.heappop(pq)
        if best.get(sig)!=(d,path) or sig in expanded: continue
        expanded.add(sig)
        if d>=max_depth: continue
        for a in E.aids:
            npth=path+(a,)
            r=E.eval(npth)
            if r['kind']=='GOAL':
                goal=npth
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'expanded':len(expanded),
                    'structural_states':len(best),'sequence':goal},sort_keys=True))
                break
            if r['kind']=='TERM':
                terminals+=1; continue
            if r['kind']!='STATE':
                raise RuntimeError(r)
            ns=r['sig']; nd=d+1
            old=best.get(ns)
            if old is None or nd<old[0]:
                best[ns]=(nd,npth); heapq.heappush(pq,(nd,npth,ns))
            else:
                dominated+=1
        if goal is not None: break
        if len(expanded)%10==0:
            print('SEARCH',json.dumps({'expanded':len(expanded),'frontier':len(pq),
                'structural_states':len(best),'dominated':dominated,'terminals':terminals,
                'max_depth':max(x[0] for x in best.values())},sort_keys=True))

    discovery_score=E.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={'classification':'ARC3_LEVEL3_COST_AS_RESOURCE_NOT_STATE',
        'scene':list(E.scene),'goal_found':goal is not None,
        'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'expanded_states':len(expanded),'discovered_structural_states':len(best),
        'dominated_arrivals':dominated,'terminal_edges':terminals,
        'fresh_eval_calls':E.calls,'replayed_actions':E.replayed_actions,
        'discovery_score':discovery_score,'independent_verification':q}
    with open('arc3_developmental_v12_level3_cost_dominance_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL3_COST_DOMINANCE_TRANSFER')
    elif goal:
        print('LEVEL3_DISCOVERY_FAILED_INDEPENDENT_REPLAY')
    else:
        print('LEVEL3_COST_DOMINANCE_FRONTIER')

if __name__=='__main__': main()
