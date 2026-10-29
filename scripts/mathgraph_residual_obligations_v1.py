"""Spec-only residual-obligation probes for the pinned TestSuiteBench hex task.

Designed before any inspection of mutant source or outputs; compares a fresh
48-probe residual suite to the frozen previous 48-probe suites. The known task
has already been scored, so this is an IN-SAMPLE development experiment.
"""
from __future__ import annotations

import argparse
import io
import math
from pathlib import Path
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET

import mathgraph_testgen_ablation as core


def expected_function(n: int, places: int) -> bytes:
    result = []
    for y in range(n):
        result.append(f"{math.sin((y / n) * math.pi / 2):.{places}f},")
        if (y + 1) % 10 == 0:
            result.append("\n")
    result.append("\n")
    return "".join(result).encode()


def expected_color(data: bytes, *, cols: int, fmt: str, prefix: int, limit: int) -> bytes:
    retained = data if limit == 0 else data[:limit]
    width = max(cols, 1)
    rendered = []
    for offset in range(0, len(retained) + 1, width):
        chunk = retained[offset: offset + width]
        row = [f"0x{offset:06x}: "]
        for value in chunk:
            lead = ("0o" if fmt == "o" else "0b" if fmt == "b" else "0x") if prefix else ""
            digits = (f"{value:04o}" if fmt == "o" else f"{value:08b}" if fmt == "b" else f"{value:02X}" if fmt == "X" else f"{value:02x}")
            palette = 22 if value == 0 else value
            row.append(f"\x1b[38;5;{palette}m{lead}{digits}\x1b[0m ")
        row.append(" " * (5 * (cols - len(chunk)) if cols else 0))
        for value in chunk:
            glyph = chr(value) if 32 <= value <= 126 else "."
            palette = 22 if value == 0 else value
            row.append(f"\x1b[38;5;{palette}m{glyph}\x1b[0m")
        row.append("\n")
        rendered.append("".join(row))
        if offset + width > len(retained):
            break
    rendered.append(f"   bytes: {len(retained)}\n")
    return "".join(rendered).encode()


def probe_cases() -> list[dict]:
    result = []
    # Functional mode: explicitly test priority, row grouping, precision, and N=0.
    fn_specs = ((0, 0), (0, 4), (1, 0), (1, 4), (2, 0), (2, 2),
                (3, 4), (5, 2), (9, 0), (10, 0), (10, 4), (11, 6))
    for i, (n, places) in enumerate(fn_specs):
        aliases = ["-u", str(n), "-p", str(places)] if i % 2 else [f"--func={n}", f"--places={places}"]
        if i % 3 == 0:
            aliases.extend(["--array=r", "--format=b", "--color=1", "--prefix=0", "--cols=3", "--len=1"])
        result.append(dict(name=f"func_{i:02d}_n{n}_p{places}", kind="function", args=aliases, n=n, places=places, data=core.pattern(9)))

    # Argument validation: choices, repetition, unknowns, type errors, precedence.
    errors = [
        ("bad_format", ["-fE"], 2, "invalid value 'E'"),
        ("bad_array", ["--array=z"], 2, "invalid value 'z'"),
        ("bad_color", ["--color=2"], 2, "invalid value '2'"),
        ("bad_prefix", ["--prefix=8"], 2, "invalid value '8'"),
        ("double_format", ["-fx", "--format=b"], 2, "cannot be used multiple times"),
        ("double_cols", ["-c2", "--cols=3"], 2, "cannot be used multiple times"),
        ("unknown_flag", ["--unknown-mg"], 2, "unexpected argument"),
        ("extra_positional", ["one", "two"], 2, "unexpected argument"),
        ("bad_cols_integer", ["--cols=whoops"], 1, "invalid digit found in string"),
        ("bad_len_integer", ["--len=-1"], 1, "invalid digit found in string"),
        ("bad_func_integer", ["--func=nope"], 1, "invalid digit found in string"),
        ("missing_cols", ["--cols"], 2, "a value is required"),
    ]
    for name, args, code, substring in errors:
        result.append(dict(name=name, kind="error", args=args, status=code, substring=substring, data=b""))

    # File semantics: source priority, raw byte reading, path handling.
    file_sizes = (0, 1, 3, 10, 255, 256, 4096)
    for i, n in enumerate(file_sizes):
        args = ["-t0", "-c", str((1, 2, 3, 10, 16, 32, 64)[i])]
        data = core.pattern(n)
        result.append(dict(name=f"file_binary_{n}", kind="file", args=args, data=data, cols=int(args[-1]), fmt="x", prefix=1, limit=0, symlink=(i == 5)))
    result.append(dict(name="file_not_found", kind="error", args=["missing-mg-check-hex-input-96254.bin"], status=1, substring="No such file", data=b""))

    # Explicit color: byte-zero palette remapping, high bytes, layout invariants.
    for i, (n, cols, fmt, prefix) in enumerate(((0, 1, "x", 1), (1, 1, "x", 1),
          (2, 3, "X", 1), (3, 3, "o", 0), (4, 2, "b", 1),
          (5, 10, "x", 0), (10, 5, "o", 1), (12, 4, "b", 0))):
        result.append(dict(name=f"color_{i:02d}", kind="color", args=["--color=1", f"--cols={cols}", f"--format={fmt}", f"--prefix={prefix}"],
                           data=core.pattern(n), cols=cols, fmt=fmt, prefix=prefix, limit=0))

    # Additional ordinary obligations: large bytes, empty/full rows, padding edge.
    ordinary = [
        ("boundary_empty_zero_cols", b"", 0, "x", 1, 0),
        ("boundary_exact_column", core.pattern(10), 10, "x", 1, 0),
        ("boundary_partial_column", core.pattern(11), 10, "X", 0, 0),
        ("boundary_binary", core.pattern(33), 16, "b", 1, 17),
        ("full_byte_range", bytes(range(256)), 16, "o", 0, 0),
        ("four_kib", core.pattern(4096), 32, "x", 1, 0),
        ("max_padding_success", b"Z", 13108, "x", 0, 0),
        ("padding_failure", b"Z", 13109, "x", 0, 0),
    ]
    for name, data, cols, fmt, prefix, limit in ordinary:
        result.append(dict(name=name, kind="panic" if name == "padding_failure" else "normal",
                           args=[f"--cols={cols}", f"--format={fmt}", f"--prefix={prefix}", "--color=0", f"--len={limit}"],
                           data=data, cols=cols, fmt=fmt, prefix=prefix, limit=limit))
    assert len(result) == 48, len(result)
    assert len({case["name"] for case in result}) == 48
    return result


