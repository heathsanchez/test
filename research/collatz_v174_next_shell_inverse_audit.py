"""V174: exact guarded inverse-shell search for NEW terminal-seeded joins.

For an ORIGINAL n whose FIRST terminal shortcut clock is D>H and a
NEW SOURCE SHELL [L,R), any single-edge merger into a directly
terminal-certified new source p at clock <=H must satisfy:
  T^i(n)=T^j(p), 0<=i,j<=H, p in [L,R),
  j + D - i <= H.
Since i<D, T^i(n) is preterminal, and p's first terminal clock
is exactly j+(D-i). Thus j<=i-(D-H).

Search ALL genuine inverse predecessor words of each exact late
endpoint T^i(n) within that bound, using mathematically SOUND
height-envelope pruning. A bounded absence excludes ONLY one-hop
direct-terminal seeds at THIS shell and THIS H, not multi-hop
proof reuse or global Collatz convergence.

A new finite positive witness is independently rechecked and
Lean-qualified in NextShellHeightUnlock.lean.
"""
from __future__ import annotations

import json
from functools import lru_cache


def T(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def orbit_to_terminal(n: int, max_clock: int = 1500) -> list[int]:
    a=[n]
    while a[-1] not in (1,2) and len(a)<=max_clock:
        a.append(T(a[-1]))
    assert a[-1] in (1,2),("UNKNOWN_BUDGET",n,max_clock)
    return a


def inverse_successors(y: int) -> tuple[int,...]:
    """Every positive one-step TRUE inverse, with exact forward replay."""
    q=[2*y]
    if y%3==2:
        p=(2*y-1)//3
        assert 0<p and p%2==1
        q.append(p)
    assert all(T(p)==y for p in q)
    return tuple(q)


def search_one_direct_seeded_shell_join(
    n: int, lo: int, hi: int, H: int, state_cap: int = 1000000,
) -> dict:
    assert 0<n<lo<hi and H>0
    path=orbit_to_terminal(n)
    D=len(path)-1
    assert D>H,("SOURCE_ALREADY_TERMINAL_BY_H",n,D,H)
    examined=0
    widest=0
    for i in range(min(H,D-1),max(0,D-H)-1,-1):
        max_j=i-(D-H)
        assert max_j>=0
        layer={path[i]}
        for j in range(max_j+1):
            examined+=len(layer)
            widest=max(widest,len(layer))
            if len(layer)>state_cap:
                raise RuntimeError(f"enumeration budget exceeded at n={n},i={i},j={j}")
            candidates=sorted(p for p in layer if lo<=p<hi)
            if candidates:
                p=candidates[0]
                source_seed_clock=D-i+j
                assert 0<=i<=H and 0<=j<=H and source_seed_clock<=H
                assert 0<p and lo<=p<hi
                assert path[i] == forward(p,j)
                assert forward(p,source_seed_clock) in (1,2)
                return {
                    "source":n,"source_first_terminal_clock":D,
                    "old_height_source_cutoff":lo,
                    "new_height_source_cutoff":hi,
                    "H":H,
                    "genuine_join_found":True,
                    "original_source_clock":i,
                    "new_source":p,"new_source_clock":j,
                    "shared_endpoint":path[i],
                    "new_source_terminal_clock":source_seed_clock,
                    "new_source_terminal_endpoint":forward(p,source_seed_clock),
                    "fully_search_exhaustive_before_first_witness":True,
                    "visited_exact_inverse_states":examined,
                    "largest_inverse_frontier":widest
                }
            if j==max_j:
                break
            rem=max_j-j-1
            f2=1<<rem
            f3=3**rem
            nxt=set()
            for y in layer:
                for p in inverse_successors(y):
                    # If already in target shell, KEEP: stopping early is
                    # allowed even when additional reverse clocks remain.
                    # Else, if p<lo, maximum growth after up to rem clocks
                    # is 2^rem*p. If p>=hi, minimum shrink is bounded by
                    # (2/3)^rem*(p+1)-1 (every inverse step >=(2p-1)/3).
                    if (lo<=p<hi or
                        ((p>=lo or p*f2>=lo) and
                         (p<hi or (p+1)*f2<=(hi+1)*f3))):
                        nxt.add(p)
            layer=nxt
            if not layer:
                break
    return {
        "source":n,"source_first_terminal_clock":D,
        "old_height_source_cutoff":lo,
        "new_height_source_cutoff":hi,
        "H":H,"genuine_join_found":False,
        "complete_negative_only_within_specified_shell_and_one_hop_seed":True,
        "visited_exact_inverse_states":examined,
        "largest_inverse_frontier":widest
    }


def forward(n:int,j:int)->int:
    for _ in range(j):
        n=T(n)
    return n


def independently_bruteforce_small(n:int,lo:int,hi:int,H:int)->bool:
    vals=[n]
    for _ in range(H):
        vals.append(T(vals[-1]))
    idx=set(vals)
    for p in range(lo,hi):
        v=p
        for j in range(H+1):
            if v in idx and len(orbit_to_terminal(p)) -1 <=H:
                return True
            if j<H:
                v=T(v)
    return False


def small_control() -> None:
    # Independent direct enumeration checks admissible predecessor
    # enumeration AND early-stop height pruning at smaller heights.
    cases=0
    for n in (27,31,63,127,703,1023):
        D=len(orbit_to_terminal(n))-1
        for H in (8,12,16,20):
            if H>=D: continue
            for lo in (128,256):
                hi=lo*2
                if n>=lo:continue
                found=search_one_direct_seeded_shell_join(n,lo,hi,H)
                brute=independently_bruteforce_small(n,lo,hi,H)
                assert found["genuine_join_found"]==brute,(n,H,lo,found,brute)
                cases+=1
    assert cases>=20
    print("small independent complete direct-forward positive/negative controls:",cases,
          file=__import__("sys").stderr)


def main() -> None:
    small_control()
    sources=(13002751,13421671,13774695,15410667)
    lo,hi=2**25,2**26
    H=208
    out=[search_one_direct_seeded_shell_join(n,lo,hi,H) for n in sources]
    witness=[r for r in out if r["genuine_join_found"]]
    assert len(witness)==1 and witness[0]["source"]==13774695
    w=witness[0]
    assert (w["original_source_clock"],w["new_source"],
            w["new_source_clock"],w["shared_endpoint"],
            w["new_source_terminal_clock"],
            w["new_source_terminal_endpoint"])==(
               207,61407743,57,191866796,201,2)
    assert all((not r["genuine_join_found"] and
                r["complete_negative_only_within_specified_shell_and_one_hop_seed"])
               for r in out if r["source"]!=13774695)
    print(json.dumps({
        "schema":"COLLATZ_V174_EXACT_NEXT_SHELL_SINGLE_JOIN_SEARCH",
        "predecessor_map":"EXACT_2Y_AND_GUARDED_ODD_(2Y-1)/3",
        "shell_lower_inclusive":lo,
        "shell_upper_exclusive":hi,
        "clock_cap":H,
        "original_sources":list(sources),
        "observations":out,
        "positive_witness_is_lean_candidate":True,
        "negative_scope":"ONLY_ONE_HOP_TO_DIRECT_TERMINAL_SEED_IN_THIS_SHELL_AND_CLOCK",
        "unbounded_elimination_proved":False,
        "global_collatz":"UNKNOWN",
        "qed":False},indent=2,sort_keys=True))


if __name__=="__main__":
    main()
