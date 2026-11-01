#!/usr/bin/env python3
"""Memory-bounded native ROS 2 CDR length-claim experiment.

All malformed inputs are run in isolated children with RLIMIT_AS and CPU/time
limits. No network traffic, publication, vehicle devices or persistent state.
"""
import collections
import json
import os
import resource
import struct
import subprocess
import sys

CASES = [
    ("UnboundedSequences", "primitive"),
    ("BoundedSequences", "bounded_primitive"),
    ("WStrings", "wstring_bounded"),
    ("WStrings", "wstring_unbounded"),
    ("MultiNested", "nested_unbounded"),
]
LENGTHS = [1, 64, 65535, 1 << 20, 1 << 28, (1 << 31) - 1, (1 << 32) - 1]
BUDGETS_MIB = [256, 512]
TIMEOUT_SECONDS = 4

def make_payload(message_type, variant, count):
    from rclpy.serialization import serialize_message
    import test_msgs.msg as m
    cls = getattr(m, message_type)
    base_msg = cls()
    base = bytes(serialize_message(base_msg))
    assert base[:4] in (b"\x00\x01\x00\x00", b"\x00\x00\x00\x00"), base[:4].hex()
    if variant == "primitive":
        changed = cls()
        changed.bool_values = [True]
    elif variant == "bounded_primitive":
        changed = cls()
        changed.bool_values = [True]
    elif variant == "wstring_bounded":
        changed = cls()
        changed.bounded_sequence_of_wstrings = ["A"]
    elif variant == "wstring_unbounded":
        changed = cls()
        changed.unbounded_sequence_of_wstrings = ["A"]
    elif variant == "nested_unbounded":
        changed = cls()
        changed.unbounded_sequence_of_arrays = [m.Arrays()]
    else:
        raise ValueError(variant)
    altered = bytes(serialize_message(changed))
    idx = next(i for i in range(min(len(base), len(altered))) if base[i] != altered[i])
    # The first changed byte must be the low-order byte of the 32-bit sequence
    # count. If serialization encodes differently, fail the experiment rather
    # than silently interpreting a different payload.
    assert base[idx:idx+4] == b"\x00\x00\x00\x00", (variant, idx, base[idx:idx+4].hex())
    assert altered[idx:idx+4] == b"\x01\x00\x00\x00", (variant, idx, altered[idx:idx+4].hex())
    return cls, base[:idx] + struct.pack("<I", count), idx, base

def child(message_type, variant, count):
    from rclpy.serialization import deserialize_message
    cls, payload, idx, valid = make_payload(message_type, variant, count)
    expected = os.environ.get("EXPECTED_LIB_DIR")
    if expected:
        paths = sorted(set(line.split()[-1] for line in open("/proc/self/maps")
                           if "/librmw_cyclonedds_cpp.so" in line and "/" in line))
        assert paths and all(p.startswith(expected) for p in paths), paths
    try:
        obj = deserialize_message(payload, cls)
    except Exception as exc:
        outcome, detail = "error", type(exc).__name__ + ": " + str(exc)[:180]
    else:
        outcome, detail = "accepted", type(obj).__name__
    record = {"outcome": outcome, "detail": detail, "count": count, "offset": idx,
              "input_bytes": len(payload), "valid_bytes": len(valid),
              "maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    print(json.dumps(record), flush=True)

def control(message_type):
    from rclpy.serialization import serialize_message, deserialize_message
    import test_msgs.msg as m
    cls = getattr(m, message_type)
    original = cls()
    data = serialize_message(original)
    result = deserialize_message(data, cls)
    assert type(result) is cls
    print(json.dumps({"outcome":"accepted", "bytes":len(data),
                      "maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)

def under_cap(mib):
    cap = mib * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def run_child(args, mib):
    env = dict(os.environ)
    try:
        p = subprocess.run([sys.executable, __file__] + list(map(str, args)),
                           text=True, capture_output=True, env=env,
                           preexec_fn=lambda: under_cap(mib),
                           timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {"outcome":"timeout", "detail":"child walltime exceeded 4s"}
    if p.returncode < 0:
        return {"outcome":"signal", "detail":f"signal {-p.returncode}", "stderr":p.stderr[-300:]}
    if p.returncode > 0:
        return {"outcome":"process_error", "code":p.returncode, "stderr":p.stderr[-550:]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        return {"outcome":"unparseable", "stdout":p.stdout[-300:], "stderr":p.stderr[-300:]}

def matrix():
    rows = []
    # Each control under each memory limit must pass. Otherwise the budget is
    # insufficient for Python/ROS itself and negative tests are inconclusive.
    for mib in BUDGETS_MIB:
        for type_name in sorted(set(x[0] for x in CASES)):
            rec = run_child(["control", type_name], mib)
            row = {"type":type_name, "variant":"control", "budget_mib":mib, **rec}
            print(json.dumps(row), flush=True);rows.append(row)
        for type_name, variant in CASES:
            for count in LENGTHS:
                rec = run_child(["child",type_name,variant,count],mib)
                row = {"type":type_name, "variant":variant, "count":count,
                       "budget_mib":mib, **rec}
                print(json.dumps(row),flush=True);rows.append(row)
    with open("/evidence/residual-results.json","w") as f:
        json.dump(rows,f,indent=2)
    c=collections.Counter(r["outcome"] for r in rows)
    print("SUMMARY", json.dumps(dict(c)),flush=True)
    controls=[r for r in rows if r["variant"]=="control"]
    assert len(controls)==len(BUDGETS_MIB)*len(set(x[0] for x in CASES))
    assert all(x["outcome"]=="accepted" for x in controls), controls
    return 0

if __name__=="__main__":
    if len(sys.argv)==5 and sys.argv[1]=="child":
        child(sys.argv[2],sys.argv[3],int(sys.argv[4]))
    elif len(sys.argv)==3 and sys.argv[1]=="control":
        control(sys.argv[2])
    elif len(sys.argv)==1:
        sys.exit(matrix())
    else:
        raise SystemExit("Usage: oom_probe.py [control TYPE | child TYPE VARIANT COUNT]")
