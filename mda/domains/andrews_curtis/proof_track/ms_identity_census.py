#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

GENS=(1,-1,2,-2)

def red(w):
    out=[]
    for x in w:
        if out and out[-1]==-x: out.pop()
        else: out.append(x)
    return tuple(out)
def inv(w): return tuple(-x for x in reversed(tuple(w)))

def phi_letter(img,g):
    return img[g-1] if g>0 else -img[-g-1]
def transform_word(w,img): return tuple(phi_letter(img,x) for x in w)
def syms():
    out=[]
    for perm in ((1,2),(2,1)):
      for s1 in (-1,1):
       for s2 in (-1,1):
        out.append((s1*perm[0],s2*perm[1]))
    return out

def cyclic_orientations(w):
    w=red(w);out=set()
    for base,invflag in ((w,False),(inv(w),True)):
      if not base:
        out.add(((),invflag,0));continue
      for k in range(len(base)):
        out.add((red(base[k:]+base[:k]),invflag,k))
    return out

def wordstr(w):
    return ''.join({1:'x',-1:'X',2:'y',-2:'Y'}[x] for x in w) or '1'

def ms_rel1(n):
    return red((-1,)+(2,)*n+(1,)+(-2,)*(n+1))
def wstar():
    return (-2,1,2,-1)
def ms_rel2(w):
    return red((-1,)+tuple(w))

def infer_n(longw):
    # recognize X y^n x Y^(n+1) up to cyclic/inverse/global signed perm
    hits=[]
    for n in range(1,25):
      c=ms_rel1(n)
      for img in syms():
        z=transform_word(c,img)
        for q,iv,k in cyclic_orientations(z):
          if q==tuple(longw):
            hits.append((n,img,iv,k))
    return hits

def match_wstar(shortw):
    c=ms_rel2(wstar())
    hits=[]
    for img in syms():
      z=transform_word(c,img)
      for q,iv,k in cyclic_orientations(z):
        if q==tuple(shortw):
          hits.append((img,iv,k))
    return hits

def extract_w_from_oriented(shortw):
    # enumerate orientations starting with X and strip it
    out=[]
    for q,iv,k in cyclic_orientations(shortw):
      if q and q[0]==-1:
        out.append({"rel":wordstr(q),"w":wordstr(q[1:]),"inv":iv,"rot":k,"w_arr":list(q[1:])})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--out-dir',required=True)
    a=ap.parse_args()
    manifest=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text())
    by={c['challenge_id']:c for c in manifest['challenges']}
    ids=['ac-01684','ac-08027','ac-00106','ac-01523','ac-01520']
    rows=[]
    for cid in ids:
      c=by[cid]; rels=[tuple(w) for w in c['initial_relators']]
      # identify longer relator as MS first relation candidate
      order=sorted(range(2), key=lambda i:len(rels[i]), reverse=True)
      li,si=order[0],order[1]
      longw,shortw=rels[li],rels[si]
      rec={
        'challenge_id':cid,
        'initial':[wordstr(w) for w in rels],
        'lengths':[len(w) for w in rels],
        'long_index':li,'short_index':si,
        'n_matches':[{'n':n,'img':list(img),'inv':iv,'rot':k} for n,img,iv,k in infer_n(longw)],
        'w_candidates':extract_w_from_oriented(shortw),
        'wstar_global_matches':[{'img':list(img),'inv':iv,'rot':k} for img,iv,k in match_wstar(shortw)],
      }
      rows.append(rec)
      print('MS_IDENTITY_CASE',json.dumps(rec,sort_keys=True))
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'cases.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print('MS_IDENTITY_SUMMARY',json.dumps({
      'cases':len(rows),
      'with_n_match':sum(bool(r['n_matches']) for r in rows),
      'with_wstar_global_match':sum(bool(r['wstar_global_matches']) for r in rows),
    },sort_keys=True))

if __name__=='__main__':main()
