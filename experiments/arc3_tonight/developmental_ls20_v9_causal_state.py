from __future__ import annotations
import hashlib, heapq, json
from collections import defaultdict
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
    h=hashlib.blake2b(digest_size=10)
    for b in regions:
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

class Evaluator:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); b=o.levels_completed
        for i,a in enumerate(L1):
            o=e.step(am[a],data={},reasoning={'mode':'causal_root'})
            if o.levels_completed>b: break
        if o.levels_completed!=1: raise RuntimeError('L1 failed')
        self.scene=bbox(grid(o)); self.aids=sorted(am)
        self.eval_cache={}
        self.eval_calls=0; self.replayed=0
    def struct(self,o): return hregions(grid(o),(self.scene,RETAINED))
    def eval(self,path):
        p=tuple(path)
        if p in self.eval_cache: return self.eval_cache[p]
        e=self.arc.make('ls20'); am=amap(e); o=e.reset(); b=o.levels_completed
        for i,a in enumerate(L1):
            o=e.step(am[a],data={},reasoning={'mode':'true_rewind_l1'})
            self.replayed+=1
            if o is None or sname(o)=='GAME_OVER':
                r=('BROKEN',None); self.eval_cache[p]=r; return r
            if o.levels_completed>b: break
        if o.levels_completed!=1:
            r=('BROKEN',None); self.eval_cache[p]=r; return r
        for j,a in enumerate(p):
            o=e.step(am[a],data={},reasoning={'mode':'causal_replay','depth':j+1})
            self.replayed+=1
            if o is None:
                r=('TERM',None); self.eval_cache[p]=r; self.eval_calls+=1; return r
            if o.levels_completed>1:
                r=('GOAL',None); self.eval_cache[p]=r; self.eval_calls+=1; return r
            if sname(o)=='GAME_OVER':
                r=('TERM',None); self.eval_cache[p]=r; self.eval_calls+=1; return r
        r=('STATE',self.struct(o)); self.eval_cache[p]=r; self.eval_calls+=1; return r
    def profile(self,path):
        out=[]
        for a in self.aids:
            kind,s=self.eval(tuple(path)+(a,))
            if kind=='STATE': out.append(('S',s))
            elif kind=='GOAL': out.append(('G',))
            elif kind=='TERM': out.append(('T',))
            else: out.append(('X',))
        return tuple(out)
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except Exception: return None

def independent_verify(seq):
    E=Evaluator(); r=E.eval(tuple(seq)); score=E.close()
    return {'ok':r[0]=='GOAL','result_kind':r[0],'actions':len(seq),'score':score}

def main():
    E=Evaluator()
    root_kind,root_s=E.eval(())
    if root_kind!='STATE': raise RuntimeError(root_kind)
    root_p=E.profile(())
    root_key=(root_s,root_p)
    best={root_key:(0,())}
    pq=[(0,(),root_s,root_p)]
    expanded=set(); structural_modes=defaultdict(set); structural_modes[root_s].add(root_p)
    dominated=0; terminals=0; goal=None
    max_depth=132; max_nodes=1200

    while pq and len(expanded)<max_nodes:
        d,path,s,p=heapq.heappop(pq)
        key=(s,p)
        if best.get(key)!=(d,path) or key in expanded: continue
        expanded.add(key); structural_modes[s].add(p)
        for idx,a in enumerate(E.aids):
            outcome=p[idx]
            if outcome[0]=='G':
                goal=path+(a,)
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'causal_states':len(best),
                                                    'structures':len(structural_modes),'expanded':len(expanded),
                                                    'sequence':goal}))
                break
            if outcome[0] in ('T','X'):
                terminals+=1; continue
            ns=outcome[1]; npth=path+(a,); nd=d+1
            if nd>max_depth: continue
            np=E.profile(npth)
            nkey=(ns,np); structural_modes[ns].add(np)
            old=best.get(nkey)
            if old is None or nd<old[0]:
                best[nkey]=(nd,npth); heapq.heappush(pq,(nd,npth,ns,np))
            else:
                dominated+=1
        if goal is not None: break
        if len(expanded)%10==0:
            mult=[len(v) for v in structural_modes.values()]
            print('SEARCH',json.dumps({'expanded':len(expanded),'frontier':len(pq),'causal_states':len(best),
                                       'structures':len(structural_modes),'multi_mode_structures':sum(x>1 for x in mult),
                                       'max_modes':max(mult or [0]),'dominated':dominated,
                                       'max_depth':max(x[0] for x in best.values())}))
    discovery_score=E.close()
    verification=independent_verify(goal) if goal else {'ok':False}
    mode_counts=sorted([len(v) for v in structural_modes.values()],reverse=True)
    result={'classification':'ARC3_CONSEQUENCE_DEFINED_CAUSAL_STATE',
            'goal_found':goal is not None,'goal_depth':None if goal is None else len(goal),
            'goal_sequence':None if goal is None else list(goal),
            'expanded_causal_states':len(expanded),'discovered_causal_states':len(best),
            'structural_states':len(structural_modes),'multi_mode_structures':sum(x>1 for x in mode_counts),
            'max_modes_per_structure':max(mode_counts or [0]),'mode_count_top20':mode_counts[:20],
            'dominated_arrivals':dominated,'terminal_outcomes':terminals,
            'eval_calls':E.eval_calls,'replayed_actions':E.replayed,
            'discovery_score':discovery_score,'independent_verification':verification}
    with open('arc3_developmental_v9_causal_state_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if verification.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL2_CAUSAL_STATE_BREAKTHROUGH')
    elif goal:
        print('CAUSAL_STATE_DISCOVERY_FAILED_REPLAY')
    else:
        print('CAUSAL_STATE_BOUNDED_FRONTIER')

if __name__=='__main__': main()
