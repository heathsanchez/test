from __future__ import annotations
import json, os, hashlib
from itertools import product
import numpy as np
import arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
L3=[1,1,1,1,1,1,1,1,3,2,2,2,2,2,2,2,2,1,1,1,3,3,1,4,4,4,4,4,4,4,1,1,1,3,1,2,1,4,2]
PREFIX=[L1,L2,L3]
TARGET_LEVEL=3
ACTIONS=(1,2,3,4)
MAX_TEST_DEPTH=4
SHARD=int(os.environ["ARC_SHARD_ACTION"])

# First certified Level-4 collision witness from V21.
ROW_A=[1,3,3,3]
ROW_B=[1,3,3,3,3,2,2,2,2,1,4,4,4,4,2,3,2,1,3,2,1,3,2,3,3,2,2,2,2,2,2,2,2,2,3,3,2,1,1,3,3,2,1,1,4,2,3,2,1,4,4,1,2,3,3,2,1,4,1,2,4,4,1,2,3,3,3,3,1,4,1,2,4,1,2,4,4,1,2,3,3,3,2,1,1]

def sname(o):
    s=o.state
    return s.name if hasattr(s,'name') else str(s)

def amap(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def frame(o):
    f=o.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)

def advance_to_level4(arc):
    env=arc.make('ls20'); am=amap(env); o=env.reset(); n=0
    for li,seq in enumerate(PREFIX):
        before=o.levels_completed
        for i,a in enumerate(seq):
            o=env.step(am[a],data={},reasoning={'mode':'protected_compiled_prefix','level':li})
            n+=1
            if o is None or sname(o)=='GAME_OVER':
                return env,am,o,False,n
            if o.levels_completed>before:
                if i!=len(seq)-1: return env,am,o,False,n
                break
        if o is None or o.levels_completed<=before: return env,am,o,False,n
    return env,am,o,o.levels_completed==TARGET_LEVEL,n

def replay_row(row):
    arc=arc_agi.Arcade(); env,am,o,ok,n=advance_to_level4(arc)
    if not ok:
        try: arc.close_scorecard()
        except: pass
        return {'ok':False,'where':'prefix'}
    for i,a in enumerate(row):
        o=env.step(am[a],data={},reasoning={'mode':'replay_collision_row','at':i+1})
        n+=1
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':'row_terminal','at':i+1,'actions':n}
        if o.levels_completed>TARGET_LEVEL:
            try: arc.close_scorecard()
            except: pass
            return {'ok':False,'where':'row_already_goal','at':i+1,'actions':n}
    a=frame(o)
    out={'ok':True,'levels_completed':o.levels_completed,'actions':n,
         'frame_counts':{str(int(v)):int(c) for v,c in zip(*np.unique(a,return_counts=True))},
         'bottom_counts':{str(int(v)):int(c) for v,c in zip(*np.unique(a[61:63,:],return_counts=True))}}
    try: arc.close_scorecard()
    except: pass
    return out

def evaluate(row,test):
    arc=arc_agi.Arcade(); env,am,o,ok,n=advance_to_level4(arc)
    if not ok:
        try: arc.close_scorecard()
        except: pass
        return {'kind':'BROKEN_PREFIX','goal':False,'actions':n}
    for a in row:
        o=env.step(am[a],data={},reasoning={'mode':'goal_kernel_row_replay'})
        n+=1
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'kind':'ROW_TERM','goal':False,'actions':n}
        if o.levels_completed>TARGET_LEVEL:
            try: arc.close_scorecard()
            except: pass
            return {'kind':'ROW_GOAL','goal':True,'actions':n}
    for i,a in enumerate(test):
        o=env.step(am[a],data={},reasoning={'mode':'goal_kernel_probe','probe_depth':len(test),'at':i+1})
        n+=1
        if o is None or sname(o)=='GAME_OVER':
            try: arc.close_scorecard()
            except: pass
            return {'kind':'TERM','goal':False,'at':i+1,'actions':n}
        if o.levels_completed>TARGET_LEVEL:
            try: arc.close_scorecard()
            except: pass
            return {'kind':'GOAL','goal':True,'at':i+1,'actions':n}
    a=frame(o)
    full_hash=hashlib.blake2b(a.tobytes(),digest_size=12).hexdigest()
    try: arc.close_scorecard()
    except: pass
    return {'kind':'NO_GOAL','goal':False,'actions':n,'frame_hash':full_hash}

def tests_for_shard():
    # Empty test is common and checked by shard 1 only.
    if SHARD==1:
        yield ()
    for depth in range(1,MAX_TEST_DEPTH+1):
        for tail in product(ACTIONS, repeat=depth-1):
            yield (SHARD,)+tail

def main():
    ra=replay_row(ROW_A); rb=replay_row(ROW_B)
    print('ROW_REPLAY',json.dumps({'A':ra,'B':rb},sort_keys=True))
    if not ra.get('ok') or not rb.get('ok'):
        print('ROWS_NOT_INDEPENDENTLY_REPLAYABLE')
        return

    tested=0; env_differences=0; goal_separator=None; first_env_difference=None
    by_depth={}
    for t in tests_for_shard():
        ea=evaluate(ROW_A,t); eb=evaluate(ROW_B,t); tested+=1
        d=len(t)
        z=by_depth.setdefault(str(d),{'tests':0,'goal_separators':0,'environment_differences':0})
        z['tests']+=1
        env_diff = (ea['kind']!=eb['kind']) or (ea.get('frame_hash')!=eb.get('frame_hash'))
        if env_diff:
            env_differences+=1; z['environment_differences']+=1
            if first_env_difference is None:
                first_env_difference={'test':list(t),'A':ea,'B':eb}
        if bool(ea.get('goal')) != bool(eb.get('goal')):
            z['goal_separators']+=1
            goal_separator={'test':list(t),'A':ea,'B':eb,'depth':len(t)}
            print('GOAL_SEPARATOR',json.dumps(goal_separator,sort_keys=True))
            break
        if tested%25==0:
            print('PROGRESS',json.dumps({'shard':SHARD,'tested':tested,'depth':len(t),
                                         'environment_differences':env_differences},sort_keys=True))

    result={'classification':'ARC3_LEVEL4_GOAL_KERNEL_COLLISION_PROBE_WITH_FRAME_DIAGNOSTIC',
            'shard_first_action':SHARD,'max_test_depth':MAX_TEST_DEPTH,
            'tested_columns':tested,'goal_separator_found':goal_separator is not None,
            'goal_separator':goal_separator,'environment_differences':env_differences,
            'first_environment_difference':first_env_difference,
            'by_depth':by_depth,'row_A_len':len(ROW_A),'row_B_len':len(ROW_B)}
    with open(f'arc3_v31b_goal_kernel_collision_probe_{SHARD}.json','w') as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print('RESULT',json.dumps(result,sort_keys=True))
    if goal_separator:
        print('VERIFIED_BOUNDED_GOAL_CONSEQUENCE_SEPARATOR')
    elif env_differences:
        print('ENVIRONMENTAL_DIFFERENCE_WITHOUT_BOUNDED_GOAL_SEPARATOR')
    else:
        print('NO_BOUNDED_SEPARATOR_OBSERVED')

if __name__=='__main__':
    main()
