"""Independent native V54 verification of executable token-rewrite programs.

The original experiment supplies the mutation and test functions.  This verifier
imports only those definitions, reconstructs clean native worlds from pinned Git
objects, and reruns their tests.  Producer verdicts and producer working trees
are never evaluation inputs.  Run the CLI with Python ``-I``.
"""

import argparse
import ast
from collections import Counter
import hashlib
import io
import json
import keyword
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import tokenize


SOURCE_COMMIT = "2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c"
SOURCE_PATH = "experiments/METALOGIC_TWO_GENERATION_COMPOUNDING_V54.py"
SOURCE_SHA256 = "13c05aea8d6c1ce2db6d3d4b85c566ee3dbd2f3fcc1c3c8c14c1c2dece7f05ba"
WORLD_PINS = {
    "django": "c6be0bf3bb744d234947cefd6def9f31d9655800",
    "requests": "8068356288978c4f54661ae6f95afe0e0831885e",
    "rich": "9d8f9a372cc5916fd4781fec207ced7ddac2f08f",
}
PYTHON = Path("/workspace/v54-venv/bin/python")
TESTS = {
    "django_truncate": ("django", "test_dj_trunc", "python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0"),
    "django_pagination": ("django", "test_dj_page", "python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0"),
    "requests_iter_slices": ("requests", "test_rq", "timeout 7s pytest -q tests/test_utils.py -k test_iter_slices"),
    "rich_json": ("rich", "test_rich", "pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only"),
}
TASK_SCOPE = {"protocol": "V54_TWO_GENERATION_COMPOUNDING_20260814", "first_word": "if", "tests": {k: v[2] for k, v in TESTS.items()}}
STAGES = {"o1": "o1", "O1": "o1", "o2": "final", "O2": "final", "final": "final", "restore": "final", "cold_restart": "final", "cold-restart": "final"}
ORIGINAL_FUNCTIONS = {"tokens", "sites", "mutate", "line_first_word", "test_dj_trunc", "test_dj_page", "test_rq", "test_rich"}


class V54VerificationError(ValueError):
    """A pinned input or native verification invariant was violated."""


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _git(repo, *args):
    return subprocess.check_output(["git", "--no-replace-objects", "-C", str(repo), *args], timeout=60, stderr=subprocess.PIPE)


def source_bytes(source_repo):
    """Read and authenticate the original experiment without executing its body."""
    content = _git(source_repo, "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}")
    if _sha(content) != SOURCE_SHA256:
        raise V54VerificationError("original_source_pin_mismatch")
    return content


def _original_environment(content):
    tree = ast.parse(content, filename=f"{SOURCE_COMMIT}:{SOURCE_PATH}")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ORIGINAL_FUNCTIONS]
    if {node.name for node in functions} != ORIGINAL_FUNCTIONS:
        raise V54VerificationError("original_function_missing")
    env = {"io": io, "json": json, "keyword": keyword, "tokenize": tokenize, "Counter": Counter, "Path": Path}
    exec(compile(ast.Module(body=functions, type_ignores=[]), SOURCE_PATH, "exec"), env)
    return env


def _program(program, stage):
    """Validate executable operators; evidence fields never establish a result."""
    if stage not in STAGES:
        raise V54VerificationError("task_out_of_scope")
    scope = "if"
    if isinstance(program, dict):
        scope = program.get("scope_word", program.get("scope", "if"))
        if isinstance(scope, dict):
            scope = scope.get("first_word")
        if "task" in program and program["task"] not in {"v54", TASK_SCOPE["protocol"]}:
            raise V54VerificationError("task_out_of_scope")
        operators = program.get("operators")
        if operators is None and "O1" in program:
            operators = [program["O1"]] + ([program["O2"]] if "O2" in program else [])
    else:
        operators = program
    if scope != "if":
        raise V54VerificationError("scope_out_of_scope")
    if not isinstance(operators, list) or len(operators) != (1 if STAGES[stage] == "o1" else 2):
        raise V54VerificationError("missing_or_extra_operator")
    for operator in operators:
        if not isinstance(operator, dict) or operator.get("kind") != "TOKEN_REWRITE":
            raise V54VerificationError("operator_code_missing_or_altered")
        if set(operator) - {"kind", "src", "dst", "scope", "scope_word"}:
            raise V54VerificationError("operator_code_missing_or_altered")
        if operator.get("scope_word", operator.get("scope", "if")) != "if":
            raise V54VerificationError("scope_out_of_scope")
        for key in ("src", "dst"):
            value = operator.get(key)
            if not isinstance(value, str) or not value or "\n" in value:
                raise V54VerificationError("operator_code_missing_or_altered")
            items = [t for t in tokenize.generate_tokens(io.StringIO(value).readline) if t.type not in {tokenize.ENDMARKER, tokenize.NEWLINE}]
            if len(items) != 1 or items[0].type not in {tokenize.OP, tokenize.NAME} or items[0].string != value:
                raise V54VerificationError("operator_code_missing_or_altered")
        if operator["src"] == operator["dst"]:
            raise V54VerificationError("identity_operator")
    return operators


