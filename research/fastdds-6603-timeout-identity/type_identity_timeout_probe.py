#!/usr/bin/env python3
"""Local source-native diagnostic; intentionally separate from upstream cases."""

import argparse
import pathlib
import re
import subprocess
import sys
import time


def run_case(executable, name, writer_field, reader_field, writer_flow, domain, expected, evidence_dir=None):
    writer_cmd = [executable, "publisher", writer_field, str(writer_flow), "0", str(domain), "11000"]
    reader_cmd = [executable, "subscriber", reader_field, "0", "2000", str(domain), "7000"]

    writer = subprocess.Popen(writer_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(1)
        reader = subprocess.Popen(reader_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            reader_output, _ = reader.communicate(timeout=16)
            writer_output, _ = writer.communicate(timeout=16)
        finally:
            if reader.poll() is None:
                reader.kill()
                reader.communicate()
    finally:
        if writer.poll() is None:
            writer.kill()
            writer.communicate()

    def matches(output):
        found = re.search(r"TYPE_ID_PROBE .* max_matched=(\d+)", output)
        return int(found.group(1)) if found else None

    observed = (matches(writer_output), matches(reader_output))
    if evidence_dir is not None:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / f"{domain}-publisher.log").write_text(writer_output)
        (evidence_dir / f"{domain}-subscriber.log").write_text(reader_output)
    writer_size = re.search(r"TYPE_ID_PROBE type_object_bytes=(\d+)", writer_output)
    reader_size = re.search(r"TYPE_ID_PROBE type_object_bytes=(\d+)", reader_output)
    sizes = (int(writer_size.group(1)) if writer_size else None,
             int(reader_size.group(1)) if reader_size else None)
    passed = writer.returncode == 0 and reader.returncode == 0 and observed == expected
    passed = passed and all(size is not None and size > 0 for size in sizes)
    if writer_flow:
        passed = passed and sizes[0] > writer_flow
    label = "PASS" if passed else "FAIL"
    print(f"{label}: {name}: observed writer/reader={observed}, expected={expected}, "
          f"TypeObject bytes={sizes}", flush=True)
    if not passed:
        print(f"  writer exit={writer.returncode}\n{writer_output}")
        print(f"  reader exit={reader.returncode}\n{reader_output}")
    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", help="path to TypeIdentityTimeoutProbe executable")
    parser.add_argument("--only", choices=["viability", "normal", "mismatch", "recovery"])
    parser.add_argument("--evidence-dir", type=pathlib.Path)
    args = parser.parse_args()

    cases = [
        ("viability", "identical types, normal lookup", "int", "int", 0, 160, (1, 1)),
        ("normal", "incompatible types, normal lookup", "int", "bool", 0, 161, (0, 0)),
        ("mismatch", "incompatible types, lookup starved", "int", "bool", 6000, 162, (0, 0)),
        ("recovery", "identical types, lookup starved", "int", "int", 6000, 163, (1, 1)),
    ]

    results = [run_case(args.executable, *case[1:], evidence_dir=args.evidence_dir) for case in cases
               if args.only is None or case[0] == args.only]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
