import json, hashlib, numpy as np, arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]
RETAINED=(53,63,1,11)
BOTTOM=(60,64,12,64)
SCENE=(5,55,9,59)

def grid(o):
    f=o.frame; return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.uint8)
def sname(o):
    s=o.state; return s.name if hasattr(s,'name') else str(s)
def amap(env):
    xs=list(env.action_space); return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}
def to_l2(env,am):
    o=env.reset(); b=o.levels_completed
    for i,a in enumerate(L1):
        o=env.step(am[a],data={})
        if o.levels_completed>b: return o,(i==len(L1)-1)
    return o,False
def hcrop(a,b):
    y0,y1,x0,x1=b
    return hashlib.blake2b(a[y0:y1,x0:x1].tobytes(),digest_size=8).hexdigest()
def counts(a,b):
    y0,y1,x0,x1=b; z=a[y0:y1,x0:x1]; v,c=np.unique(z,return_counts=True)
    return {int(x):int(n) for x,n in zip(v,c)}
def diff(a,b,region):
    y0,y1,x0,x1=region; x=a[y0:y1,x0:x1]; y=b[y0:y1,x0:x1]
    m=x!=y
    ys,xs=np.where(m)
    r={'n':int(m.sum())}
    if len(ys): r['bbox_local']=[int(ys.min()),int(ys.max()+1),int(xs.min()),int(xs.max()+1)]
    return r
def run(seq):
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env); o,ok=to_l2(env,am)
    assert ok
    root=grid(o).copy()
    traj=[]
    for i,aid in enumerate(seq):
        before=grid(o).copy()
        o=env.step(am[aid],data={})
        after=grid(o).copy()
        traj.append({'i':i+1,'a':aid,'state':sname(o),'lc':o.levels_completed,
                     'scene_hash':hcrop(after,SCENE),'latent_hash':hcrop(after,BOTTOM),
                     'retained_hash':hcrop(after,RETAINED),
                     'scene_diff':diff(before,after,SCENE),'latent_diff':diff(before,after,BOTTOM),
                     'latent_counts':counts(after,BOTTOM)})
        if sname(o)=='GAME_OVER' or o.levels_completed>1: break
    try: arc.close_scorecard()
    except: pass
    return {'seq':seq,'root':{'scene_hash':hcrop(root,SCENE),'latent_hash':hcrop(root,BOTTOM),
                              'retained_hash':hcrop(root,RETAINED),'latent_counts':counts(root,BOTTOM)},
            'traj':traj,'final_scene_diff_from_root':diff(root,grid(o),SCENE),
            'final_latent_diff_from_root':diff(root,grid(o),BOTTOM)}

def main():
    seqs=[]
    for a in [1,2,3,4]:
        for n in [1,2,3,4,8,16,32]:
            seqs.append([a]*n)
    seqs += [[1,2],[2,1],[3,4],[4,3],[1,2,1,2,1,2,1,2],
             [3,4,3,4,3,4,3,4],[1,3,2,4]*4,[1,4,2,3]*4]
    for s in seqs:
        r=run(s)
        print('PROBE',json.dumps(r,sort_keys=True))
if __name__=='__main__': main()
