from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
import numpy as np
import arc_agi

def grid(obs):
    f=obs.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)

def sname(obs):
    s=obs.state
    return s.name if hasattr(s,'name') else str(s)

def comps(a):
    vals,counts=np.unique(a,return_counts=True)
    bg=int(vals[np.argmax(counts)])
    m=a!=bg; H,W=m.shape; seen=np.zeros_like(m,bool); out=[]
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
            ys=[p[0] for p in pts]; xs=[p[1] for p in pts]
            out.append({'size':len(pts),'bbox':(min(ys),max(ys)+1,min(xs),max(xs)+1)})
    out.sort(key=lambda z:(-z['size'],z['bbox']))
    return bg,out

def crop(a,b):
    y0,y1,x0,x1=b
    return a[y0:y1,x0:x1]

class Projector:
    def __init__(self, scene_bbox, extras=()):
        self.scene_bbox=tuple(scene_bbox)
        self.extras=tuple(tuple(x) for x in extras)
    @property
    def cost(self):
        def area(b): return (b[1]-b[0])*(b[3]-b[2])
        return sum(area(b) for b in (self.scene_bbox,)+self.extras)
    def signature(self,obs):
        a=grid(obs)
        h=hashlib.blake2b(digest_size=12)
        for b in (self.scene_bbox,)+self.extras:
            c=crop(a,b)
            h.update(bytes(b)); h.update(c.tobytes())
        return h.hexdigest()

class Explorer:
    def __init__(self,proj,max_actions=900):
        self.p=proj; self.max_actions=max_actions
        self.edges=defaultdict(dict); self.states=set(); self.actions=0; self.resets=0
        self.terminals=0; self.relocations=0
    def run(self):
        arc=arc_agi.Arcade(); env=arc.make('ls20'); obs=env.reset(); start=obs.levels_completed
        acts=list(env.action_space)
        aids=[getattr(a,'value',i+1) for i,a in enumerate(acts)]
        amap=dict(zip(aids,acts))
        root=self.p.signature(obs); cur=root; self.states.add(root)
        def untried(s): return [a for a in aids if a not in self.edges[s]]
        def path_to_frontier(st):
            q=deque([st]); prev={st:None}; pa={}
            while q:
                s=q.popleft()
                if untried(s):
                    seq=[]; c=s
                    while prev[c] is not None:
                        seq.append(pa[c]); c=prev[c]
                    return list(reversed(seq)),s
                for a,t in self.edges[s].items():
                    if t is not None and t not in prev:
                        prev[t]=s; pa[t]=a; q.append(t)
            return None
        while self.actions<self.max_actions:
            if obs.levels_completed>start:
                return self.finish(arc,True,obs,False)
            if sname(obs)=='GAME_OVER':
                obs=env.reset(); self.resets+=1; cur=self.p.signature(obs); self.states.add(cur); continue
            u=untried(cur)
            if u:
                aid=u[0]; before=cur
                nxt=env.step(amap[aid],data={},reasoning={'mode':'qualify_observation_channel'})
                self.actions+=1
                if nxt is None:
                    self.edges[before][aid]=None; continue
                if nxt.levels_completed>start:
                    obs=nxt; return self.finish(arc,True,obs,False)
                if sname(nxt)=='GAME_OVER':
                    self.edges[before][aid]=None; self.terminals+=1
                    obs=env.reset(); self.resets+=1; cur=self.p.signature(obs); self.states.add(cur); continue
                t=self.p.signature(nxt); self.edges[before][aid]=t; self.states.add(t)
                obs=nxt; cur=t; continue
            plan=path_to_frontier(cur)
            if plan and plan[0]:
                aid=plan[0][0]; before=cur; self.relocations+=1
                nxt=env.step(amap[aid],data={},reasoning={'mode':'frontier_navigation'})
                self.actions+=1
                if nxt is None or sname(nxt)=='GAME_OVER':
                    self.edges[before].pop(aid,None)
                    obs=env.reset(); self.resets+=1; cur=self.p.signature(obs); self.states.add(cur); continue
                if nxt.levels_completed>start:
                    obs=nxt; return self.finish(arc,True,obs,False)
                t=self.p.signature(nxt)
                if self.edges[before].get(aid)!=t:
                    # direct witness that the proposed state is not Markov; keep search open by
                    # invalidating the stale edge rather than silently pretending determinism.
                    self.edges[before].pop(aid,None)
                obs=nxt; cur=t; self.states.add(t); continue
            rplan=path_to_frontier(root)
            if rplan is None:
                return self.finish(arc,False,obs,True)
            seq,target=rplan
            obs=env.reset(); self.resets+=1; cur=self.p.signature(obs); self.states.add(cur)
            for aid in seq:
                if self.actions>=self.max_actions: break
                before=cur
                nxt=env.step(amap[aid],data={},reasoning={'mode':'frontier_replay'})
                self.actions+=1
                if nxt is None or sname(nxt)=='GAME_OVER':
                    self.edges[before].pop(aid,None); break
                if nxt.levels_completed>start:
                    obs=nxt; return self.finish(arc,True,obs,False)
                t=self.p.signature(nxt)
                if self.edges[before].get(aid)!=t:
                    self.edges[before].pop(aid,None)
                obs=nxt; cur=t; self.states.add(t)
        return self.finish(arc,False,obs,False)
    def finish(self,arc,won,obs,exhausted):
        out={'won':won,'levels_completed':obs.levels_completed,'actions':self.actions,'resets':self.resets,
             'unique_states':len(self.states),'qualified_edges':sum(len(v) for v in self.edges.values()),
             'terminal_edges':self.terminals,'exhausted':exhausted,'projection_cost':self.p.cost,
             'extras':[list(x) for x in self.p.extras]}
        try:
            sc=arc.close_scorecard(); out['score']=None if sc is None else sc.score
        except Exception: pass
        return out

