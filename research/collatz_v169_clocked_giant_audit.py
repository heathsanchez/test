"""V169: exact source/clock finite DSU component audit.

Runs the independently existing V168 C++ retroactive quotient compiler at
H(k)=8k with owner extension disabled (maxClock = initial H).
Checks both true T1 and the actual G7 two-basin negative control.
Also independently recomputes small graphs in Python.

No inferred asymptotic bound, no local import of the Shaik/Mazur
predecessor theorem, and no universal Collatz result.
"""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
import subprocess


SOURCE = Path("research/collatz_v168_retrospective_quotient.cpp")
BIN = Path("/tmp/collatz-v169-retro-quotient")


def step(n: int, c: int) -> int:
    return n // 2 if n % 2 == 0 else (3 * n + c) // 2


def independent_small_full_graph(k: int, c: int) -> dict:
    """Independently scans entire H-prefix of each source, including good ones.

    The existing V168 program stops scanning a source once GOOD is known.
    Removing that optimization cannot change BAD components: a sound
    GOOD component cannot coalesce with a genuinely bad component.
    """
    N, H = (1 << k) - 1, 8 * k
    roots = (1, 2) if c == 1 else (7, 14)
    parent = list(range(N + 1))
    size = [1] * (N + 1)
    is_seeded = [False] * (N + 1)

    def root(n: int) -> int:
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def join(a: int, b: int) -> None:
        a, b = root(a), root(b)
        if a == b:
            return
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        is_seeded[a] |= is_seeded[b]

    join(*roots)
    is_seeded[root(roots[0])] = True
    owner: dict[int, int] = {}
    for n in range(1, N + 1):
        x = n
        for i in range(H + 1):
            if x in roots:
                join(n, x)
                is_seeded[root(n)] = True
            else:
                p = owner.setdefault(x, n)
                if n != p:
                    join(n, p)
            if i < H:
                x = step(x, c)
    components = collections.Counter(
        root(n) for n in range(1, N + 1) if not is_seeded[root(n)]
    )
    return {
        "unresolved_sources": sum(components.values()),
        "unresolved_components": len(components),
        "largest_unresolved_component": max(components.values(), default=0),
    }


def existing_source_locked_compiler(k: int, c: int, H: int | None = None) -> dict:
    if H is None:
        H = 8 * k
    args = [str(BIN), str(k), str(H), str(H), "T" if c == 1 else "G"]
    d = json.loads(subprocess.check_output(args, text=True))
    assert d["schema"] == "COLLATZ_V168_RETROACTIVE_FUTURE_QUOTIENT"
    assert d["k"] == k and d["initial_clock"] == H
    assert d["owner_clock_cap"] == H
    assert d["additional_source_clock_steps"] == 0
    assert d["additional_actual_two_clock_mergers"] == 0
    assert d["initial_unresolved_sources"] == d["final_unresolved_sources"]
    assert d["initial_unresolved_components"] == d["final_unresolved_components"]
    assert d["initial_largest_unresolved_component"] == d["final_largest_unresolved_component"]
    assert d["global_collatz"] == "UNKNOWN" and d["qed"] is False
    return d




def certify_adverse_sources() -> list[dict]:
    """Exact future and eventual terminal receipts for the seven finite timeouts.

    These are ordinary bounded test witnesses, NEVER an assumption that all
    unknown sources eventually terminate.
    """
    cases=[
        (20,1027431,238),(20,1042431,276),
        (22,2643183,271),(22,3428767,349),
        (22,3964775,270),(22,4053039,335),
        (22,4063723,354),
    ]
    receipts=[]
    for k,n,clock in cases:
        x=n
        for t in range(clock):
            assert x not in (1,2),(n,t,x)
            x=step(x,1)
        assert x in (1,2),(n,clock,x)
        receipts.append({'k':k,'source':n,
                         'verified_direct_terminal_clock':clock})
    assert step(2643183,1)==3964775
    x=4063723
    for _ in range(5):
        x=step(x,1)
    assert x==3428767
    return receipts


def main() -> None:
    subprocess.run(
        ["g++", "-std=c++17", "-O3", str(SOURCE), "-o", str(BIN)],
        check=True,
    )
    rows = []
    for k in (8, 10, 12, 14, 16, 18, 20, 22):
        for c in ((1, 7) if k <= 20 else (1,)):
            row = existing_source_locked_compiler(k, c)
            item = {
                "k": k,
                "H": row["initial_clock"],
                "intercept": c,
                "N": row["positive_source_cutoff"],
                "unresolved_sources": row["initial_unresolved_sources"],
                "unresolved_components": row["initial_unresolved_components"],
                "largest_unresolved_component": row["initial_largest_unresolved_component"],
                "component_fraction_numerator": row["initial_largest_unresolved_component"],
                "component_fraction_denominator": 2**k,
                "largest_few": row["initial_top_components"][:4],
            }
            if k <= 12:
                independent = independent_small_full_graph(k, c)
                assert item["unresolved_sources"] == independent["unresolved_sources"], (item, independent)
                assert item["unresolved_components"] == independent["unresolved_components"], (item, independent)
                assert item["largest_unresolved_component"] == independent["largest_unresolved_component"], (item, independent)
            rows.append(item)
    observed = {(r["k"], r["intercept"]):r for r in rows}
    for k in (8, 10, 12, 14, 16, 18):
        assert observed[k, 1]["unresolved_sources"] == 0
    assert (observed[20,1]["unresolved_sources"],
            observed[20,1]["unresolved_components"],
            observed[20,1]["largest_unresolved_component"]) == (2,2,1)
    assert (observed[22,1]["unresolved_sources"],
            observed[22,1]["unresolved_components"],
            observed[22,1]["largest_unresolved_component"]) == (5,3,2)
    assert observed[20,7]["unresolved_sources"] == 898779
    assert observed[20,7]["largest_unresolved_component"] >= 898000
    assert observed[12,7]["unresolved_sources"] == 3510

    k20_later = existing_source_locked_compiler(20, 1, 184)
    assert k20_later["final_unresolved_sources"] == 0

    output = {
        "schema":"COLLATZ_V169_CLOCKED_GIANT_COMPONENT_BOUNDED_AUDIT",
        "source_cpp_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "method":"source-indexed true two-clock observed collision union; ownerMaxClock=H",
        "clock_schedule":"H=8*k; safely greater than 11*log(2)*k",
        "independently_recomputed_k":[8,10,12],
        "rows":rows,
        "adverse_source_receipts":certify_adverse_sources(),
        "k22_observed_two_clock_edges":[
            {'source':2643183,'clock':1,'other':3964775,'other_clock':0},
            {'source':4063723,'clock':5,'other':3428767,'other_clock':0},
        ],
        "true_k20_at_H184_unresolved":0,
        "positive_density_external_theorem_locally_rebuilt":False,
        "component_anti_giant_limit_proved":False,
        "all_ledger_edges_individually_lean_reified":False,
        "all_timeouts_stay_UNKNOWN":True,
        "global_collatz":"UNKNOWN","qed":False,
    }
    print(json.dumps(output, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
