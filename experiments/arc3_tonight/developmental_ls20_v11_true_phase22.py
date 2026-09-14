from __future__ import annotations
import hashlib, heapq, json
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)
K=22

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
    h=hashlib.blake2b(digest_size=10)
    for b in (scene,RETAINED):
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

class Fresh:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); b=o.levels_completed
        for i,a in enumerate(L1):
            o=e.step(am[a],data={},reasoning={'mode':'phase22_root'})
            if o.levels_completed>b: break
        if o.levels_completed!=1: raise RuntimeError('L1 root failed')
        self.scene=largest_bbox(grid(o)); self.aids=sorted(am)
        self.cache={}; self.calls=0; self.replayed=0
    def eval(self,path):
        path=tuple(path)
        if path in self.cache: return self.cache[path]
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); b=o.levels_completed
        for i,a in enumerate(L1):
            o=e.step(am[a],data={},reasoning={'mode':'fresh_phase22_l1'})
            self.replayed+=1
            if o is None or sname(o)=='GAME_OVER':
                r=('BROKEN',None); self.cache[path]=r; return r
            if o.levels_completed>b:
                if i!=len(L1)-1:
                    r=('BROKEN_EARLY',None); self.cache[path]=r; return r
                break
        for a in path:
            o=e.step(am[a],data={},reasoning={'mode':'fresh_phase22_path'})
            self.replayed+=1
            if o is None or sname(o)=='GAME_OVER':
                r=('TERM',None); self.cache[path]=r; self.calls+=1; return r
            if o.levels_completed>1:
                r=('GOAL',None); self.cache[path]=r; self.calls+=1; return r
        s=struct_sig(grid(o),self.scene)
        r=('STATE',(s,len(path)%K))
        self.cache[path]=r; self.calls+=1; return r
    def close(self):
        try:
            sc=self.arc.close_scorecard()
            return None if sc is None else sc.score
        except Exception:
            return None

def verify(seq):
    F=Fresh(); r=F.eval(seq); score=F.close()
    return {'ok':r[0]=='GOAL','kind':r[0],'actions':len(seq),'score':score}

def main():
    F=Fresh()
    rk,rstate=F.eval(())
    if rk!='STATE': raise RuntimeError(rk)
    best={rstate:(0,())}
    pq=[(0,(),rstate)]
    expanded=set(); structures=set([rstate[0]])
    dominated=0; terminals=0; goal=None
    max_depth=154
    max_expanded=1200

    while pq and len(expanded)<max_expanded:
        d,path,state=heapq.heappop(pq)
        if best.get(state)!=(d,path) or state in expanded: continue
        expanded.add(state)
        for a in F.aids:
            npth=path+(a,)
            kind,nstate=F.eval(npth)
            if kind=='GOAL':
                goal=npth
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'expanded':len(expanded),
                                                    'phase_states':len(best),'structures':len(structures),
                                                    'sequence':goal}))
                break
            if kind in ('TERM','NONE'):
                terminals+=1; continue
            if kind!='STATE':
                raise RuntimeError(kind)
            structures.add(nstate[0]); nd=d+1
            if nd>max_depth: continue
            old=best.get(nstate)
            if old is None or nd<old[0]:
                best[nstate]=(nd,npth); heapq.heappush(pq,(nd,npth,nstate))
            else:
                dominated+=1
        if goal is not None: break
        if len(expanded)%10==0:
            phases=sorted(set(s[1] for s in best))
            print('SEARCH',json.dumps({'expanded':len(expanded),'frontier':len(pq),
                                       'phase_states':len(best),'structures':len(structures),
                                       'phase_values':phases,'dominated':dominated,
                                       'terminals':terminals,'max_depth':max(x[0] for x in best.values())}))
    discovery_score=F.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={'classification':'ARC3_TRUE_ROOT_PHASE22_COST_DOMINANCE',
            'k':K,'goal_found':goal is not None,'goal_depth':None if goal is None else len(goal),
            'goal_sequence':None if goal is None else list(goal),
            'expanded_states':len(expanded),'discovered_phase_states':len(best),
            'structural_states':len(structures),'dominated_arrivals':dominated,
            'terminal_edges':terminals,'fresh_eval_calls':F.calls,'replayed_actions':F.replayed,
            'discovery_score':discovery_score,'independent_verification':q}
    with open('arc3_developmental_v11_true_phase22_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL2_TRUE_PHASE22_BREAKTHROUGH')
    elif goal:
        print('PHASE22_DISCOVERY_FAILED_REPLAY')
    else:
        print('PHASE22_BOUNDED_FRONTIER')

if __name__=='__main__': main()
