#!/usr/bin/env python3
import collections

def ident(n): return tuple(range(n))

def compose(a,b):
    # a after b
    return tuple(a[b[i]] for i in range(len(a)))

def inv(a):
    out=[0]*len(a)
    for i,j in enumerate(a):out[j]=i
    return tuple(out)

def cycle(n,items):
    p=list(range(n))
    if items:
        for i,x in enumerate(items):p[x]=items[(i+1)%len(items)]
    return tuple(p)

def eval_word(word,x,y):
    e=ident(len(x));xi=inv(x);yi=inv(y)
    lut={1:x,-1:xi,2:y,-2:yi}
    cur=e
    for a in word:cur=compose(cur,lut[a])
    return cur

def conj(g,r):
    return compose(compose(g,r),inv(g))

def move(pair,m,x,y):
    a,b=pair
    ai=inv(a);bi=inv(b);xi=inv(x);yi=inv(y)
    if m==0:return (ai,b)
    if m==1:return (a,bi)
    if m==2:return (compose(a,b),b)
    if m==3:return (compose(a,bi),b)
    if m==4:return (a,compose(b,a))
    if m==5:return (a,compose(b,ai))
    gs=(x,xi,y,yi)
    if 6<=m<=9:return (conj(gs[m-6],a),b)
    if 10<=m<=13:return (a,conj(gs[m-10],b))
    raise ValueError(m)

_CACHE={}
def pdb(n,swap=False):
    key=(n,swap)
    if key in _CACHE:return _CACHE[key]
    t=cycle(n,(0,1))
    c=cycle(n,tuple(range(n)))
    x,y=(c,t) if swap else (t,c)
    target=(x,y)
    q=collections.deque([target]);dist={target:0}
    while q:
        s=q.popleft();d=dist[s]
        for m in range(14):
            z=move(s,m,x,y)
            if z not in dist:
                dist[z]=d+1;q.append(z)
    _CACHE[key]=(x,y,dist)
    return _CACHE[key]

def lower_bound(initial,groups=((3,False),(3,True),(4,False),(4,True),(5,False),(5,True))):
    best=0;parts={}
    for n,swap in groups:
        x,y,dist=pdb(n,swap)
        state=(eval_word(initial[0],x,y),eval_word(initial[1],x,y))
        d=dist.get(state)
        label=f"S{n}:{'yx' if swap else 'xy'}"
        if d is not None:
            parts[label]=d;best=max(best,d)
        else:
            parts[label]=None
    return best,parts
