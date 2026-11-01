#!/usr/bin/env python3
"""Process-isolated ROS 2 CDR truncation comparison; native packages from CI."""
import json
import os
import subprocess
import sys

TYPES = ["Arrays", "Strings", "BoundedSequences", "UnboundedSequences", "MultiNested", "WStrings", "BasicTypes"]
RMW = ["rmw_fastrtps_cpp", "rmw_cyclonedds_cpp"]
CASES = ["valid", "empty", "header_1", "header_2", "header_3", "header_only", "valid_header", "be_zero", "be_one", "be_two", "le_zero", "le_one", "le_two", "invalid_header", "valid_minus_1", "valid_minus_half"]

def child(type_name, case):
    from rclpy.serialization import deserialize_message, serialize_message
    import test_msgs.msg
    cls = getattr(test_msgs.msg, type_name)
    valid = bytes(serialize_message(cls()))
    if case == "valid":
        data = valid
    elif case == "empty":
        data = b""
    elif case == "header_only":
        data = b"\x00\x00\x00\x01"
    elif case.startswith("header_"):
        data = b"\x00\x00\x00\x01"[:int(case.split("_")[1])]
    elif case == "valid_header":
        data = valid[:4]
    elif case in ("be_zero", "be_one", "be_two", "le_zero", "le_one", "le_two", "invalid_header"):
        data = {
            "be_zero": b"\x00\x00\x00\x00",
            "be_one": b"\x00\x00\x00\x01",
            "be_two": b"\x00\x00\x00\x02",
            "le_zero": b"\x00\x01\x00\x00",
            "le_one": b"\x00\x01\x00\x01",
            "le_two": b"\x00\x01\x00\x02",
            "invalid_header": b"\xff\xff\x00\x00",
        }[case]
    elif case == "valid_minus_1":
        data = valid[:-1]
    elif case == "valid_minus_half":
        data = valid[:max(4, len(valid)//2)]
    else:
        raise ValueError(case)
    try:
        value = deserialize_message(data, cls)
    except Exception as exc:
        print(json.dumps({"outcome": "error", "exception": type(exc).__name__,
                          "length": len(data), "valid_length": len(valid), "native_prefix": valid[:4].hex()}))
    else:
        print(json.dumps({"outcome": "accepted", "returned_type": type(value).__name__,
                          "length": len(data), "valid_length": len(valid), "native_prefix": valid[:4].hex()}))

def matrix():
    rows = []
    for backend in RMW:
        for typename in TYPES:
            for case in CASES:
                env = dict(os.environ, RMW_IMPLEMENTATION=backend)
                try:
                    p = subprocess.run([sys.executable, __file__, "child", typename, case],
                                       env=env, text=True, capture_output=True, timeout=6)
                    if p.returncode < 0:
                        outcome, detail = "signal", f"signal {-p.returncode}"
                    elif p.returncode > 0:
                        outcome, detail = "process_error", p.stderr[-600:]
                    else:
                        try:
                            detail = json.loads(p.stdout.strip().splitlines()[-1])
                            outcome = detail["outcome"]
                        except (ValueError, IndexError, KeyError):
                            outcome, detail = "invalid_record", (p.stdout + p.stderr)[-600:]
                except subprocess.TimeoutExpired:
                    outcome, detail = "timeout", "child exceeded 6s"
                row = {"backend": backend, "type": typename, "case": case,
                       "outcome": outcome, "detail": detail}
                rows.append(row)
                print(json.dumps(row), flush=True)
    with open("/evidence/results.json", "w") as file:
        json.dump({"cases": rows}, file, indent=2)
    counts = {}
    for row in rows:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    print("SUMMARY", json.dumps(counts), flush=True)
    positive = [row for row in rows if row["case"] == "valid"]
    if len(positive) != 14 or any(row["outcome"] != "accepted" for row in positive):
        print("POSITIVE CONTROL FAILED: cannot interpret matrix", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "child":
        child(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 1:
        sys.exit(matrix())
    else:
        sys.exit("usage: probe.py [child TYPE CASE]")
