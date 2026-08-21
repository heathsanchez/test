#!/usr/bin/env python3
import argparse, json, random
from pathlib import Path
from collections import Counter


def canon(g): return tuple(tuple(r) for r in g)
def shape(g): return (len(g), len(g[0]) if g else 0)
def rot90(g): return [list(r) for r in zip(*g[::-1])]
def rot180(g): return rot90(rot90(g))
def rot270(g): return rot90(rot180(g))
def flip_h(g): return [r[::-1] for r in g]
def flip_v(g): return g[::-1]
def transpose(g): return [list(r) for r in zip(*g)]
def bg(g): return Counter(x for r in g for x in r).most_common(1)[0][0]
def crop_nonbg(g):
    b=bg(g); pts=[(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x!=b]
    if not pts: return [row[:] for row in g]
    rs=[p[0] for p in pts]; cs=[p[1] for p in pts]
    return [row[min(cs):max(cs)+1] for row in g[min(rs):max(rs)+1]]
def comps(g):
    b=bg(g); h,w=shape(g); seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        if g[r][c]==b or (r,c) in seen: continue
        q=[(r,c)]; seen.add((r,c)); cc=[]
        while q:
          x,y=q.pop(); cc.append((x,y))
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            a,z=x+dx,y+dy
            if 0<=a<h and 0<=z<w and (a,z) not in seen and g[a][z]!=b:
              seen.add((a,z)); q.append((a,z))
        out.append(cc)
    return out
def crop_largest(g):
    cs=comps(g)
    if not cs: return [r[:] for r in g]
    cc=max(cs,key=len); rs=[x for x,_ in cc]; ys=[y for _,y in cc]
    return [row[min(ys):max(ys)+1] for row in g[min(rs):max(rs)+1]]
def scale(g,k): return [[x for x in row for _ in range(k)] for row in g for _ in range(k)]
def tile(g,kr,kc): return [[x for _ in range(kc) for x in row] for _ in range(kr) for row in g]
def hcat(a,b): return [ra+rb for ra,rb in zip(a,b)]
def vcat(a,b): return [r[:] for r in a]+[r[:] for r in b]

class Family:
  def __init__(self,name,fit): self.name=name; self.fit=fit

def fixed(name,fn):
  def fit(task):
    if all(canon(fn(p['input']))==canon(p['output']) for p in task['train']):
      return lambda g: fn(g)
  return Family(name,fit)

def fit_recolor(task):
    mp={}
    for p in task['train']:
      if shape(p['input'])!=shape(p['output']): return None
      for a,b in zip(sum(p['input'],[]),sum(p['output'],[])):
        if a in mp and mp[a]!=b: return None
        mp[a]=b
    if not any(a!=b for a,b in mp.items()): return None
    return lambda g:[[mp.get(x,x) for x in row] for row in g]

def fit_scale(task):
    ks=[]
    for p in task['train']:
      hi,wi=shape(p['input']); ho,wo=shape(p['output'])
      if not hi or ho%hi or wo%wi or ho//hi!=wo//wi: return None
      k=ho//hi
      if k not in (2,3,4) or canon(scale(p['input'],k))!=canon(p['output']): return None
      ks.append(k)
    if len(set(ks))!=1: return None
    k=ks[0]; return lambda g:scale(g,k)

def fit_tile(task):
    pars=[]
    for p in task['train']:
      hi,wi=shape(p['input']); ho,wo=shape(p['output'])
      if not hi or ho%hi or wo%wi: return None
      kr,kc=ho//hi,wo//wi
      if kr*kc<=1 or kr>4 or kc>4 or canon(tile(p['input'],kr,kc))!=canon(p['output']): return None
      pars.append((kr,kc))
    if len(set(pars))!=1:return None
    kr,kc=pars[0]; return lambda g:tile(g,kr,kc)

def fit_recolor_after(fn):
  def fit(task):
    mp={}
    for p in task['train']:
      x=fn(p['input']); y=p['output']
      if shape(x)!=shape(y): return None
      for a,b in zip(sum(x,[]),sum(y,[])):
        if a in mp and mp[a]!=b:return None
        mp[a]=b
    if not mp:return None
    return lambda g:[[mp.get(x,x) for x in row] for row in fn(g)]
  return fit

FAMILIES={f.name:f for f in [
 fixed('identity',lambda g:[r[:] for r in g]), Family('recolor_map',fit_recolor),
 fixed('rot90',rot90),fixed('rot180',rot180),fixed('rot270',rot270),fixed('flip_h',flip_h),fixed('flip_v',flip_v),fixed('transpose',transpose),
 fixed('crop_nonbg',crop_nonbg),fixed('crop_largest',crop_largest), Family('scale_up',fit_scale),Family('tile_repeat',fit_tile),
 fixed('h_mirror_concat',lambda g:hcat(g,flip_h(g))),fixed('v_mirror_concat',lambda g:vcat(g,flip_v(g))),
 Family('rot90_recolor',fit_recolor_after(rot90)),Family('rot180_recolor',fit_recolor_after(rot180)),Family('flip_h_recolor',fit_recolor_after(flip_h)),Family('flip_v_recolor',fit_recolor_after(flip_v)),
]}
BASE=('identity','recolor_map')

def fit_classes(task,names):
  classes={}
  for n in names:
    fn=FAMILIES[n].fit(task)
    if fn is None: continue
    try: outs=tuple(canon(fn(p['input'])) for p in task['test'])
    except Exception: continue
    classes.setdefault(outs,[]).append(n)
  return classes

def verdict(task,names):
  classes=fit_classes(task,names)
  if len(classes)==0:return {'status':'abstain','families':[]}
  if len(classes)>1:return {'status':'ambiguous','families':sum(classes.values(),[])}
  outs,members=next(iter(classes.items()))
  exact=all(canon(p['output'])==outs[i] for i,p in enumerate(task['test']))
  return {'status':'exact' if exact else 'false','families':members}

def load(root):
  d=root/'data'/'evaluation'
  if not d.exists(): d=root/'evaluation'
  return {p.stem:json.loads(p.read_text()) for p in sorted(d.glob('*.json'))}

def main():
  ap=argparse.ArgumentParser(); ap.add_argument('--arc-root',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--n',type=int,default=50); ap.add_argument('--seed',type=int,default=1729)
  a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
  all_tasks=load(a.arc_root); ids=sorted(all_tasks); random.Random(a.seed).shuffle(ids); ids=ids[:a.n]
  active=list(BASE); installed_at={x:0 for x in BASE}; records=[]; transfers=[]; constructions=[]
  dormant=[x for x in FAMILIES if x not in BASE]
  for i,tid in enumerate(ids,1):
    task=all_tasks[tid]; frozen=verdict(task,BASE); before=list(active); dev=verdict(task,before)
    construction=None
    if dev['status']!='exact':
      candidates=[]
      for f in dormant:
        if f in active: continue
        v=verdict(task,[f])
        if v['status']=='exact': candidates.append(f)
      if len(candidates)==1:
        f=candidates[0]; active.append(f); installed_at[f]=i; construction=f; constructions.append({'task':tid,'index':i,'family':f})
        dev=verdict(task,active)
    reused=[f for f in dev.get('families',[]) if installed_at.get(f,10**9)<i and f not in BASE]
    causal=False; ablation=None
    if dev['status']=='exact' and frozen['status']!='exact' and reused:
      without=[f for f in active if f not in reused]; ab=verdict(task,without); causal=ab['status']!='exact'; ablation=ab['status']
      if causal: transfers.append({'task':tid,'index':i,'families':reused,'ablation_status':ab['status']})
    rec={'i':i,'task':tid,'frozen':frozen['status'],'developmental':dev['status'],'active_before':before,'constructed':construction,'reused_prior':reused,'causal_transfer':causal,'ablation':ablation,'active_after':list(active)}
    records.append(rec); print(json.dumps(rec),flush=True)
  summary={'seed':a.seed,'n':len(ids),'task_ids':ids,'families_total':len(FAMILIES),'base_families':list(BASE),'final_active':active,'constructions':constructions,'causal_transfers':transfers,
    'frozen_exact':sum(r['frozen']=='exact' for r in records),'developmental_exact':sum(r['developmental']=='exact' for r in records),'frozen_false':sum(r['frozen']=='false' for r in records),'developmental_false':sum(r['developmental']=='false' for r in records),
    'strong_gate':bool(transfers) and sum(r['developmental']=='false' for r in records)<=sum(r['frozen']=='false' for r in records),
    'claim_scope':'bounded dormant operator-family activation; not open-ended invention'}
  (a.out_dir/'records.json').write_text(json.dumps(records,indent=2)); (a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