def _manifest(root, files=None):
    if files is None:
        files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() or p.is_symlink())
    records = []
    for name in files:
        path = root / name
        if path.is_symlink():
            if not path.resolve().is_relative_to(root.resolve()) or path.suffix in {".py", ".pyc", ".pyo"}:
                raise V54VerificationError("unsafe_native_source_symlink")
            records.append([name, _sha(b"symlink\0" + os.readlink(path).encode())])
        elif path.is_file():
            records.append([name, _sha(path.read_bytes())])
        else:
            raise V54VerificationError("native_source_missing")
    # Runtime cache/data files are harmless, but new executable source is not.
    extras = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.suffix in {".py", ".pyc", ".pyo"}} - set(files)
    if extras:
        raise V54VerificationError("unexpected_native_code")
    return records, _sha(_json_bytes(records))


def _snapshot(repo, commit, target):
    actual = _git(repo, "rev-parse", f"{commit}^{{commit}}").decode().strip()
    if actual != commit:
        raise V54VerificationError("native_commit_pin_mismatch")
    archive = _git(repo, "archive", "--format=tar", commit)
    target.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir() or member.issym()):
                raise V54VerificationError("unsafe_native_archive_entry")
            destination = target / path
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.issym():
                destination.parent.mkdir(parents=True, exist_ok=True)
                link = Path(member.linkname)
                if link.is_absolute() or not (destination.parent / link).resolve().is_relative_to(target.resolve()):
                    raise V54VerificationError("unsafe_native_archive_symlink")
                destination.symlink_to(member.linkname)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(tar.extractfile(member).read())
    # git archive honors repository-local attributes.  The exported bytes must
    # therefore also match every blob in the pinned tree, including files an
    # untrusted producer might try to export-ignore or export-subst.
    entries = _git(repo, "ls-tree", "-r", "-z", commit).split(b"\0")
    expected = {}
    for entry in entries:
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, object_id = header.decode().split()
        if kind != "blob" or mode not in {"100644", "100755", "120000"}:
            raise V54VerificationError("unsupported_native_tree_entry")
        expected[name.decode()] = (mode, object_id)
    actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file() or p.is_symlink()}
    if actual != set(expected):
        raise V54VerificationError("native_archive_tree_mismatch")
    for name, (mode, object_id) in expected.items():
        path = target / name
        if path.is_symlink() != (mode == "120000"):
            raise V54VerificationError("native_archive_blob_mismatch")
        content = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        blob = b"blob " + str(len(content)).encode() + b"\0" + content
        if hashlib.sha1(blob).hexdigest() != object_id:
            raise V54VerificationError("native_archive_blob_mismatch")
    manifest, digest = _manifest(target)
    if any(name.endswith((".pyc", ".pyo")) for name, _ in manifest):
        raise V54VerificationError("native_archive_contains_bytecode")
    return {"commit": commit, "git_tree": _git(repo, "rev-parse", f"{commit}^{{tree}}").decode().strip(), "source_sha256": digest, "file_count": len(manifest)}, [record[0] for record in manifest]


