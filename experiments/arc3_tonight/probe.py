import json, os, random, sys, traceback
from dataclasses import asdict, is_dataclass

import arc_agi

def safe(obj):
    if obj is None:
        return None
    if hasattr(obj, 'model_dump'):
        try: return obj.model_dump()
        except Exception: pass
    if is_dataclass(obj):
        try: return asdict(obj)
        except Exception: pass
    if isinstance(obj, (str,int,float,bool,list,dict,tuple)):
        return obj
    out={}
    for k in dir(obj):
        if k.startswith('_'): continue
        try:
            v=getattr(obj,k)
        except Exception:
            continue
        if callable(v): continue
        if k in ('frame','frames','data'):
            try:
                if hasattr(v,'shape'): out[k]={'shape':list(v.shape)}
                elif isinstance(v,list): out[k]={'type':'list','len':len(v)}
                else: out[k]=str(type(v))
            except Exception: out[k]=str(type(v))
        elif isinstance(v,(str,int,float,bool,type(None))): out[k]=v
        elif isinstance(v,(list,tuple)) and len(v)<20: out[k]=[str(x) for x in v]
        else: out[k]=str(type(v))
    return out

def action_payload(a):
    try:
        complex_flag=a.is_complex()
    except Exception:
        complex_flag=False
    return {'x':32,'y':32} if complex_flag else {}

def main():
    print('arc_agi', getattr(arc_agi,'__version__','unknown'))
    arc=arc_agi.Arcade()
    try:
        envs=arc.get_environments()
        print('ENVIRONMENTS', [safe(e) for e in envs][:20])
    except Exception as e:
        print('GET_ENVIRONMENTS_ERROR',repr(e))
    for game in ['ls20','ft09','vc33']:
        print('\n=== GAME',game,'===')
        try:
            env=arc.make(game)
            if env is None:
                print('MAKE_NONE'); continue
            print('ENV_TYPE',type(env))
            try: print('INFO',json.dumps(safe(env.info),default=str)[:5000])
            except Exception as e: print('INFO_ERROR',repr(e))
            try: print('ACTIONS',[str(a) for a in env.action_space])
            except Exception as e: print('ACTIONS_ERROR',repr(e)); continue
            try:
                r=env.reset()
                print('RESET',json.dumps(safe(r),default=str)[:8000])
            except Exception as e: print('RESET_ERROR',repr(e))
            for i,a in enumerate(list(env.action_space)[:min(5,len(env.action_space))]):
                try:
                    obs=env.step(a,data=action_payload(a))
                    print('STEP',i,str(a),json.dumps(safe(obs),default=str)[:8000])
                    try: env.reset()
                    except Exception: pass
                except Exception as e:
                    print('STEP_ERROR',i,str(a),repr(e))
        except Exception as e:
            print('GAME_ERROR',repr(e)); traceback.print_exc()
    try:
        sc=arc.get_scorecard()
        print('SCORECARD',json.dumps(safe(sc),default=str)[:8000])
    except Exception as e: print('SCORECARD_ERROR',repr(e))

if __name__=='__main__': main()
