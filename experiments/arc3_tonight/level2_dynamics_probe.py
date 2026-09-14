import json, numpy as np, arc_agi

L1=[3,3,3,1,1,4,4,1,3,2,2,1,3,2,3,4,4,3,2,2,1,3,4,2,2,3,4,1,2,3,4,4,1,2,3,4,4,1,1,1,1,1,1,1]

def grid(o):
    f=o.frame
    return np.asarray(f[-1] if isinstance(f,list) else f,dtype=np.int16)

def amap(env):
    xs=list(env.action_space)
    return {getattr(a,'value',i+1):a for i,a in enumerate(xs)}

def sname(o):
    s=o.state
    return s.name if hasattr(s,'name') else str(s)

def to_l2(env,am):
    o=env.reset()
    b=o.levels_completed
    for a in L1:
        o=env.step(am[a],data={})
    assert o.levels_completed==b+1
    return o

def diff_report(a,b):
    d=a!=b
    ys,xs=np.where(d)
    out={'changed':int(d.sum())}
    if len(ys):
        out['bbox']=[int(ys.min()),int(ys.max()+1),int(xs.min()),int(xs.max()+1)]
        pairs={}
        for y,x in zip(ys,xs):
            k=f'{int(a[y,x])}>{int(b[y,x])}'
            pairs[k]=pairs.get(k,0)+1
        out['transitions']=dict(sorted(pairs.items(),key=lambda kv:-kv[1])[:12])
        # diff connected components
        H,W=d.shape; seen=np.zeros_like(d,bool); comps=[]
        for y,x in zip(ys,xs):
            if seen[y,x]: continue
            q=[(int(y),int(x))]; seen[y,x]=1; pts=[]
            for cy,cx in q:
                pts.append((cy,cx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=cy+dy,cx+dx
                    if 0<=ny<H and 0<=nx<W and d[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1; q.append((ny,nx))
            yy=[p[0] for p in pts]; xx=[p[1] for p in pts]
            comps.append({'n':len(pts),'bbox':[min(yy),max(yy)+1,min(xx),max(xx)+1]})
        comps.sort(key=lambda z:-z['n'])
        out['components']=comps[:12]
    return out

def main():
    arc=arc_agi.Arcade(); env=arc.make('ls20'); am=amap(env)
    root=to_l2(env,am); rg=grid(root)
    print('L2_ROOT',json.dumps({'shape':list(rg.shape),'colors':dict(zip(*[x.tolist() for x in np.unique(rg,return_counts=True)]))},sort_keys=True))
    for aid in sorted(am):
        o=env.reset()
        assert o.levels_completed==1
        z=env.step(am[aid],data={})
        print('ONE',aid,json.dumps({'state':sname(z),'lc':z.levels_completed,'diff':diff_report(grid(o),grid(z))},sort_keys=True))
    seqs=[[1,1],[2,2],[3,3],[4,4],[1,2],[2,1],[3,4],[4,3],
          [1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4]]
    for seq in seqs:
        o=env.reset(); a0=grid(o).copy(); z=o
        for aid in seq:
            z=env.step(am[aid],data={})
            if sname(z)=='GAME_OVER' or z.levels_completed>1: break
        print('SEQ',seq,json.dumps({'state':sname(z),'lc':z.levels_completed,'diff_from_root':diff_report(a0,grid(z))},sort_keys=True))
    try: arc.close_scorecard()
    except: pass

if __name__=='__main__': main()