_NATIVE_RUNNER = r'''
import hashlib, importlib, json, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1]).resolve()
package, report, mode = sys.argv[2:5]
args = sys.argv[5:]
venv = pathlib.Path(sys.executable).parent.parent
dependency_path = venv / 'lib' / ('python%d.%d' % sys.version_info[:2]) / 'site-packages'
sys.path[:] = [str(root / 'src'), str(root), str(root / 'tests')] + sys.path + [str(dependency_path)]
sys.dont_write_bytecode = True
code = 1
started_tests = []
def write_report():
    global code
    imports, aliases = [], []
    for name, module in sorted(tuple(sys.modules.items())):
        if name == package or name.startswith(package + '.'):
            filename = getattr(module, '__file__', None)
            if not filename:
                continue
            source = pathlib.Path(filename).resolve()
            actual_name = getattr(module, '__name__', '')
            if package == 'requests' and name.startswith('requests.packages.') and not actual_name.startswith('requests.'):
                alias_root = name.removeprefix('requests.packages.').split('.')[0]
                if alias_root in {'urllib3', 'idna', 'chardet', 'charset_normalizer'} and source.is_relative_to(dependency_path) and sys.modules.get(actual_name) is module:
                    aliases.append([name, actual_name, str(source), hashlib.sha256(source.read_bytes()).hexdigest()])
                    continue
            if not source.is_relative_to(root) or source.suffix != '.py':
                code = 97
            imports.append([name, str(source.relative_to(root)) if source.is_relative_to(root) else str(source), hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None])
    if not imports:
        code = 98
    dependency_sources = []
    for name, module in sorted(tuple(sys.modules.items())):
        filename = getattr(module, '__file__', None)
        if filename and pathlib.Path(filename).resolve().is_relative_to(dependency_path):
            source = pathlib.Path(filename).resolve()
            if source.is_file():
                dependency_sources.append([name, str(source.relative_to(dependency_path)), hashlib.sha256(source.read_bytes()).hexdigest()])
    pathlib.Path(report).write_text(json.dumps({'exit_code': code, 'imports': imports, 'dependency_aliases': aliases, 'started_tests': started_tests, 'dependency_sources_sha256': hashlib.sha256(json.dumps(dependency_sources, separators=(',', ':')).encode()).hexdigest(), 'python_version': sys.version, 'python_executable': sys.executable, 'pytest_version': getattr(sys.modules.get('pytest'), '__version__', None)}))
class TestStartWitness:
    def pytest_runtest_logstart(self, nodeid, location):
        started_tests.append(nodeid)
        write_report()
try:
    importlib.import_module(package)
    write_report()
    if mode == 'django':
        sys.argv = [str(root / 'tests/runtests.py')] + args
        runpy.run_path(sys.argv[0], run_name='__main__')
        code = 0
    else:
        import pytest
        code = int(pytest.main(args, plugins=[TestStartWitness()]))
except SystemExit as error:
    code = error.code if isinstance(error.code, int) else (0 if error.code is None else 1)
finally:
    write_report()
raise SystemExit(code)
'''


