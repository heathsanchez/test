#!/usr/bin/env python3
import argparse,heapq,json,re,sys,time
from collections import defaultdict,deque
from pathlib import Path


def parse_submission(path,cid):
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
        if m and m.group(1)==cid:
            return list(json.loads(m.group(2)))
    raise KeyError(cid)


def replay(core,state,path):
    s=state
    for m in path:
        s=core.apply_move(s,m)
    return s


def word_features(w):
    ex=[0,0]
    turns=0
    same=0
    for i,x in enumerate(w):
        j=abs(x)-1
        if 0 <= j < 2:
            ex[j]+=1 if x>0 else -1
        if i:
            if abs(w[i-1]) != abs(x): turns+=1
            else: same+=1
    cyc_cancel = int(bool(w) and len(w)>1 and w[0]==-w[-1])
    return (len(w),abs(ex[0]),abs(ex[1]),turns,same,cyc_cancel)


def motif(state):
    # Deliberately coarser than exact presentation identity.  Relator order,
    # relator inversion and generator sign are quotiented out in the summary.
    fs=sorted(word_features(tuple(w)) for w in state)
    lens=sorted(len(w) for w in state)
    total=sum(lens)
    balance=abs(lens[0]-lens[-1]) if lens else 0
    return (tuple(fs),total,balance)


