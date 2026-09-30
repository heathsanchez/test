"""Bounded audit of rank counterexamples after the two qualified exit rules."""
import hashlib
import json

BASE = 3294206330938702138381104133963803
PERIOD = 2**191 * 27
PROBES = (0, 1, 2, 3, 17)
EXPECTED = ((279, "direct"), (270, "direct"), (217, "M1"),
            (247, "splice"), (254, "direct"))

def step(x):
    return (3*x + 1)//2 if x % 2 else x//2

def iterate(x, count):
    for _ in range(count):
        x = step(x)
    return x

def order(x, prime):
    assert x != 0
    x = abs(x)
    result = 0
    while x % prime == 0:
        x //= prime
        result += 1
    return result

rows = []
for t, expected in zip(PROBES, EXPECTED):
    n = BASE + PERIOD*t
    y = n
    owners = {}
    for k in range(2001):
        if k in (167, 178, 181):
            assert y % 8 == 3 and y > n
            owners[k] = (y+1)//4
        if 0 < y < n:
            kind, lower, extra, back = "direct", y, 0, 0
        elif y % 8 == 5 and 0 < (y+1)//4 < n:
            kind, lower, extra, back = "splice", (y+1)//4, 3, 1
        elif y % 3 == 2 and 0 < (2*y-1)//3 < n:
            kind, lower, extra, back = "M1", (2*y-1)//3, 0, 1
        else:
            y = step(y)
            continue
        assert (k, kind) == expected
        assert 0 < lower < n
        assert iterate(n, k+extra) == iterate(lower, back)
        break
    else:
        raise AssertionError("Probe remained unresolved at the declared cap")
    m0, m1, m2 = (owners[i] for i in (167, 178, 181))
    assert 2048*m1 == 6561*m0+2443 and 8*m2 == 9*m1+1
    d0, d1 = (2048-6561)*m0-2443, (8-9)*m1-1
    before = (order(d0, 2)-11, order(d0, 3))
    after = (order(d1, 2)-3, order(d1, 3))
    assert before == (1, 0) and after == (7, 2)
    covered = t % 2**88 == 0
    assert covered == (t == 0)
    assert (n+5) % 864 != 0
    rows.append(dict(t=t, source=n, qualified_subcylinder_covers=covered,
                     plateau_rule_covers=False, rank_before=before,
                     rank_after=after, first_DSM1_event=k, event_kind=kind,
                     lower_source=lower, common_future_steps=k+extra,
                     lower_source_steps=back))
report = dict(
    status="BOUNDED_EXACT_GUARD_AUDIT",
    global_collatz="UNKNOWN",
    scope="Five fixed probes; exact integer replay, no new universal Lean theorem.",
    conclusion="Deleting the qualified t=0 mod 2^88 cylinder does not repair the old rank.",
    caveat="All five probes have finite exits. None certifies a full no-OrdinaryExit premise.",
    prior_rank_authority="537f49ba3a8e10542a23fdd227ed43bbf8fc69f1",
    prior_exit_authority="09d67ddc504bc6c5303f597294292fac6391a124",
    rows=rows,
)
report["certificate_sha256"] = hashlib.sha256(
    json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(report, indent=2))
