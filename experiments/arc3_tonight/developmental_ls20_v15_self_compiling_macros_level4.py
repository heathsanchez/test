from __future__ import annotations
import hashlib, heapq, json
from collections import Counter
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
def hregions(a,regions):
    h=hashlib.blake2b(digest_size=12)
    for b in regions:
        y0,y1,x0,x1=b
        h.update(bytes(b)); h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

def mine_macros(seqs,max_keep=8):
    counts=Counter()
    for seq in seqs:
        for n in range(2,9):
            for i in range(len(seq)-n+1):
                counts[tuple(seq[i:i+n])]+=1
    ranked=[]
    for m,f in counts.items():
        if f<2: continue
        # Full cost is always charged; this score only decides which verified
        # chunks are worth exposing as search constructors.
        gain=(len(m)-1)*(f-1)
        ranked.append((gain,len(m),f,m))
    ranked.sort(key=lambda x:(-x[0],-x[1],-x[2],x[3]))
    chosen=[]
    for gain,n,f,m in ranked:
        # Avoid keeping a macro that is merely a strict prefix of an already
        # selected same-symbol run unless it adds a distinct composition.
        if m in chosen: continue
        chosen.append(m)
        if len(chosen)>=max_keep: break
    return [{'seq':list(m),'len':len(m),'frequency':counts[m],
             'reuse_score':(len(m)-1)*(counts[m]-1)} for m in chosen]

class Evaluator:
    def __init__(self):
        self.arc=arc_agi.Arcade()
        e=self.arc.make('ls20'); am=amap(e)
        o,ok=self.replay_prefix(e,am,count=False)
        if not ok or o.levels_completed!=TARGET_LEVEL:
            raise RuntimeError('failed to establish Level4')
        self.scene=largest_bbox(grid(o)); self.aids=sorted(am)
        self.calls=0; self.replayed=0
    def replay_prefix(self,e,am,count=True):
        o=e.reset()
        for li,seq in enumerate(PREFIX):
            before=o.levels_completed
            for i,a in enumerate(seq):
                o=e.step(am[a],data={},reasoning={'mode':'compiled_self_prefix','level':li})
                if count: self.replayed+=1
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
            o=e.step(am[a],data={},reasoning={'mode':'self_compiled_constructor','depth':j+1})
            self.replayed+=1
            if o is None or sname(o)=='GAME_OVER':
                self.calls+=1; return {'kind':'TERM','depth':j+1}
            if o.levels_completed>TARGET_LEVEL:
                self.calls+=1; return {'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
        self.calls+=1
        return {'kind':'STATE','depth':len(path),'sig':self.sig(o)}
    def close(self):
        try:
            sc=self.arc.close_scorecard(); return None if sc is None else sc.score
        except: return None

def verify(seq):
    E=Evaluator(); r=E.eval(tuple(seq)); score=E.close()
    return {'ok':r.get('kind')=='GOAL' and r.get('depth')==len(seq),
            'result':r,'score':score,'actions':len(seq)}

def main():
    macros=mine_macros(PREFIX)
    constructors=[{'name':f'a{a}','seq':[a],'primitive':True} for a in [1,2,3,4]]
    constructors += [{'name':f'm{i}','seq':m['seq'],'primitive':False} for i,m in enumerate(macros)]
    print('COMPILED_CONSTRUCTORS',json.dumps({'macros':macros,'constructors':constructors},sort_keys=True))

    E=Evaluator(); root=E.eval(())
    if root['kind']!='STATE': raise RuntimeError(root)
    best={root['sig']:(0,())}
    pq=[(0,(),root['sig'])]
    expanded=set(); dominated=0; terminals=0; goal=None
    used_macros=Counter()
    max_cost=180; max_expansions=1200

    while pq and len(expanded)<max_expansions:
        cost,path,s=heapq.heappop(pq)
        if best.get(s)!=(cost,path) or s in expanded: continue
        expanded.add(s)
        if cost>=max_cost: continue

        # Prefer previously compiled constructors at equal eventual cost, but
        # Dijkstra ordering remains by full primitive action cost.
        for c in constructors:
            chunk=tuple(c['seq'])
            if cost+len(chunk)>max_cost: continue
            npth=path+chunk
            r=E.eval(npth)
            if r['kind']=='GOAL':
                # Goal may occur before the end of a macro; truncate to the
                # exact primitive action at which consequence occurred.
                actual=npth[:r['depth']]
                goal=actual
                if not c['primitive']: used_macros[c['name']]+=1
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'expanded':len(expanded),
                    'ledger_entries':len(best),'dominated_histories':dominated,
                    'via_constructor':c['name'],'sequence':goal},sort_keys=True))
                break
            if r['kind']=='TERM':
                terminals+=1; continue
            if r['kind']!='STATE': raise RuntimeError(r)
            ns=r['sig']; nc=cost+len(chunk)
            old=best.get(ns)
            if old is None or nc<old[0]:
                best[ns]=(nc,npth)
                heapq.heappush(pq,(nc,npth,ns))
            else:
                dominated+=1
        if goal is not None: break

        if len(expanded)%25==0:
            print('LEDGER',json.dumps({'expanded':len(expanded),'frontier':len(pq),
                'ledger_entries':len(best),'dominated_histories':dominated,
                'max_cost_seen':max(v[0] for v in best.values()),
                'authority_calls':E.calls},sort_keys=True))

    discovery_score=E.close()
    q=verify(list(goal)) if goal else {'ok':False}
    result={'classification':'ARC3_SELF_OPTIMIZING_LEDGER_WITH_COMPILED_CONSTRUCTORS',
        'macros':macros,'goal_found':goal is not None,
        'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'expanded_ledger_entries':len(expanded),'ledger_entries':len(best),
        'dominated_histories':dominated,'terminal_outcomes':terminals,
        'authority_calls':E.calls,'authority_replayed_actions':E.replayed,
        'used_macros':dict(used_macros),'scene':list(E.scene),
        'discovery_score':discovery_score,'independent_verification':q}
    with open('arc3_developmental_v15_self_compiling_macros_level4_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if q.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL4_SELF_OPTIMIZING_COMPILED_CONSTRUCTOR_TRANSFER')
    elif goal:
        print('LEVEL4_COMPILED_CONSTRUCTOR_DISCOVERY_FAILED_REPLAY')
    else:
        print('LEVEL4_COMPILED_CONSTRUCTOR_FRONTIER')

if __name__=='__main__': main()
