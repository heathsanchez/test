from __future__ import annotations
import hashlib, json
from collections import deque
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)

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

def to_l2(env,am):
    o=env.reset(); before=o.levels_completed
    for i,a in enumerate(L1):
        o=env.step(am[a],data={},reasoning={'mode':'retained_level1'})
        if o is None or sname(o)=='GAME_OVER': return o,False
        if o.levels_completed>before:
            return o,(i==len(L1)-1)
    return o,False

def independent_verify(seq):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env)
    o,ok=to_l2(env,am)
    if not ok:
        try: arc.close_scorecard()
        except: pass
        return {'ok':False,'where':'L1'}
    before=o.levels_completed
    for i,a in enumerate(seq):
        o=env.step(am[a],data={},reasoning={'mode':'independent_resource_quotient_verification'})
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':'terminal','at':i+1}
        if o.levels_completed>before:
            exact=(i==len(seq)-1)
            score=None
            try:
                sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: pass
            return {'ok':exact,'where':'goal','at':i+1,'levels_completed':o.levels_completed,'score':score}
    score=None
    try:
        sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except: pass
    return {'ok':False,'where':'no_goal','levels_completed':o.levels_completed,'score':score}

def main():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env)
    o,ok=to_l2(env,am)
    if not ok: raise RuntimeError('retained L1 route failed')
    level=o.levels_completed
    scene=largest_bbox(grid(o))
    aids=sorted(am)

    def sig(obs):
        return hregions(grid(obs),(scene,RETAINED))

    # Crucial law: the bottom strip is an action/resource clock, not ontology.
    # Every edge is therefore qualified after level-local reset and replay of
    # the cheapest currently known path to the structural state.
    # Prime ARC's level-local checkpoint: immediately after a level transition,
    # reset may still point to the previous checkpoint until one action is taken
    # in the new level. Take one anonymous action, then require reset to recover
    # exactly the structural Level-2 root observed at transition.
    transition_root_sig=sig(o)
    prime_action=aids[0]
    _prime=env.step(am[prime_action],data={},reasoning={'mode':'prime_level2_checkpoint'})
    root_obs=env.reset()
    if root_obs is None or root_obs.levels_completed!=level:
        raise RuntimeError('primed reset did not return Level2 root')
    root=sig(root_obs)
    if root!=transition_root_sig:
        raise RuntimeError('primed reset returned wrong structural root')

    best_path={root:()}
    q=deque([root])
    expanded=set()
    edges={}
    dominated=0
    replay_actions=0
    reset_count=0
    stale_replay=0
    terminal_edges=0
    self_loops=0
    goal=None

    def restore_and_replay(path, expected_sig):
        nonlocal replay_actions,reset_count,stale_replay
        z=env.reset(); reset_count+=1
        if z is None or z.levels_completed!=level:
            return None,False
        for a in path:
            z=env.step(am[a],data={},reasoning={'mode':'cheapest_path_replay'})
            replay_actions+=1
            if z is None or sname(z)=='GAME_OVER' or z.levels_completed>level:
                return z,False
        ok=(sig(z)==expected_sig)
        if not ok: stale_replay+=1
        return z,ok

    max_states=5000
    while q and len(expanded)<max_states and goal is None:
        s=q.popleft()
        if s in expanded: continue
        path=best_path[s]
        expanded.add(s)
        if len(expanded)%25==0:
            print('SEARCH',json.dumps({'expanded':len(expanded),'frontier':len(q),
                'discovered':len(best_path),'depth':len(path),'dominated':dominated,
                'replay_actions':replay_actions,'stale_replay':stale_replay},sort_keys=True))
        for a in aids:
            z,valid=restore_and_replay(path,s)
            if not valid:
                continue
            before=sig(z)
            n=env.step(am[a],data={},reasoning={'mode':'resource_quotient_probe','depth':len(path)+1})
            if n is None:
                terminal_edges+=1; edges[(s,a)]=None; continue
            if n.levels_completed>level:
                goal=path+(a,)
                edges[(s,a)]='GOAL'
                print('GOAL_DISCOVERED',json.dumps({'depth':len(goal),'expanded':len(expanded),
                    'discovered':len(best_path),'replay_actions':replay_actions,
                    'sequence':goal},sort_keys=True))
                break
            if sname(n)=='GAME_OVER':
                terminal_edges+=1; edges[(s,a)]=None; continue
            ns=sig(n); edges[(s,a)]=ns
            if ns==before: self_loops+=1
            np=path+(a,)
            old=best_path.get(ns)
            if old is None:
                best_path[ns]=np; q.append(ns)
            elif len(np)<len(old):
                best_path[ns]=np; q.append(ns)
            else:
                dominated+=1

    discovery_score=None
    try:
        sc=arc.close_scorecard(); discovery_score=None if sc is None else sc.score
    except Exception: pass

    verification=independent_verify(goal) if goal else {'ok':False}
    result={
        'classification':'ARC3_RESOURCE_SEPARATED_STRUCTURAL_QUOTIENT',
        'scene':list(scene),'goal_found':goal is not None,
        'goal_depth':None if goal is None else len(goal),
        'goal_sequence':None if goal is None else list(goal),
        'expanded_structural_states':len(expanded),
        'discovered_structural_states':len(best_path),
        'qualified_edges':len(edges),'dominated_arrivals':dominated,
        'self_loops':self_loops,'terminal_edges':terminal_edges,
        'replay_actions':replay_actions,'reset_count':reset_count,
        'stale_replay_witnesses':stale_replay,
        'discovery_score':discovery_score,
        'independent_verification':verification
    }
    with open('arc3_developmental_v10b_resource_quotient_result.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if verification.get('ok'):
        print('VERIFIED_EXTERNAL_ARC3_LEVEL2_RESOURCE_QUOTIENT_BREAKTHROUGH')
    elif goal:
        print('RESOURCE_QUOTIENT_GOAL_FAILED_INDEPENDENT_REPLAY')
    else:
        print('RESOURCE_QUOTIENT_BOUNDED_FRONTIER')

if __name__=='__main__': main()
