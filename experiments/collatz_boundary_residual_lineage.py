#!/usr/bin/env python3
"""Exact coalescence census for the first H512 Collatz boundary failures.

The four known absolute-H512 failures from K33/K34 are replayed and their
earliest common forward state is computed exactly.  This tests whether the
boundary residual consists of independent obstructions or one shared delayed
trajectory lineage.
"""

SEEDS=[
    (33,12235060455),
    (33,14500812391),
    (34,20646664519),
    (34,26130934783),
]

def T(n:int)->int:
    return (3*n+1)//2 if n&1 else n//2

def trajectory(n:int,steps:int=1024):
    a=[n]
    for _ in range(steps):
        a.append(T(a[-1]))
    return a

def first_cone(n:int,limit:int=4096):
    y=n
    for t in range(limit+1):
        if y<n:
            return t,"DIRECT",y
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n:
                assert T(p)==y
                return t,"CONE",y
        y=T(y)
    return None

def main():
    tr={n:trajectory(n) for _,n in SEEDS}
    common=set.intersection(*(set(v) for v in tr.values()))
    assert common

    best=None
    for v in common:
        arrivals=[tr[n].index(v) for _,n in SEEDS]
        key=(max(arrivals),sum(arrivals),v)
        if best is None or key<best[0]:
            best=(key,v,arrivals)

    _,core,arrivals=best
    assert core==26130934783,(core,arrivals)
    assert arrivals==[10,15,6,0],arrivals

    print("BOUNDARY_COMMON_LINEAGE",
          f"core={core}",
          "arrivals="+",".join(map(str,arrivals)),
          f"max_arrival={max(arrivals)}")

    for (K,n),a in zip(SEEDS,arrivals):
        z=n
        for _ in range(a):
            z=T(z)
        assert z==core
        fc=first_cone(n)
        assert fc is not None
        t,kind,y=fc
        print("BOUNDARY_LINEAGE_MEMBER",
              f"K={K}",f"n={n}",f"to_core={a}",
              f"first_cone_t={t}",f"kind={kind}",
              f"first_cone_y={y}")

    print("FOUR_H512_FAILURES_COLLAPSE_TO_ONE_EXACT_LINEAGE")
    print("VERIFIED_BOUNDARY_RESIDUAL_LINEAGE")

if __name__=="__main__":
    main()
