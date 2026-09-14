from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)
BOTTOM=(60,64,12,64)

def grid(o):
    f=o.frame; return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)
def sname(o):
    s=o.state; return s.name if hasattr(s,'name') else str(s)
def amap(env):
    xs=list(env.action_space); return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}
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
def hreg(a,b):
    y0,y1,x0,x1=b
    return hashlib.blake2b(a[y0:y1,x0:x1].tobytes(),digest_size=10).hexdigest()
def hstruct(a,scene):
    h=hashlib.blake2b(digest_size=10)
    for b in (scene,RETAINED):
        y0,y1,x0,x1=b; h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

def calibrate(max_steps=160):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
    if not ok: raise RuntimeError('L1 failed')
    scene=bbox(grid(o)); root_scene=hstruct(grid(o),scene); aid=2
    seen={hreg(grid(o),BOTTOM):0}; seq=[(0,next(iter(seen)),root_scene)]
    repeat=None
    for t in range(1,max_steps+1):
        o=env.step(am[aid],data={},reasoning={'mode':'latent_cycle_calibration'})
        if o is None or sname(o)=='GAME_OVER' or o.levels_completed>1: break
        bh=hreg(grid(o),BOTTOM); sh=hstruct(grid(o),scene)
        seq.append((t,bh,sh))
        if bh in seen:
            repeat={'first':seen[bh],'again':t,'period':t-seen[bh],'hash':bh}
            break
        seen[bh]=t
    try: arc.close_scorecard()
    except: pass
    return {'scene':scene,'phase_by_hash':seen,'repeat':repeat,'sequence':seq,
            'unique_hashes':len(seen),'calibration_steps':len(seq)-1}

class Explorer:
    def __init__(self,phase_by_hash,k,max_actions=16000):
        self.phase_by_hash=phase_by_hash; self.k=k; self.max_actions=max_actions
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
        if not ok: raise RuntimeError('L1 failed')
        scene=bbox(grid(o)); level=o.levels_completed; aids=sorted(am)
        unknown_phase_ids={}; next_unknown=10_000
        def phase(z):
            nonlocal next_unknown
            bh=hreg(grid(z),BOTTOM)
            if bh in self.phase_by_hash: return self.phase_by_hash[bh]%self.k
            if bh not in unknown_phase_ids:
                unknown_phase_ids[bh]=next_unknown; next_unknown+=1
            return unknown_phase_ids[bh]
        def state(z): return (hstruct(grid(z),scene),phase(z))
        edges=defaultdict(dict); states=set(); actions=0; resets=0; nondet=0; episode=[]
        cur=state(o); root_struct=cur[0]; states.add(cur)
        def untried(s): return [a for a in aids if a not in edges[s]]
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
            nonlocal o,cur,resets,episode
            o=env.reset(); resets+=1; episode=[]; cur=state(o); states.add(cur)
            return cur
        # Root is not a single phase because reset may preserve the latent counter.
        # Search from the actually observed post-reset state each time.
        while actions<self.max_actions and o.levels_completed==level:
            u=untried(cur)
            if u:
                a=u[0]; before=cur
                z=env.step(am[a],data={},reasoning={'mode':'latent_cycle_probe','k':self.k})
                actions+=1; episode.append(a)
                if z is None: edges[before][a]='TERM'; continue
                if z.levels_completed>level: o=z; break
                if sname(z)=='GAME_OVER': edges[before][a]='TERM'; reset(); continue
                nxt=state(z); old=edges[before].get(a)
                if old is not None and old!=nxt: nondet+=1
                edges[before][a]=nxt; states.add(nxt); o=z; cur=nxt; continue
            fp=frontier(cur)
            if fp and fp[0]:
                a=fp[0][0]; before=cur
                z=env.step(am[a],data={},reasoning={'mode':'latent_cycle_nav','k':self.k})
                actions+=1; episode.append(a)
                if z is None or sname(z)=='GAME_OVER': edges[before].pop(a,None); reset(); continue
                if z.levels_completed>level: o=z; break
                nxt=state(z)
                if edges[before].get(a)!=nxt: nondet+=1; edges[before].pop(a,None)
                states.add(nxt); o=z; cur=nxt; continue
            # Current reachable component is exhausted. Reset to whatever true latent
            # phase the environment now exposes and continue from there.
            oldcur=cur; reset()
            if cur==oldcur and frontier(cur) is None:
                break
        won=o.levels_completed>level
        out={'k':self.k,'won':won,'actions':actions,'states':len(states),
             'edges':sum(len(v) for v in edges.values()),'nondet':nondet,'resets':resets,
             'unknown_phase_hashes':len(unknown_phase_ids)}
        if won: out['candidate_sequence']=episode; out['candidate_actions']=len(episode)
        try: sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
        except: pass
        return out

def main():
    cal=calibrate()
    print('CALIBRATION',json.dumps({k:v for k,v in cal.items() if k not in ('phase_by_hash','sequence')},default=list,sort_keys=True))
    # How often does the main scene change during an otherwise inert calibration?
    scene_runs=[]; last=None; start=0
    for t,bh,sh in cal['sequence']:
        if last is None: last=sh; start=t
        elif sh!=last:
            scene_runs.append({'from':start,'to':t-1,'hash':last}); last=sh; start=t
    if last is not None: scene_runs.append({'from':start,'to':cal['sequence'][-1][0],'hash':last})
    print('CALIBRATION_SCENE_RUNS',json.dumps(scene_runs,sort_keys=True))
    period=cal['repeat']['period'] if cal['repeat'] else cal['unique_hashes']
    candidates=[]
    for k in [22,11,33,66,period,3,6,2,1]:
        if k>0 and k not in candidates and (period%k==0 or k==period): candidates.append(k)
    trials=[]
    for k in candidates:
        r=Explorer(cal['phase_by_hash'],k).run(); trials.append(r)
        print('LATENT_PHASE_TRIAL',json.dumps(r,sort_keys=True))
        if r['won']: break
    result={'classification':'ARC3_OBSERVED_LATENT_CYCLE_FACTORING',
            'calibration':{k:v for k,v in cal.items() if k not in ('phase_by_hash','sequence')},
            'scene_runs':scene_runs,'candidates':candidates,'trials':trials}
    with open('arc3_developmental_v10_latent_cycle_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True,default=list)
    wins=[r for r in trials if r['won']]
    if wins: print('VERIFIED_EXTERNAL_ARC3_LEVEL2_LATENT_CYCLE_BREAKTHROUGH',json.dumps(wins[0],sort_keys=True))
    else: print('LATENT_CYCLE_FACTORED_FRONTIER')

if __name__=='__main__': main()
