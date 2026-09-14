#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path

try:
    from dd.cudd import BDD
except Exception:
    from dd.autoref import BDD

def const_bits(bdd, value, width):
    return [bdd.true if ((value >> i) & 1) else bdd.false for i in range(width)]

def zext(bits, width, bdd):
    if len(bits) >= width:
        return bits[:width]
    return bits + [bdd.false] * (width - len(bits))

def mux(sel, a, b):
    # sel ? b : a
    return [(~sel & x) | (sel & y) for x, y in zip(a, b)]

def add2(bdd, a, b, width):
    a = zext(a, width, bdd)
    b = zext(b, width, bdd)
    out = []
    carry = bdd.false
    for i in range(width):
        ai, bi = a[i], b[i]
        s = ai ^ bi ^ carry
        carry = (ai & bi) | (ai & carry) | (bi & carry)
        out.append(s)
    return out

def add_const(bdd, a, value, width):
    return add2(bdd, a, const_bits(bdd, value, width), width)

def odd_branch(bdd, u):
    # 3*u + 2
    width = len(u) + 2
    uu = zext(u, width, bdd)
    twice = [bdd.false] + zext(u, width - 1, bdd)
    s = add2(bdd, uu, twice, width)
    return add_const(bdd, s, 2, width)

def uge_const(bdd, bits, c):
    # unsigned bits >= constant c
    width = len(bits)
    cb = [(c >> i) & 1 for i in range(width)]
    gt = bdd.false
    eq = bdd.true
    for i in range(width - 1, -1, -1):
        xi = bits[i]
        if cb[i]:
            eq = eq & xi
        else:
            gt = gt | (eq & xi)
            eq = eq & ~xi
    return gt | eq

def ule_const(bdd, bits, c):
    width = len(bits)
    cb = [(c >> i) & 1 for i in range(width)]
    lt = bdd.false
    eq = bdd.true
    for i in range(width - 1, -1, -1):
        xi = bits[i]
        if cb[i]:
            lt = lt | (eq & ~xi)
            eq = eq & xi
        else:
            eq = eq & ~xi
    return lt | eq

def uge_bits(bdd, a, b):
    width = max(len(a), len(b))
    a = zext(a, width, bdd)
    b = zext(b, width, bdd)
    gt = bdd.false
    eq = bdd.true
    for i in range(width - 1, -1, -1):
        ai, bi = a[i], b[i]
        gt = gt | (eq & ai & ~bi)
        eq = eq & ~(ai ^ bi)
    return gt | eq

def pick_seed(bdd, valid, names):
    if valid == bdd.false:
        return None
    it = bdd.pick_iter(valid, care_vars=set(names))
    m = next(it, None)
    if m is None:
        return None
    n = 0
    for i, name in enumerate(names):
        if bool(m.get(name, False)):
            n |= 1 << i
    return n

def replay(n, limit):
    x = n
    first_descent = None
    peak = n
    for t in range(1, limit + 1):
        x = (3*x + 1)//2 if (x & 1) else x//2
        peak = max(peak, x)
        if x < n:
            first_descent = t
            break
    return {"first_descent": first_descent, "stopped_at": t, "x": x, "peak": peak}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, default=72)
    ap.add_argument("--lower", type=int, default=2075 * (1 << 60))
    ap.add_argument("--upper", type=int, default=(1 << 72) - 1)
    ap.add_argument("--horizon", type=int, default=2000)
    ap.add_argument("--checkpoint", type=int, default=50)
    ap.add_argument("--out", default="bdd-result.json")
    A = ap.parse_args()

    K = A.bits
    assert 0 <= A.lower <= A.upper < (1 << K)

    bdd = BDD()
    try:
        bdd.configure(reordering=True)
    except Exception:
        pass
    names = [f"n{i}" for i in range(K)]
    bdd.declare(*names)
    seed = [bdd.var(name) for name in names]

    valid = uge_const(bdd, seed, A.lower) & ule_const(bdd, seed, A.upper)
    x = list(seed)
    results = []
    start = time.time()

    print(f"BDD_EXACT bits={K} lower={A.lower} upper={A.upper} horizon={A.horizon}")
    for t in range(1, A.horizon + 1):
        p = x[0]
        u = x[1:]
        odd = odd_branch(bdd, u)
        w = max(len(u), len(odd))
        even = zext(u, w, bdd)
        odd = zext(odd, w, bdd)
        x = mux(p, even, odd)

        # Retain exactly those starts whose actual shortcut-Collatz iterate
        # has never fallen below the start.
        valid = valid & uge_bits(bdd, x, seed)

        if t % A.checkpoint == 0 or valid == bdd.false:
            try:
                count = bdd.count(valid, nvars=K)
            except TypeError:
                count = bdd.count(valid)
            witness = pick_seed(bdd, valid, names)
            row = {
                "horizon": t,
                "count": int(count),
                "nodes": len(bdd),
                "witness": witness,
                "seconds": time.time() - start,
            }
            if witness is not None:
                row["replay"] = replay(witness, t + 10)
            results.append(row)
            print("CHECK", json.dumps(row, separators=(",", ":")), flush=True)
            if valid == bdd.false:
                break

    status = "UNSAT" if valid == bdd.false else "SURVIVORS"
    summary = {
        "kind": "exact_bdd_no_descent",
        "status": status,
        "bits": K,
        "lower": A.lower,
        "upper": A.upper,
        "requested_horizon": A.horizon,
        "reached_horizon": results[-1]["horizon"] if results else 0,
        "results": results,
        "wall_seconds": time.time() - start,
    }
    Path(A.out).write_text(json.dumps(summary, indent=2) + "\n")
    print("RESULT_JSON", json.dumps(summary, separators=(",", ":")), flush=True)

if __name__ == "__main__":
    main()
