#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from z3 import Bool, If, Int, Solver, sat, unsat

DEFAULT_L = 2075 * (1 << 60)
DEFAULT_U = (1 << 72) - 1

def required_odds(max_horizon: int):
    req = [0] * (max_horizon + 1)
    q = 0
    p3 = 1
    p2 = 1
    for t in range(1, max_horizon + 1):
        p2 <<= 1
        while p3 < p2:
            q += 1
            p3 *= 3
        req[t] = q
    return req

def replay(n: int, limit: int):
    x = n
    q = 0
    first_contract = None
    first_descent = None
    min_x = n
    for t in range(1, limit + 1):
        if x & 1:
            q += 1
            x = (3 * x + 1) // 2
        else:
            x //= 2
        if first_contract is None and pow(3, q) < (1 << t):
            first_contract = t
        if first_descent is None and x < n:
            first_descent = t
        min_x = min(min_x, x)
        if first_contract is not None and first_descent is not None:
            break
    return {
        "first_contract": first_contract,
        "first_descent": first_descent,
        "min_x": min_x,
        "stopped_at": t,
        "x": x,
        "odd_count": q,
    }

def parse_checkpoints(s: str, max_horizon: int):
    vals = sorted({int(x) for x in s.split(",") if x.strip()})
    vals = [x for x in vals if 1 <= x <= max_horizon]
    if max_horizon not in vals:
        vals.append(max_horizon)
    return vals

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lower", type=int, default=DEFAULT_L)
    ap.add_argument("--upper", type=int, default=DEFAULT_U)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--max-horizon", type=int, default=1500)
    ap.add_argument("--checkpoints", default="400,600,800,1000,1200,1500")
    ap.add_argument("--timeout-ms", type=int, default=900000)
    ap.add_argument("--out", default="collatz_exact_result.json")
    args = ap.parse_args()

    assert 0 <= args.shard_index < args.shards
    assert args.lower <= args.upper

    total = args.upper - args.lower + 1
    lo = args.lower + (total * args.shard_index) // args.shards
    hi = args.lower + (total * (args.shard_index + 1)) // args.shards - 1
    if args.shard_index == args.shards - 1:
        hi = args.upper

    checkpoints = parse_checkpoints(args.checkpoints, args.max_horizon)
    req = required_odds(args.max_horizon)

    solver = Solver()
    solver.set(timeout=args.timeout_ms)
    x = [Int("x_0")]
    q = [Int("q_0")]
    solver.add(x[0] >= lo, x[0] <= hi, q[0] == 0)

    results = []
    cp_set = set(checkpoints)
    t0 = time.time()

    print(f"EXACT_SHARD index={args.shard_index}/{args.shards} lo={lo} hi={hi} width={hi-lo+1}")
    print(f"MAX_HORIZON {args.max_horizon} timeout_ms={args.timeout_ms}")

    for t in range(args.max_horizon):
        odd = Bool(f"o_{t}")
        xn = Int(f"x_{t+1}")
        qn = Int(f"q_{t+1}")
        solver.add(If(odd, 3 * x[t] + 1, x[t]) == 2 * xn)
        solver.add(xn > 0)
        solver.add(qn == q[t] + If(odd, 1, 0))
        solver.add(qn >= req[t + 1])
        x.append(xn)
        q.append(qn)

        horizon = t + 1
        if horizon not in cp_set:
            continue

        c0 = time.time()
        status = solver.check()
        elapsed = time.time() - c0
        row = {"horizon": horizon, "status": str(status), "check_seconds": elapsed}
        if status == sat:
            model = solver.model()
            n = model[x[0]].as_long()
            qr = model[q[horizon]].as_long()
            xr = model[x[horizon]].as_long()
            rep = replay(n, max(args.max_horizon + 50, horizon + 50))
            row.update({"witness": n, "q": qr, "x_horizon": xr, "replay": rep})
            print(f"SAT horizon={horizon} n={n} q={qr} x={xr} check_s={elapsed:.3f} replay={rep}")
        elif status == unsat:
            print(f"UNSAT horizon={horizon} check_s={elapsed:.3f}")
            results.append(row)
            break
        else:
            row["reason_unknown"] = solver.reason_unknown()
            print(f"UNKNOWN horizon={horizon} check_s={elapsed:.3f} reason={row['reason_unknown']}")
        results.append(row)

    summary = {
        "kind": "exact_linear_integer_collatz_coefficient_persistence",
        "lower_global": args.lower,
        "upper_global": args.upper,
        "shards": args.shards,
        "shard_index": args.shard_index,
        "lower": lo,
        "upper": hi,
        "max_horizon": args.max_horizon,
        "checkpoints": checkpoints,
        "timeout_ms": args.timeout_ms,
        "results": results,
        "wall_seconds": time.time() - t0,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2) + "\n")
    print("RESULT_JSON", json.dumps(summary, separators=(",", ":")))

if __name__ == "__main__":
    main()
