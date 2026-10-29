"""Frozen, spec-first TestSuiteBench transfer challenge for sd.

Two 48-case, executable-independent suites. This file was designed before
receiving any sd mutant feedback. No reference or mutant executable is read
to generate the test oracle. This does not constitute an AI model comparison.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET

TASK = "chmln__sd.87d1ba5"


def case(name: str, args: list[str], data: bytes = b"", expected: bytes = b"", *,
         code: int = 0, stderr_contains: tuple[bytes, ...] = (),
         files: dict[str, bytes] | None = None, after: dict[str, bytes] | None = None) -> dict:
    return dict(name=name, args=args, data=data, expected=expected,
                code=code, stderr_contains=stderr_contains,
                files=files or {}, after=after or {})


def cases(mode: str) -> list[dict]:
    result: list[dict] = []
    add = result.append

    if mode == "baseline":
        words = ["alpha", "beta", "cat", "dog", "red", "blue", "sun", "moon"]
        for i in range(24):
            find = words[i % len(words)]
            repl = f"R{i}"
            payload = f"{find} {find.upper()} {find} {find}!".encode()
            add(case(f"fixed_basic_{i}", ["-F", find, repl], payload,
                     payload.replace(find.encode(), repl.encode())))
        for i in range(8):
            find = words[i]
            payload = (find + " other " + find + "\n" + find).encode()
            add(case(f"regex_literal_{i}", [find, "X"], payload,
                     payload.replace(find.encode(), b"X")))
        for i in range(8):
            find = f"missing{i}"
            payload = f"nothing here {i}\n".encode()
            add(case(f"no_match_{i}", [find, "X"], payload, payload))
        for i in range(8):
            payload = (f"item{i} " * (i + 1)).encode()
            add(case(f"fixed_limit_{i}", ["-F", "-n", "1", f"item{i}", "X"], payload,
                     payload.replace(f"item{i}".encode(), b"X", 1)))
    elif mode == "signature":
        # 1. Option/state composition: precedence, empty flags and reset.
        flag_cases = [
            ("flags_ic", ["-f", "ic", "test", "X"], b"Test TEST test", b"Test TEST X"),
            ("flags_ci", ["-f", "ci", "test", "X"], b"Test TEST test", b"X X X"),
            ("flags_iw", ["-f", "iw", "test", "X"], b"Test TEST test", b"Test TEST X"),
            ("flags_wi", ["-f", "wi", "test", "X"], b"Test TEST test", b"X X X"),
            ("flags_empty", ["--flags=", "^line", "X"], b"line1\nline2", b"X1\nX2"),
            ("flags_e", ["--flags=e", "^line", "X"], b"line1\nline2", b"X1\nline2"),
            ("flags_m", ["--flags=m", "^line", "X"], b"line1\nline2", b"X1\nX2"),
            ("flags_s", ["--flags=s", "a.*b", "X"], b"a\nb", b"X"),
            ("flags_normal", ["a.*b", "X"], b"a\nb", b"a\nb"),
            ("flags_unknown", ["--flags=q", "test", "X"], b"test", b"X"),
            ("flags_fixed_i", ["-F", "-f", "i", "test", "X"], b"Test TEST test", b"X X X"),
            ("flags_reset_w", ["-f", "iwi", "test", "X"], b"Test TEST test", b"X X X"),
        ]
        for name, argv, payload, output in flag_cases:
            add(case(name, argv, payload, output))

        # 2. Per-input limits and option spelling/interleaving.
        limit_cases = [
            ("limit_zero", ["-n", "0", "foo", "X"], b"foo foo foo", b"X X X"),
            ("limit_one", ["-n", "1", "foo", "X"], b"foo foo foo", b"X foo foo"),
            ("limit_two", ["-n=2", "foo", "X"], b"foo foo foo", b"X X foo"),
            ("limit_long", ["--max-replacements=3", "foo", "X"], b"foo foo foo foo", b"X X X foo"),
            ("limit_large", ["--max-replacements", "999999999", "foo", "X"], b"foo foo", b"X X"),
            ("limit_after", ["foo", "X", "--max-replacements", "1"], b"foo foo", b"X foo"),
            ("limit_with_fixed", ["-F", "foo", "X", "-n", "1"], b"foo foo", b"X foo"),
            ("limit_empty_input", ["-n", "2", "foo", "X"], b"", b""),
        ]
        for name, argv, payload, output in limit_cases:
            add(case(name, argv, payload, output))

        # 3. Literal/regex boundary, replacement escapes, Unicode and binary.
        byte_cases = [
            ("literal_dot", ["-F", "a.b", "X"], b"a.b a0b", b"X a0b"),
            ("regex_dot", ["a.b", "X"], b"a.b a0b", b"X X"),
            ("literal_dollar", ["-F", "foo", "$1bad"], b"foo", b"$1bad"),
            ("literal_slash_n", ["-F", "foo", r"\n"], b"foo", b"\\n"),
            ("regex_slash_n", ["foo", r"\n"], b"foo", b"\n"),
            ("regex_capture", [r"(\w+) (\w+)", "$2 $1"], b"hello world", b"world hello"),
            ("fixed_binary", ["-F", "foo", "R"], b"\x00\x01foo\xff\xfe", b"\x00\x01R\xff\xfe"),
            ("fixed_unicode", ["-F", "café", "tea"], "café café!".encode(), b"tea tea!"),
            ("crlf_preserve", ["-F", "foo", "X"], b"foo\r\nfoo\rbar\n", b"X\r\nX\rbar\n"),
            ("empty_regex", ["", "X"], b"abc", b"XaXbXcX"),
            ("replace_hex_quirk", ["foo", r"\x41X"], b"foo", b"A"),
            ("replace_unicode_quirk", ["foo", r"\u0041X"], b"foo", b"A"),
        ]
        for name, argv, payload, output in byte_cases:
            add(case(name, argv, payload, output))

        # 4. CLI grammar and independent file-state contracts.
        add(case("terminator_find", ["--", "--foo", "X"], b"--foo", b"X"))
        add(case("terminator_replace", ["foo", "--", "-w"], b"foo", b"-w"))
        add(case("option_after_positionals", ["foo", "X", "-F"], b"foo foo", b"X X"))
        add(case("clustered_boolean", ["-pF", "foo", "X"], b"foo", b"X"))
        add(case("alias_fixed", ["-s", ".", "X"], b". a", b"X a"))
        add(case("repeated_preview_invalid", ["-p", "-p", "foo", "X"], b"foo", b"", code=2,
                 stderr_contains=(b"multiple times",)))
        add(case("file_in_place", ["-F", "foo", "X", "a.txt"], files={"a.txt": b"foo\nfoo"},
                 after={"a.txt": b"X\nX"}))
        add(case("file_preview", ["-pF", "foo", "X", "a.txt"], expected=b"X\nX",
                 files={"a.txt": b"foo\nfoo"}, after={"a.txt": b"foo\nfoo"}))
        add(case("multi_file_limit", ["-F", "-n", "1", "foo", "X", "a.txt", "b.txt"],
                 files={"a.txt": b"foo foo", "b.txt": b"foo foo"},
                 after={"a.txt": b"X foo", "b.txt": b"X foo"}))
        add(case("missing_file_atomic", ["-F", "foo", "X", "a.txt", "not_there.txt"],
                 files={"a.txt": b"foo"}, after={"a.txt": b"foo"}, code=1,
                 stderr_contains=(b"invalid path: not_there.txt",)))
        add(case("multi_preview", ["-pF", "foo", "X", "a.txt", "b.txt"],
                 expected=b"----- FILE a.txt -----\nX\n----- FILE b.txt -----\nX\n",
                 files={"a.txt": b"foo\n", "b.txt": b"foo\n"},
                 after={"a.txt": b"foo\n", "b.txt": b"foo\n"}))
        add(case("files_empty_output", ["-F", "foo", "", "a.txt"],
                 files={"a.txt": b"foo"}, after={"a.txt": b""}))
        add(case("missing_option", ["foo", "X", "--unrecognized"], b"foo", b"", code=2,
                 stderr_contains=(b"unexpected argument",)))
        add(case("invalid_limit", ["foo", "X", "--max-replacements=nan"], b"foo", b"", code=2,
                 stderr_contains=(b"invalid value",)))
        add(case("invalid_regex", ["(", "X"], b"foo", b"", code=1,
                 stderr_contains=(b"unclosed group",)))
        add(case("ambiguous_replacement", ["foo", "$1bad"], b"foo", b"", code=1,
                 stderr_contains=(b"ambiguous",)))
    else:
        raise ValueError(mode)

    assert len(result) == 48, (mode, len(result))
    assert len({r["name"] for r in result}) == 48
    return result


def run_suite(mode: str) -> int:
    suite = ET.Element("testsuite", name=f"mathgraph_sd_{mode}", tests="48", errors="0", failures="0")
    failures = 0
    executable = str(Path("executable").resolve())
    for item in cases(mode):
        node = ET.SubElement(suite, "testcase", classname=f"tests.{mode}", name=item["name"])
        try:
            with tempfile.TemporaryDirectory(prefix="mg_sd_") as td:
                root = Path(td)
                for name, content in item["files"].items():
                    (root / name).write_bytes(content)
                proc = subprocess.run([executable, *item["args"]], input=item["data"],
                                      cwd=root, capture_output=True, timeout=10)
                assert proc.returncode == item["code"], ("status", proc.returncode, item["code"], proc.stderr[:300])
                assert proc.stdout == item["expected"], ("stdout", proc.stdout[:500], item["expected"][:500])
                if item["code"] == 0:
                    assert proc.stderr == b"", ("unexpected stderr", proc.stderr[:500])
                else:
                    assert all(e in proc.stderr for e in item["stderr_contains"]), ("stderr", proc.stderr[:500])
                for name, content in item["after"].items():
                    assert (root / name).read_bytes() == content, ("file", name, (root / name).read_bytes()[:200], content[:200])
        except Exception as exc:
            failures += 1
            ET.SubElement(node, "failure", message=type(exc).__name__).text = str(exc)[:2400]
    suite.set("failures", str(failures))
    Path("eval").mkdir(exist_ok=True)
    root = ET.Element("testsuites")
    root.append(suite)
    ET.ElementTree(root).write("eval/results.xml", encoding="utf-8", xml_declaration=True)
    print(f"sd {mode}: {48-failures}/48 passed", flush=True)
    return int(bool(failures))


def package(root: Path) -> None:
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
                item = tarfile.TarInfo(name)
                item.size = len(content)
                item.mode = 0o755 if name.endswith(".sh") else 0o644
                tar.addfile(item, io.BytesIO(content))
        print(mode, len(cases(mode)), destination / "tests.tar.gz")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path)
    parser.add_argument("--run", choices=("baseline", "signature"))
    a = parser.parse_args()
    if a.package:
        package(a.package)
    elif a.run:
        raise SystemExit(run_suite(a.run))
    else:
        parser.error("select --package or --run")
