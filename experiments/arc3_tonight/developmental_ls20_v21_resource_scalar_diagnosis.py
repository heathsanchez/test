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
    xs=list(env.action_space); return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}
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
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()
def comps(mask):
    H,W=mask.shape; seen=np.zeros_like(mask,bool); out=[]
    ys,xs=np.where(mask)
    for y,x in zip(ys,xs):
        if seen[y,x]: continue
        q=[(int(y),int(x))]; seen[y,x]=1; pts=[]
        for cy,cx in q:
            pts.append((cy,cx))
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=1; q.append((ny,nx))
        yy=[p[0] for p in pts]; xx=[p[1] for p in pts]
        out.append({'n':len(pts),'bbox':[min(yy),max(yy)+1,min(xx),max(xx)+1]})
    out.sort(key=lambda z:-z['n'])
    return out
class Prior:
    def __init__(self,seqs):
        self.bi=defaultdict(Counter)
        for seq in seqs:
            prev=0
            for a in seq: self.bi[prev][a]+=1; prev=a
    def rank(self,prev,a):
        c=self.bi[prev]; return (c[a]+1)/(sum(c.values())+4)

def fresh():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o=env.reset()
    for li,seq in enumerate(PREFIX):
        before=o.levels_completed
        for i,a in enumerate(seq):
            o=env.step(am[a],data={})
            if o.levels_completed>before: break
    assert o.levels_completed==TARGET_LEVEL
    return arc,env,am,o

def main():
    arc,env,am,o=fresh(); scene=largest_bbox(grid(o)); root=sig(o,scene); P=Prior(PREFIX)
    edges=defaultdict(dict); edge_first={}; state_visits=Counter({root:1}); edge_visits=Counter()
    cur=root; prev_action=0; history=[]

    for step in range(1,500):
        unknown=[a for a in ACTIONS if a not in edges[cur]]
        if unknown:
            a=min(unknown,key=lambda x:(-P.rank(prev_action,x),x))
        else:
            def score(a):
                t=edges[cur][a]
                if t in ('TERM','GOAL'): return (10**12,10**12,-P.rank(prev_action,a),a)
                return (edge_visits[(cur,a)],state_visits[t],-P.rank(prev_action,a),a)
            a=min(ACTIONS,key=score)

        before=cur; pre=grid(o).copy(); pre_hist=tuple(history)
        z=env.step(am[a],data={})
        edge_visits[(before,a)]+=1
        history.append(a)
        if z is None or sname(z)=='GAME_OVER' or z.levels_completed>TARGET_LEVEL:
            print('ENDED_BEFORE_COLLISION',json.dumps({'step':step,'state':None if z is None else sname(z),'lc':None if z is None else z.levels_completed}))
            break
        ns=sig(z,scene)
        old=edges[before].get(a)
        if old is not None and old!=ns:
            first=edge_first[(before,a)]
            fa=first['frame']; diff=fa!=pre
            report={
                'classification':'ARC3_LEVEL4_CAUSAL_COLLISION_MEMORY_GENESIS_WITNESS',
                'step':step,'state_sig':before,'action':a,
                'old_successor':old,'new_successor':ns,
                'first_step':first['step'],'first_history_len':len(first['history']),
                'second_history_len':len(pre_hist),
                'first_history':list(first['history']),'second_history':list(pre_hist),
                'first_suffixes':{str(k):list(first['history'][-k:]) for k in [1,2,3,4,5,8,13,21,34]},
                'second_suffixes':{str(k):list(pre_hist[-k:]) for k in [1,2,3,4,5,8,13,21,34]},
                'full_frame_diff_pixels':int(diff.sum()),
                'full_frame_diff_components':comps(diff)[:20],
                'first_nonretained_hash':hashlib.blake2b(fa.tobytes(),digest_size=12).hexdigest(),
                'second_nonretained_hash':hashlib.blake2b(pre.tobytes(),digest_size=12).hexdigest(),
                'step_delta':step-first['step'],
                'step_mods':{str(m):[first['step']%m,step%m] for m in range(2,33)},
                'bottom_first_rows':fa[60:64,:].tolist(),
                'bottom_second_rows':pre[60:64,:].tolist(),
                'bottom_first_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(fa[60:64,:],return_counts=True))},
                'bottom_second_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(pre[60:64,:],return_counts=True))},
                'row61_first_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(fa[61,:],return_counts=True))},
                'row61_second_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(pre[61,:],return_counts=True))},
                'row62_first_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(fa[62,:],return_counts=True))},
                'row62_second_unique_counts':{str(int(v)):int(n) for v,n in zip(*np.unique(pre[62,:],return_counts=True))}
            }
            # Compare each row/column to locate smallest observational witness.
            report['row_diff_counts']=[int(x) for x in diff.sum(axis=1)]
            report['col_diff_counts']=[int(x) for x in diff.sum(axis=0)]
            with open('arc3_developmental_v21_resource_scalar_result.json','w') as f:
                json.dump(report,f,indent=2,sort_keys=True)
            print('COLLISION_REPORT',json.dumps(report,sort_keys=True))
            print('VERIFIED_EXTERNAL_ARC3_CAUSAL_COLLISION_FORCES_MEMORY_OR_ADDITIONAL_STATE')
            try: arc.close_scorecard()
            except: pass
            return

        if old is None:
            edges[before][a]=ns
            edge_first[(before,a)]={'step':step,'history':pre_hist,'frame':pre}
        cur=ns; o=z; prev_action=a; state_visits[ns]+=1

    try: arc.close_scorecard()
    except: pass
    print('NO_COLLISION_REPRODUCED')

if __name__=='__main__': main()
