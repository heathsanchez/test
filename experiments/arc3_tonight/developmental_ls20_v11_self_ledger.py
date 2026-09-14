from __future__ import annotations
import hashlib, heapq, json
import numpy as np
import arc_agi

# Already earned and independently replay-qualified capabilities.
L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
COMPILED=[L1,L2]
RETAINED_PROBE=(53,63,1,11)

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
    vals,cnts=np.unique(a,return_counts=True)
    bg=int(vals[np.argmax(cnts)])
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
        h.update(bytes(b))
        h.update(a[y0:y1,x0:x1].tobytes())
    return h.hexdigest()

class EnvironmentAuthority:
    """The environment is only an authority for consequences.

    The kernel never stores or predicts an environment model. For any history it
    wants qualified, this object replays already-compiled capabilities, executes
    that history, and returns only the resulting consequence.
    """
    def __init__(self):
        self.arc=arc_agi.Arcade()
        self.aids=None
        self.target_level=len(COMPILED)
        self.scene=None
        self.eval_cache={}
        self.eval_calls=0
        self.replayed_actions=0
        self.prefix_actions=sum(map(len,COMPILED))
        root=self._evaluate_uncached(())
        if root['kind']!='STATE':
            raise RuntimeError(f'cannot establish target root: {root}')
        self.scene=largest_bbox(root['frame'])
        # Re-evaluate root under the now-frozen representation.
        self.eval_cache.clear()
        root=self.eval(())
        if root['kind']!='STATE': raise RuntimeError(root)
        self.root_sig=root['sig']

    def _replay_compiled(self,env,am):
        o=env.reset()
        for li,seq in enumerate(COMPILED):
            before=o.levels_completed
            for ai,a in enumerate(seq):
                o=env.step(am[a],data={},reasoning={'mode':'compiled_prefix','compiled_level':li})
                self.replayed_actions+=1
                if o is None or sname(o)=='GAME_OVER':
                    return o,False
                if o.levels_completed>before:
                    if ai!=len(seq)-1:
                        return o,False
                    break
            if o is None or o.levels_completed<=before:
                return o,False
        return o,(o.levels_completed==self.target_level)

    def _evaluate_uncached(self,path):
        env=self.arc.make('ls20'); am=amap(env)
        if self.aids is None: self.aids=sorted(am)
        o,ok=self._replay_compiled(env,am)
        if not ok:
            return {'kind':'BROKEN_PREFIX','level':None if o is None else o.levels_completed}
        if not path:
            return {'kind':'STATE','frame':grid(o).copy(),'depth':0}
        for j,a in enumerate(path):
            o=env.step(am[a],data={},reasoning={'mode':'ledger_history','depth':j+1})
            self.replayed_actions+=1
            if o is None:
                return {'kind':'TERM','depth':j+1}
            if o.levels_completed>self.target_level:
                return {'kind':'GOAL','depth':j+1,'levels_completed':o.levels_completed}
            if sname(o)=='GAME_OVER':
                return {'kind':'TERM','depth':j+1}
        return {'kind':'STATE','frame':grid(o).copy(),'depth':len(path)}

    def eval(self,path):
        p=tuple(path)
        if p in self.eval_cache:
            return self.eval_cache[p]
        r=self._evaluate_uncached(p)
        self.eval_calls+=1
        if r['kind']=='STATE' and self.scene is not None:
            r={'kind':'STATE','sig':hregions(r['frame'],(self.scene,RETAINED_PROBE)),
               'depth':r['depth']}
        self.eval_cache[p]=r
        return r

    def close(self):
        try:
            sc=self.arc.close_scorecard()
            return None if sc is None else sc.score
        except Exception:
            return None