def coarse(m):
    fs,total,balance=m
    # Quantise the high-variance coordinates so nearby proof shapes share a bucket.
    q=[]
    for f in fs:
        ln,e0,e1,turns,same,cyc=f
        q.append((ln//2,e0//2,e1//2,turns//2,same//2,cyc))
    return (tuple(q),total//3,balance//3)


def mdist(a,b):
    af,at,ab=a; bf,bt,bb=b
    if len(af)!=len(bf): return 10**9
    d=abs(at-bt)+abs(ab-bb)
    for x,y in zip(af,bf):
        d += sum(abs(i-j) for i,j in zip(x,y))
    return d


def bounded_frontier(core,start,moves,depth,cap,node_cap,target_motif=None):
    seen={start:()}
    layers=[[start]]
    ranked=[]
    for dep in range(depth+1):
        layer=layers[-1]
        for s in layer:
            mm=motif(s)
            score=mdist(mm,target_motif) if target_motif is not None else 0
            ranked.append((score,dep,s,seen[s],mm,coarse(mm)))
        if dep==depth: break
        nxt=[]
        for s in layer:
            p=seen[s]
            for m in moves:
                n=core.apply_move(s,m)
                if sum(map(len,n))>cap or n in seen: continue
                seen[n]=p+(m,)
                nxt.append(n)
                if len(seen)>=node_cap: break
            if len(seen)>=node_cap: break
        layers.append(nxt)
        if not nxt or len(seen)>=node_cap: break
    ranked.sort(key=lambda z:(z[0],z[1]))
    return seen,ranked


def local_bidir(core,src,dst,moves,half_depth,cap,node_cap=70000):
    if src==dst:return []
    f={src:()}; b={dst:()}; fq=[src]; bq=[dst]
    def expand(front,own,other,forward):
        new=[]
        for s in front:
            p=own[s]
            for m in moves:
                n=core.apply_move(s,m)
                if sum(map(len,n))>cap or n in own: continue
                np=p+(m,); own[n]=np
                if n in other:
                    if forward:
                        tail=other[n]
                        return list(np+tuple(core.INVERSE_MOVE[x] for x in reversed(tail))),[]
                    head=other[n]
                    return list(head+tuple(core.INVERSE_MOVE[x] for x in reversed(np))),[]
                new.append(n)
                if len(own)+len(other)>=node_cap:return None,new
        return None,new
    for _ in range(half_depth):
        hit,fq=expand(fq,f,b,True)
        if hit is not None:return hit
        hit,bq=expand(bq,b,f,False)
        if hit is not None:return hit
        if not fq and not bq:break
        if len(f)+len(b)>=node_cap:break
    return None


def motif_bridge(core,src,dst,moves,front_depth,front_cap,local_depth,total_cap,pair_cap):
    sm=motif(src); dm=motif(dst)
    fs,fr=bounded_frontier(core,src,moves,front_depth,total_cap,front_cap,dm)
    bs,br=bounded_frontier(core,dst,moves,front_depth,total_cap,front_cap,sm)
    buckets=defaultdict(list)
    for score,dep,s,p,m,c in br:
        buckets[c].append((score,dep,s,p,m))
    candidates=[]
    for score,dep,s,p,m,c in fr:
        for q in buckets.get(c,())[:6]:
            candidates.append((mdist(m,q[4]),dep+q[1],s,p,q[2],q[3],m,q[4]))
    if not candidates:
        # fall back to nearest motif pairs, still bounded and prospectively frozen
        topf=fr[:80]; topb=br[:80]
        for _,df,s,p,m,_ in topf:
            best=sorted(((mdist(m,mb),db,t,pb,mb) for _,db,t,pb,mb,_ in topb),key=lambda z:z[0])[:3]
            for d,db,t,pb,mb in best:candidates.append((d,df+db,s,p,t,pb,m,mb))
    candidates.sort(key=lambda z:(z[0],z[1]))
    tested=0
    for d,_,s,pf,t,pb,mf,mb in candidates[:pair_cap]:
        tested+=1
        local=local_bidir(core,s,t,moves,local_depth,total_cap)
        if local is None:continue
        tail=[core.INVERSE_MOVE[x] for x in reversed(pb)]
        path=list(pf)+local+tail
        if replay(core,src,path)==dst:
            return path,{"tested_pairs":tested,"motif_distance":d,"front_states":len(fs),"back_states":len(bs)}
    return None,{"tested_pairs":tested,"front_states":len(fs),"back_states":len(bs)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--p9-solution',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--front-depth',type=int,default=4)
    ap.add_argument('--front-cap',type=int,default=90000)
    ap.add_argument('--local-depth',type=int,default=3)
    ap.add_argument('--extra-total',type=int,default=18)
    ap.add_argument('--pair-cap',type=int,default=180)
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    acc=Path(a.acc_root); sys.path.insert(0,str(acc/'competition/tools'))
    from verifier import core,stable_core
    manifest=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    limits=manifest['limits']; byid={c['challenge_id']:c for c in manifest['challenges']}
    ids=['ac-09633','ac-01821','ac-01684']
    states={cid:tuple(tuple(w) for w in byid[cid]['initial_relators']) for cid in ids}
    p9=parse_submission(a.p9_solution,'ac-09633')
    assert core.verify(byid['ac-09633'],p9,byid['ac-09633']['move_spec_version'],limits)['ok']
    moves=list(range(core.NUM_MOVES))
    evidence=[]; bridges={}
    for src,dst in [('ac-01821','ac-09633'),('ac-01684','ac-01821')]:
        cap=max(sum(map(len,states[src])),sum(map(len,states[dst])))+a.extra_total
        t=time.time()
        path,meta=motif_bridge(core,states[src],states[dst],moves,a.front_depth,a.front_cap,a.local_depth,cap,a.pair_cap)
        meta.update({'src':src,'dst':dst,'found':path is not None,'length':None if path is None else len(path),'seconds':round(time.time()-t,3),'cap':cap})
        evidence.append(meta); bridges[(src,dst)]=path
    b10=bridges[('ac-01821','ac-09633')]; b11=bridges[('ac-01684','ac-01821')]
    candidates={}
    if b10 is not None:candidates['ac-01821']=b10+p9
    if b11 is not None and b10 is not None:candidates['ac-01684']=b11+b10+p9
    rows=[]; lines=[]
    for cid,path in candidates.items():
        c=byid[cid]; v=core.verify(c,path,c['move_spec_version'],limits)
        sid='sac-'+cid[3:]; sc=byid[sid]; sp=path+[16,15]
        sv=stable_core.verify(sc,sp,sc['move_spec_version'],limits)
        if not v.get('ok') or not sv.get('ok'):raise RuntimeError(f'verify fail {cid}')
        rows.append({'challenge_id':cid,'length':len(path),'stable_length':len(sp),'ac_hash':v['certificate_hash'],'stable_hash':sv['certificate_hash']})
        lines += [f"{cid}: {json.dumps(path,separators=(',',':'))}",f"{sid}: {json.dumps(sp,separators=(',',':'))}"]
    rep={'mechanism':'MOTIF_BUCKET_PLUS_LOCAL_EXACT_CLOSURE','bridge_10':None if b10 is None else len(b10),'bridge_11':None if b11 is None else len(b11),'candidate_count':len(rows),'evidence':evidence}
    (out/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    (out/'candidates.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (out/'pending_submission.txt').write_text('\n'.join(lines)+('\n' if lines else ''))
    print('MOTIF_BRIDGE_V5',json.dumps(rep,sort_keys=True))

if __name__=='__main__':main()