class _NativeAuthority:
    def __init__(self, env, snapshots, files, receipt_root, python_path):
        self.env, self.snapshots, self.files, self.receipt_root = env, snapshots, files, receipt_root
        self.receipts = []
        self.label = ""
        self.python_path = Path(python_path).absolute()
        env.update(DJ=snapshots["django"], RQ=snapshots["requests"], RH=snapshots["rich"], sh=self.sh)

    def sh(self, command, cwd, timeout=40):
        matches = [(name, value) for name, value in TESTS.items() if value[2] == command and self.snapshots[value[0]] == cwd]
        if len(matches) != 1:
            raise V54VerificationError("native_command_out_of_scope")
        test_name, (world, _, _) = matches[0]
        root = self.snapshots[world]
        manifest_before, before = _manifest(root, self.files[world])
        report = self.receipt_root / f"imports-{len(self.receipts)}.json"
        if world == "django":
            args = command.split()[2:]
        elif world == "requests":
            args = command.split()[4:]
        else:
            args = command.split()[1:]
        argv = [str(self.python_path), "-I", "-S", "-B", "-c", _NATIVE_RUNNER, str(root), world, str(report), world, *args]
        clean_env = {"PATH": str(self.python_path.parent) + ":/usr/bin:/bin", "HOME": str(self.receipt_root), "LANG": "C.UTF-8", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        started = time.perf_counter()
        try:
            process = subprocess.run(argv, cwd=root, env=clean_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=7 if world == "requests" else timeout)
            returncode, output, timed_out = process.returncode, process.stdout, False
        except subprocess.TimeoutExpired as error:
            returncode, output, timed_out = None, error.stdout or b"", True
        _, after = _manifest(root, self.files[world])
        native_report = json.loads(report.read_text()) if report.exists() else None
        imports = native_report["imports"] if native_report else []
        source_records = dict(manifest_before)
        imports_valid = bool(imports) and all(source_records.get(name) == digest for _, name, digest in imports)
        passed = returncode == 0 and not timed_out and before == after and imports_valid
        receipt = {"label": self.label, "test": test_name, "world": world, "original_command": command, "exit_code": returncode, "timed_out": timed_out, "passed": passed, "source_before_sha256": before, "source_after_sha256": after, "source_unchanged": before == after, "imports_verified": imports_valid, "import_count": len(imports), "imports_sha256": _sha(_json_bytes(imports)), "dependency_aliases_sha256": _sha(_json_bytes(native_report.get("dependency_aliases", []) if native_report else [])), "stdout_sha256": _sha(output), "stdout_tail": output.decode(errors="replace")[-2500:], "elapsed_seconds": time.perf_counter() - started}
        if native_report:
            receipt.update({key: native_report.get(key) for key in ("dependency_sources_sha256", "python_version", "python_executable", "pytest_version")})
            receipt["started_tests"] = native_report.get("started_tests", [])
        self.receipts.append(receipt)
        # A timeout is a valid broken Requests outcome (the original test uses
        # timeout 7s), but import/source corruption is never a negative witness.
        if before != after or not imports_valid:
            raise V54VerificationError("native_source_or_import_integrity_failure")
        if timed_out and (world != "requests" or not native_report.get("started_tests")):
            raise V54VerificationError("timeout_without_original_requests_test_witness")
        return passed, receipt["stdout_tail"]

    def test(self, name, label):
        self.label = label
        return self.env[TESTS[name][1]]()


def _write_receipt(out, receipt):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    receipt["receipt_sha256"] = _sha(_json_bytes(receipt))
    with out.open("x") as handle:
        handle.write(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    out.chmod(0o444)


def receipt_binding_valid(receipt, stage, program):
    """Check an existing receipt's exact binding; native admission must rerun verify."""
    if not isinstance(receipt, dict):
        return False
    content = dict(receipt)
    digest = content.pop("receipt_sha256", None)
    return digest == _sha(_json_bytes(content)) and receipt.get("stage") == stage and receipt.get("program_sha256") == _sha(_json_bytes(program)) and receipt.get("scope_sha256") == _sha(_json_bytes(TASK_SCOPE)) and receipt.get("source_sha256") == SOURCE_SHA256 and receipt.get("status") == "accepted"


def verify(stage: str, program: dict | list, source_repo: Path, worlds: Path, out: Path, *, python_path: Path | None = None) -> dict:
    """Rerun pinned native tests and write one new, immutable verification receipt."""
    started = time.perf_counter()
    program_bytes = _json_bytes(program)
    program = json.loads(program_bytes)
    receipt = {"protocol": "UDM_V54_INDEPENDENT_NATIVE_VERIFICATION_V1", "stage": stage, "status": "error", "evaluated": False, "source_commit": SOURCE_COMMIT, "source_path": SOURCE_PATH, "source_sha256": SOURCE_SHA256, "verifier_source_sha256": _sha(Path(__file__).read_bytes()), "native_runner_sha256": _sha(_NATIVE_RUNNER.encode()), "program_sha256": _sha(program_bytes), "scope": TASK_SCOPE, "scope_sha256": _sha(_json_bytes(TASK_SCOPE)), "producer_worktree_ignored": True, "native_receipts": []}
    authority = None
    try:
        operators = _program(program, stage)
        content = source_bytes(Path(source_repo))
        env = _original_environment(content)
        native_python = Path(python_path or sys.executable)
        if not native_python.is_file():
            raise V54VerificationError("native_python_missing")
        with tempfile.TemporaryDirectory(prefix="v54-independent-native-") as directory:
            temporary = Path(directory)
            snapshots, files, pins = {}, {}, {}
            for world, commit in WORLD_PINS.items():
                snapshots[world] = temporary / world
                pins[world], files[world] = _snapshot(Path(worlds) / world, commit, snapshots[world])
            receipt["native_pins"] = pins
            receipt["native_python"] = str(native_python.absolute())
            authority = _NativeAuthority(env, snapshots, files, temporary, native_python)
            receipt["evaluated"] = True
            gates = {}
            original_texts = {}

            def breaking_site(world, relative, src, dst, test):
                path = snapshots[world] / relative
                base = path.read_bytes()
                original_texts[path] = base
                if not authority.test(test, f"{test}:baseline"):
                    raise V54VerificationError("native_baseline_failed")
                bads = []
                for site in env["sites"](path, src):
                    path.write_bytes(base)
                    old_line = env["mutate"](path, site, dst)
                    if not authority.test(test, f"{test}:breaking_site:{site[0]}:{site[1]}"):
                        bads.append((site, old_line))
                path.write_bytes(base)
                if len(bads) != 1:
                    raise V54VerificationError("original_unique_breaking_site_not_unique")
                return path, bads[0][0], bads[0][1]

            trunc, trunc_site, trunc_line = breaking_site("django", "django/db/backends/utils.py", "<=", "<", "django_truncate")
            page, page_site, page_line = breaking_site("django", "django/core/paginator.py", "<=", "<", "django_pagination")
            rich, rich_site, rich_line = breaking_site("rich", "rich/highlighter.py", "<", "<=", "rich_json")
            request, request_site, request_line = breaking_site("requests", "src/requests/utils.py", "<=", "<", "requests_iter_slices")
            scope_words = {env["line_first_word"](trunc_line), env["line_first_word"](page_line)}
            harm_word = env["line_first_word"](rich_line)
            gates["learned_scope_matches"] = scope_words == {"if"} and harm_word != "if"
            receipt["scope_witness"] = {"help_first_words": sorted(scope_words), "harm_first_word": harm_word}

            def apply(path, operator, line_no=None, scoped=True):
                candidates = env["sites"](path, operator["src"], line_no)
                candidates = [site for site in candidates if not scoped or env["line_first_word"](path.read_text().splitlines()[site[0] - 1]) == "if"]
                if line_no is not None and len(candidates) != 1:
                    return False
                for site in reversed(candidates):
                    env["mutate"](path, site, operator["dst"])
                return bool(candidates)

            for path, site, test in ((trunc, trunc_site, "django_truncate"), (page, page_site, "django_pagination")):
                path.write_bytes(original_texts[path])
                env["mutate"](path, site, "<")
                applied = apply(path, operators[0], site[0])
                gates[test + "_repaired"] = applied and authority.test(test, test + ":candidate_O1")
                path.write_bytes(original_texts[path])

            rich.write_bytes(original_texts[rich])
            apply(rich, operators[0])
            gates["rich_scoped_preserved"] = authority.test("rich_json", "rich:scoped_O1")
            rich.write_bytes(original_texts[rich])
            apply(rich, operators[0], scoped=False)
            gates["rich_global_rejected"] = not authority.test("rich_json", "rich:deliberately_global_O1")
            rich.write_bytes(original_texts[rich])

            or_sites = env["sites"](request, "or", request_site[0])
            if not or_sites:
                raise V54VerificationError("original_requests_OR_site_missing")
            def double_broken():
                request.write_bytes(original_texts[request])
                env["mutate"](request, request_site, "<")
                live_or = [s for s in env["sites"](request, "or", request_site[0]) if s[1] == or_sites[0][1]]
                if len(live_or) != 1:
                    raise V54VerificationError("original_requests_OR_site_lost")
                env["mutate"](request, live_or[0], "and")

            double_broken()
            gates["requests_cold_fails"] = not authority.test("requests_iter_slices", "requests:double_broken")
            first_applied = apply(request, operators[0], request_site[0])
            gates["requests_O1_residual_fails"] = first_applied and not authority.test("requests_iter_slices", "requests:O1_only")
            if STAGES[stage] == "final":
                second_applied = apply(request, operators[1], request_site[0])
                gates["requests_O1_O2_passes"] = second_applied and authority.test("requests_iter_slices", "requests:O1_then_O2")
                double_broken()
                second_applied = apply(request, operators[1], request_site[0])
                gates["requests_O1_ablation_fails"] = second_applied and not authority.test("requests_iter_slices", "requests:O1_ablated")
            request.write_bytes(original_texts[request])
            receipt["gates"] = gates
            receipt["native_receipts"] = authority.receipts
            receipt["source_unchanged"] = all(_manifest(snapshots[world], files[world])[1] == pins[world]["source_sha256"] for world in WORLD_PINS)
            receipt["status"] = "accepted" if gates and all(gates.values()) and receipt["source_unchanged"] else "rejected"
            receipt["reason"] = "native_success" if receipt["status"] == "accepted" else "native_failure"
    except V54VerificationError as error:
        receipt.update(status="rejected", reason=str(error), error_type=type(error).__name__)
    except Exception as error:
        receipt.update(status="error", reason=str(error), error_type=type(error).__name__)
    finally:
        if authority is not None:
            receipt["native_receipts"] = authority.receipts
        receipt["elapsed_seconds"] = time.perf_counter() - started
    _write_receipt(out, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--worlds", type=Path, required=True)
    parser.add_argument("--operators", required=True, help="JSON file or literal JSON executable program")
    parser.add_argument("--scope", default="if")
    parser.add_argument("--stage", default="final")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = args.operators.lstrip()
    operator_file = None if value.startswith(("[", "{")) else Path(value)
    program = json.loads(value if operator_file is None else operator_file.read_text())
    if args.out.resolve() == (operator_file.resolve() if operator_file else None):
        parser.error("--out must not overwrite the executable program")
    if isinstance(program, list):
        program = {"operators": program, "scope_word": args.scope}
    elif args.scope != "if" or "scope_word" not in program and "scope" not in program:
        program = dict(program, scope_word=args.scope)
    receipt = verify(args.stage, program, args.source, args.worlds, args.out)
    print(json.dumps({"status": receipt["status"], "reason": receipt.get("reason"), "receipt_sha256": receipt["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