def main():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); o=env.reset(); a=grid(o)
    try: arc.close_scorecard()
    except Exception: pass
    bg,cc=comps(a)
    scene=cc[0]
    # anonymous observation candidates: every other non-background connected component
    # with >=3 pixels, ordered by added area then canonical bbox.
    candidates=[]
    for z in cc[1:]:
        if z['size']<3: continue
        b=tuple(z['bbox']); area=(b[1]-b[0])*(b[3]-b[2])
        candidates.append({'size':z['size'],'bbox':b,'area':area})
    candidates.sort(key=lambda z:(z['area'],z['size'],z['bbox']))
    candidates=candidates[:12]
    print('ROOT',json.dumps({'background':bg,'scene':scene,'candidates':candidates},default=list,sort_keys=True))

    baseline=Explorer(Projector(scene['bbox']),max_actions=400).run()
    print('BASELINE_SCENE',json.dumps(baseline,sort_keys=True))

    singles=[]
    winners=[]
    for i,c in enumerate(candidates):
        p=Projector(scene['bbox'],[c['bbox']])
        r=Explorer(p,max_actions=900).run()
        r.update({'candidate_index':i,'candidate_size':c['size'],'candidate_bbox':list(c['bbox'])})
        singles.append(r); print('SINGLE',json.dumps(r,sort_keys=True))
        if r['won']: winners.append((p.cost,i,r,c))

    # Only if no singleton wins, test cheapest pairs. This is still blind and consequence qualified.
    pairs=[]
    if not winners:
        pair_specs=[]
        for i in range(len(candidates)):
            for j in range(i+1,len(candidates)):
                area=candidates[i]['area']+candidates[j]['area']
                pair_specs.append((area,i,j))
        pair_specs.sort()
        for _,i,j in pair_specs[:24]:
            p=Projector(scene['bbox'],[candidates[i]['bbox'],candidates[j]['bbox']])
            r=Explorer(p,max_actions=1200).run()
            r.update({'candidate_pair':[i,j]}); pairs.append(r)
            print('PAIR',json.dumps(r,sort_keys=True))
            if r['won']: winners.append((p.cost,(i,j),r,(candidates[i],candidates[j]))); break

    result={'background':bg,'scene':scene,'candidates':candidates,'scene_baseline':baseline,
            'singles':singles,'pairs':pairs}
    if winners:
        winners.sort(key=lambda x:(x[0],x[2]['actions']))
        w=winners[0]
        result['selected']={'projection_cost':w[0],'candidate':w[1],'result':w[2]}
        # frozen reuse: rerun only the selected channel(s), no candidate search.
        if isinstance(w[1],tuple):
            extras=[candidates[k]['bbox'] for k in w[1]]
        else:
            extras=[candidates[w[1]]['bbox']]
        reuse=Explorer(Projector(scene['bbox'],extras),max_actions=900).run()
        result['compiled_reuse']=reuse
        print('COMPILED_REUSE',json.dumps(reuse,sort_keys=True))
        marker='VERIFIED_EXTERNAL_ARC3_OBSERVATION_GENESIS_AND_COMPILED_LEVEL_ACQUISITION' if reuse['won'] else 'DISCOVERY_WON_REUSE_FAILED'
    else:
        marker='NO_OBSERVATION_CHANNEL_IN_DECLARED_COMPONENT_BASIS_SOLVED_LEVEL1'
    with open('arc3_developmental_v3_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True,default=list)
    print(marker)

if __name__=='__main__': main()