def execute(case: dict) -> None:
    args = list(case["args"])
    data = case["data"]
    expected_data = data
    inp = data
    temporary = None
    try:
        if case["kind"] == "file":
            temporary = tempfile.TemporaryDirectory(dir=".", prefix="mg-check-file-")
            base = Path(temporary.name)
            source = base / "name with spaces.bin"
            source.write_bytes(data)
            if case.get("symlink"):
                link = base / "read via symlink.bin"
                link.symlink_to(source.absolute())
                source = link
            args.append(str(source))
            inp = b"this stdin must be ignored"
        proc = subprocess.run(["./executable", *args], input=inp, capture_output=True, timeout=15)
        if case["kind"] == "function":
            expected = expected_function(case["n"], case["places"])
            assert (proc.returncode, proc.stdout, proc.stderr) == (0, expected, b""), (proc.returncode, proc.stdout[:300], expected[:300], proc.stderr[:300])
        elif case["kind"] == "error":
            assert proc.returncode == case["status"] and proc.stdout == b"", (proc.returncode, proc.stdout[:100])
            assert case["substring"].encode() in proc.stderr, proc.stderr[:400]
        elif case["kind"] == "color":
            expected = expected_color(data, cols=case["cols"], fmt=case["fmt"], prefix=case["prefix"], limit=case["limit"])
            assert (proc.returncode, proc.stdout, proc.stderr) == (0, expected, b""), (proc.returncode, proc.stdout[:300], expected[:300], proc.stderr[:300])
        elif case["kind"] == "panic":
            assert proc.returncode == 101 and proc.stdout == b"0x000000: 5a ", (proc.returncode, proc.stdout[:150])
            assert b"Formatting argument out of range" in proc.stderr, proc.stderr[:400]
        else:
            expected = core.expected_normal(expected_data, cols=case["cols"], fmt=case["fmt"], prefix=case["prefix"], limit=case["limit"])
            assert (proc.returncode, proc.stdout, proc.stderr) == (0, expected, b""), (proc.returncode, proc.stdout[:300], expected[:300], proc.stderr[:300])
    finally:
        if temporary is not None:
            temporary.cleanup()


def run_suite() -> int:
    suite = ET.Element("testsuite", name="mathgraph_residual", tests="48", errors="0", failures="0", skipped="0")
    failures = 0
    for case in probe_cases():
        node = ET.SubElement(suite, "testcase", classname="tests.obligations", name=case["name"])
        try:
            execute(case)
        except Exception as exc:
            failures += 1
            ET.SubElement(node, "failure", message=type(exc).__name__).text = repr(exc)[:3000]
    suite.set("failures", str(failures))
    Path("eval").mkdir(exist_ok=True)
    root = ET.Element("testsuites")
    root.append(suite)
    ET.ElementTree(root).write("eval/results.xml", encoding="utf-8", xml_declaration=True)
    print(f"obligations: {48 - failures}/48 pass, {failures} fail", flush=True)
    return int(failures > 0)


def package(destination: Path) -> None:
    target = destination / "obligations" / core.TASK
    target.mkdir(parents=True, exist_ok=True)
    contents = {
        "eval/run.sh": b"#!/bin/sh\nset -eu\npython3 eval/check.py --run\n",
        "eval/check.py": Path(__file__).read_bytes(),
        "eval/mathgraph_testgen_ablation.py": Path(core.__file__).read_bytes(),
    }
    with tarfile.open(target / "tests.tar.gz", "w:gz") as tar:
        for name, content in contents.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            entry.mode = 0o755 if name.endswith(".sh") else 0o644
            tar.addfile(entry, io.BytesIO(content))
    print("obligations", len(probe_cases()), target / "tests.tar.gz")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--package", type=Path)
    cli.add_argument("--run", action="store_true")
    options = cli.parse_args()
    if options.package:
        package(options.package)
    elif options.run:
        raise SystemExit(run_suite())
    else:
        cli.error("one of --package or --run is required")
