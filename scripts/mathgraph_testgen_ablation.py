"""Frozen, reference-blind TestSuiteBench probe-selection ablation (hex task).

Both suites share the same executable-independent oracle and 48 test cases.
Only their test selection differs. This is NOT an AI-agent head-to-head.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import subprocess
import tarfile
import xml.etree.ElementTree as ET

TASK = "sitkevij__hex.61ae69b"
LANGUAGES = "rcgpkjsf"


def expected_normal(data: bytes, *, cols: int = 10, fmt: str = "x", prefix: int = 1, limit: int = 0) -> bytes:
    retained = data if limit == 0 else data[:limit]
    effective = max(cols, 1)
    rows = []
    for start in range(0, len(retained) + 1, effective):
        chunk = retained[start:start + effective]
        if fmt == "x":
            token = lambda b: f"{b:02x}"
            lead = "0x"
        elif fmt == "X":
            token = lambda b: f"{b:02X}"
            lead = "0x"
        elif fmt == "o":
            token = lambda b: f"{b:04o}"
            lead = "0o"
        else:
            token = lambda b: f"{b:08b}"
            lead = "0b"
        numbers = "".join((lead if prefix else "") + token(b) + " " for b in chunk)
        padding = " " * (5 * (cols - len(chunk)) if cols > 0 else 0)
        preview = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        rows.append(f"0x{start:06x}: {numbers}{padding}{preview}\n")
        if start + effective > len(retained):
            break
    return ("".join(rows) + f"   bytes: {len(retained)}\n").encode()


def expected_array(data: bytes, *, lang: str, cols: int = 10, limit: int = 0) -> bytes:
    retained = data if limit == 0 else data[:limit]
    openings = {
        "r": f"let ARRAY: [u8; {len(retained)}] = [",
        "c": f"unsigned char ARRAY[{len(retained)}] = {{",
        "g": f"a := [{len(retained)}]byte{{",
        "p": "a = [",
        "k": "val a = byteArrayOf(",
        "j": "byte[] a = new byte[]{",
        "s": "let a: [UInt8] = [",
        "f": "let a = [|",
    }
    closings = {"r": "];", "c": "};", "g": "}", "p": "]", "k": ")", "j": "};", "s": "]", "f": "|]"}
    effective = max(cols, 1)
    pieces = [openings[lang] + "\n"]
    for start in range(0, len(retained) + 1, effective):
        chunk = retained[start:start + effective]
        formatted = []
        for i, b in enumerate(chunk):
            idx = start + i
            value = f"0x{b:02x}" + ("uy" if lang == "f" else "")
            if idx < len(retained) - 1 or lang == "g":
                value += "; " if lang == "f" else ", "
            formatted.append(value)
        pieces.append("    " + "".join(formatted) + "\n")
        if start + effective > len(retained):
            break
    pieces.append(closings[lang] + "\n")
    return "".join(pieces).encode()


def pattern(n: int) -> bytes:
    alphabet = bytes([0, 32, 65, 127, 255, 10, 13, 97, 0xC3, 0xA9, 0x58, 0x01])
    return (alphabet * (n // len(alphabet) + 1))[:n]


def cases(mode: str) -> list[dict]:
    selected = []
    if mode == "baseline":
        for n in range(24):
            selected.append(dict(name=f"default_len_{n}", data=pattern(n), args=["-t", "0"], cols=10, fmt="x", prefix=1, limit=0))
        for fmt in "xXob":
            selected.append(dict(name=f"format_{fmt}", data=b"\xab", args=["-t0", "-f", fmt], cols=10, fmt=fmt, prefix=1, limit=0))
        for cols in (1, 2, 5, 10):
            selected.append(dict(name=f"cols_{cols}", data=b"Z", args=["-t0", "-c", str(cols)], cols=cols, fmt="x", prefix=1, limit=0))
        for limit in (0, 1, 2, 4):
            selected.append(dict(name=f"limit_{limit}", data=b"ABCD", args=["-t0", "-l", str(limit)], cols=10, fmt="x", prefix=1, limit=limit))
        for lang in LANGUAGES:
            selected.append(dict(name=f"array_{lang}", data=b"test", args=["-a", lang], cols=10, limit=0, lang=lang))
        for n in (0, 1, 3, 7):
            selected.append(dict(name=f"no_prefix_{n}", data=pattern(n), args=["-t0", "-r0"], cols=10, fmt="x", prefix=0, limit=0))
    elif mode == "signature":
        widths = (0, 1, 2, 3, 4, 5, 10, 16)
        for wi, width in enumerate(widths):
            for fi, fmt in enumerate("xXob"):
                index = wi * 4 + fi
                prefix = (wi + fi) % 2
                data_len = (0, 1, max(1, width), max(1, width) + 1)[fi]
                data_len += 2 if index % 5 == 0 else 0
                data = pattern(data_len + 3)
                limit = data_len if index % 3 != 0 else 0
                selected.append(dict(
                    name=f"cross_{index:02d}_c{width}_f{fmt}_p{prefix}_l{limit}",
                    data=data, args=[f"--cols={width}", "--format", fmt, f"--prefix={prefix}", "--color=0", f"--len={limit}"],
                    cols=width, fmt=fmt, prefix=prefix, limit=limit,
                ))
        for li, lang in enumerate(LANGUAGES):
            for vi in range(2):
                width = (1, 2, 3, 4)[(li + vi) % 4]
                size = (0, 1, width, width + 1)[(li * 2 + vi) % 4]
                input_data = pattern(size + 3)
                limit = size if size else 0
                if size == 0:
                    input_data = b""
                args = [f"--array={lang}", f"--cols={width}", f"--len={limit}", "--format=b", "--color=1", "--prefix=0"]
                selected.append(dict(name=f"array_cross_{lang}_{vi}", data=input_data, args=args, cols=width, limit=limit, lang=lang))
    else:
        raise ValueError(mode)
    assert len(selected) == 48, (mode, len(selected))
    assert len({x['name'] for x in selected}) == 48
    return selected


def run_suite(mode: str) -> int:
    suite = ET.Element("testsuite", name=f"mathgraph_{mode}", tests="48", errors="0", failures="0", skipped="0")
    failures = 0
    for case in cases(mode):
        node = ET.SubElement(suite, "testcase", classname=f"tests.{mode}", name=case["name"])
        try:
            proc = subprocess.run(["./executable", *case["args"]], input=case["data"], capture_output=True, timeout=12)
            if "lang" in case:
                expected = expected_array(case["data"], lang=case["lang"], cols=case["cols"], limit=case["limit"])
            else:
                expected = expected_normal(case["data"], cols=case["cols"], fmt=case["fmt"], prefix=case["prefix"], limit=case["limit"])
            assert (proc.returncode, proc.stdout, proc.stderr) == (0, expected, b""), (
                f"returncode={proc.returncode}; stdout={proc.stdout[:700]!r}; "
                f"expected={expected[:700]!r}; stderr={proc.stderr[:700]!r}"
            )
        except Exception as exc:
            failures += 1
            ET.SubElement(node, "failure", message=type(exc).__name__).text = str(exc)[:2500]
    suite.set("failures", str(failures))
    Path("eval").mkdir(exist_ok=True)
    root = ET.Element("testsuites")
    root.append(suite)
    ET.ElementTree(root).write("eval/results.xml", encoding="utf-8", xml_declaration=True)
    print(f"{mode}: {48 - failures}/48 pass, {failures} fail", flush=True)
    return 1 if failures else 0


def package_suites(root: Path) -> None:
    source = Path(__file__).read_bytes()
    for mode in ("baseline", "signature"):
        cases(mode)
        destination = root / mode / TASK
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(destination / "tests.tar.gz", "w:gz") as tar:
            for name, content in {
                "eval/run.sh": b"#!/bin/sh\nset -eu\npython3 eval/check.py --run " + mode.encode() + b"\n",
                "eval/check.py": source,
            }.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o755 if name.endswith(".sh") else 0o644
                tar.addfile(info, io.BytesIO(content))
        print(mode, len(cases(mode)), destination / "tests.tar.gz")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path)
    parser.add_argument("--run", choices=("baseline", "signature"))
    args = parser.parse_args()
    if args.package:
        package_suites(args.package)
    elif args.run:
        raise SystemExit(run_suite(args.run))
    else:
        parser.error("one of --package or --run is required")