class SelfLedger:
    """Smallest present: consequential class -> cheapest verified history."""
    def __init__(self,authority):
        self.A=authority
        root=self.A.eval(())
        self.rep={root['sig']:(0,())}
        self.outcomes={}
        self.expanded=set()
        self.dominated=0
        self.terminals=0
        self.self_returns=0

    def run(self,max_states=4000,max_depth=180):
        root=self.A.root_sig
        pq=[(0,(),root)]
        goal=None

        while pq and len(self.expanded)<max_states:
            cost,path,s=heapq.heappop(pq)
            if self.rep.get(s)!=(cost,path): continue
            if s in self.expanded: continue
            self.expanded.add(s)
            if cost>=max_depth: continue

            if len(self.expanded)%25==0:
                print('LEDGER',json.dumps({
                    'expanded':len(self.expanded),
                    'entries':len(self.rep),
                    'frontier':len(pq),
                    'cost':cost,
                    'dominated_histories':self.dominated,
                    'qualified_outcomes':len(self.outcomes)
                },sort_keys=True))

            for a in self.A.aids:
                npth=path+(a,)
                r=self.A.eval(npth)
                self.outcomes[(s,a)]=r['kind'] if r['kind']!='STATE' else r['sig']

                if r['kind']=='GOAL':
                    goal=npth
                    print('GOAL_DISCOVERED',json.dumps({
                        'depth':len(goal),
                        'expanded':len(self.expanded),
                        'ledger_entries':len(self.rep),
                        'dominated_histories':self.dominated,
                        'sequence':goal
                    }))
                    return goal

                if r['kind']!='STATE':
                    self.terminals+=1
                    continue

                ns=r['sig']
                if ns==s: self.self_returns+=1
                nc=cost+1
                old=self.rep.get(ns)
                if old is None or nc<old[0]:
                    self.rep[ns]=(nc,npth)
                    heapq.heappush(pq,(nc,npth,ns))
                else:
                    self.dominated+=1

        return None

def independent_verify(level3_seq):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o=env.reset()
    total=0
    for li,seq in enumerate(COMPILED):
        before=o.levels_completed
        for ai,a in enumerate(seq):
            o=env.step(am[a],data={},reasoning={'mode':'independent_compiled_prefix','level':li})
            total+=1
            if o is None or sname(o)=='GAME_OVER':
                try: arc.close_scorecard()
                except: pass
                return {'ok':False,'where':f'prefix_{li}','total_actions':total}
            if o.levels_completed>before:
                if ai!=len(seq)-1:
                    try: arc.close_scorecard()
                    except: pass
                    return {'ok':False,'where':f'prefix_{li}_early','total_actions':total}
                break
        if o.levels_completed<=before:
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':f'prefix_{li}_no_goal','total_actions':total}

    before=o.levels_completed
    for i,a in enumerate(level3_seq):
        o=env.step(am[a],data={},reasoning={'mode':'independent_level3_ledger_verification'})
        total+=1
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':'level3_terminal','at':i+1,'total_actions':total}
        if o.levels_completed>before:
            exact=(i==len(level3_seq)-1)
            score=None
            try:
                sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: pass
            return {'ok':exact,'where':'level3_goal','level3_actions':i+1,
                    'total_actions':total,'levels_completed':o.levels_completed,'score':score}
    score=None
    try:
        sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except: pass
    return {'ok':False,'where':'level3_no_goal','total_actions':total,
            'levels_completed':o.levels_completed,'score':score}

def main():
    A=EnvironmentAuthority()
    K=SelfLedger(A)
    goal=K.run()
    discovery_score=A.close()
    verification=independent_verify(goal) if goal else {'ok':False}

    result={
        'classification':'ARC3_SELF_LEDGER_KERNEL',
        'principle':'kernel ledger is the present; environment only qualifies consequences',
        'target_level':3,
        'compiled_prefix_lengths':[len(x) for x in COMPILED],
        'scene':list(A.scene),
        'retained_probe':list(RETAINED_PROBE),
        'goal_found':goal is not None,
        'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'ledger_entries':len(K.rep),
        'expanded_entries':len(K.expanded),
        'qualified_outcomes':len(K.outcomes),
        'dominated_histories':K.dominated,
        'terminal_outcomes':K.terminals,
        'self_returns':K.self_returns,
        'authority_eval_calls':A.eval_calls,
        'authority_replayed_actions':A.replayed_actions,
        'discovery_score':discovery_score,
        'independent_verification':verification
    }
    with open('arc3_developmental_v11_self_ledger_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if verification.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL3_SELF_LEDGER_BREAKTHROUGH')
    elif goal:
        print('SELF_LEDGER_DISCOVERY_FAILED_INDEPENDENT_REPLAY')
    else:
        print('SELF_LEDGER_BOUNDED_FRONTIER')

if __name__=='__main__': main()
