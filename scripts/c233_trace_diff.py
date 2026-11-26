"""Compare only source-branch decisions, excluding irrelevant budget drift.

This diagnostic never decides theorem equality. Incomplete or malformed logs
remain UNKNOWN instead of being interpreted as a conversion counterexample.
"""

import json
import pathlib
import sys


PREFIX = "NUCLEUS_C233_DECISION:"
FIELDS = ("seq", "kind", "left", "right", "budget", "attempts", "outcome")
PATH_FIELDS = ("kind", "left", "right", "outcome", "depth", "ctx")


def _events(lines: list[str]) -> list[dict[str, str]] | None:
    events = []
    for line in lines:
        if PREFIX not in line:
            continue
        fragments = line.split(PREFIX, 1)[1].strip().split(":")
        try:
            event = dict(fragment.split("=", 1) for fragment in fragments)
            if not all(event.get(field) for field in FIELDS):
                return None
            if int(event["seq"]) != len(events):
                return None
            events.append(event)
        except (ValueError, TypeError):
            return None
    return events


def compare_trace_lines(low_lines: list[str], high_lines: list[str]) -> dict:
    if any("NUCLEUS_C233_TRUNCATED" in line for line in low_lines + high_lines):
        return {"status": "UNKNOWN", "reason": "truncated-observation"}
    low, high = _events(low_lines), _events(high_lines)
    if low is None or high is None or not low or not high:
        return {"status": "UNKNOWN", "reason": "missing-or-malformed-events"}
    for index, (left, right) in enumerate(zip(low, high)):
        if any(left[field] != right[field] for field in PATH_FIELDS):
            return {
                "status": "FIRST_DIVERGENCE", "index": index,
                "compared_events": index + 1,
                "low": left, "high": right,
            }
    if len(low) != len(high):
        return {"status": "INCOMPLETE_PATH", "compared_events": min(len(low), len(high)),
                "low_count": len(low), "high_count": len(high)}
    return {"status": "SAME_OBSERVED_PATH", "compared_events": len(low)}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: c233_trace_diff.py LOW_STDERR HIGH_STDERR")
    low = pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines()
    high = pathlib.Path(sys.argv[2]).read_text(errors="replace").splitlines()
    print(json.dumps(compare_trace_lines(low, high), indent=2))
