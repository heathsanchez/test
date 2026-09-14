import json, arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
L2=[1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,1,2,2,3,3,4,1,4,1,1,1,1,1,1,1,3,3,3,3,3,3,2,3,2,2,2,2,2]
L3=[1,1,1,1,1,1,1,1,3,2,2,2,2,2,2,2,2,1,1,1,3,3,1,4,4,4,4,4,4,4,1,1,1,3,1,2,1,4,2]
PREFIX=[L1,L2,L3]

def sname(o):
    s=o.state
    return s.name if hasattr(s,'name') else str(s)
def amap(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def reach_l4(env,am):
    o=env.reset()
    for li,seq in enumerate(PREFIX):
        before=o.levels_completed
        for i,a in enumerate(seq):
            o=env.step(am[a],data={},reasoning={'mode':'compiled_prefix','level':li})
            if o is None or sname(o)=='GAME_OVER': return o,False
            if o.levels_completed>before:
                if i!=len(seq)-1: return o,False
                break
        if o.levels_completed<=before: return o,False
    return o,o.levels_completed==3

def test(seq,name):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=reach_l4(env,am)
    if not ok:
        try: arc.close_scorecard()
        except: pass
        return {'name':name,'ok_prefix':False}
    before=o.levels_completed
    for i,a in enumerate(seq):
        o=env.step(am[a],data={},reasoning={'mode':'whole_capability_transfer','source':name})
        if o is None or sname(o)=='GAME_OVER':
            try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: score=None
            return {'name':name,'ok_prefix':True,'goal':False,'terminal':True,'actions':i+1,'score':score}
        if o.levels_completed>before:
            try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
            except: score=None
            return {'name':name,'ok_prefix':True,'goal':True,'actions':i+1,'exact_end':i==len(seq)-1,
                    'levels_completed':o.levels_completed,'score':score}
    try: sc=arc.close_scorecard(); score=None if sc is None else sc.score
    except: score=None
    return {'name':name,'ok_prefix':True,'goal':False,'terminal':False,'actions':len(seq),
            'levels_completed':o.levels_completed,'score':score}

def main():
    out=[test(L1,'L1'),test(L2,'L2'),test(L3,'L3')]
    print('RESULT',json.dumps(out,sort_keys=True))
    wins=[x for x in out if x.get('goal')]
    if wins: print('VERIFIED_LEVEL4_WHOLE_CAPABILITY_TRANSFER',json.dumps(wins,sort_keys=True))
    else: print('WHOLE_CAPABILITY_TRANSFER_REJECTED')

if __name__=='__main__': main()
