"""V6 typed Git materialization and scoped, independently observed pytest execution.

All source facts come from the original V5 read-only Git inventory. A source
entry is never an execution warrant. We stage only authentic regular blobs
and in-tree links to authentic regular blobs; gitlinks remain opaque, never
cloned, followed, or treated as Python source. Original verifiers untouched.

The native runner observes actual pytest call/deselection/collection results and
source-module imports. It trusts original test code, Python host, pytest and the
specified plugins; it is NOT a hostile-Python sandbox, not a generic G2 machine
and not an independently formalized program refinement.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from . import typed_source_inventory_v5 as typed

SCHEMA = "UDM_TYPED_GIT_NATIVE_TRANSPORT_V6"
RECEIPT_SCHEMA = "UDM_TYPED_SCOPED_NATIVE_PYTEST_V6"
VALID_MODES = {"100644": 0o644, "100755": 0o755}
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_NODE = re.compile(r"[A-Za-z0-9_./-]+::[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\Z")


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _root(path, *, exists=False):
    path = Path(path).absolute()
    if path.resolve() != path or path.is_symlink() or (exists and not path.is_dir()):
        raise ValueError("root not canonical or unavailable")
    return path


def _approved_inventory(repo, commit):
    if not isinstance(commit, str) or not _COMMIT.fullmatch(commit):
        raise ValueError("missing exact original source commit")
    report = typed.snapshot(_root(repo, exists=True), commit)
    if report["status"] != typed.SOURCE_STATUS or report["executable_authority"] != "NONE":
        raise ValueError("original typed Git snapshot not an inventory-only authority")
    for link in report["links"]:
        if link["resolution"] != "INTERNAL_REGULAR_FILE":
            raise ValueError("unsafe or unresolved original Git symlink: " + link["resolution"])
        if not any(row["path"] == link["resolved_path"] and row["mode"] in VALID_MODES
                   for row in report["manifest"]):
            raise ValueError("original Git symlink target lacks protected regular blob")
    return report


def _expected_paths(report):
    expected = {row["path"]: row for row in report["manifest"] if row["mode"] != "160000"}
    directories = set()
    for name in expected:
        path = PurePosixPath(name).parent
        while str(path) not in (".", ""):
            directories.add(str(path))
            path = path.parent
    return expected, directories


def stage(repo, commit, dest):
    """Materialize exact Git source bytes; opaque gitlinks remain metadata only.

    Abort before writing on unresolved or unsafe links. The stage is a new local
    test world, not a grant to read/excute any gitlink/submodule content.
    """
    root = _root(repo, exists=True)
    output = _root(dest)
    if output.exists() or output == root or output.is_relative_to(root):
        raise ValueError("new external output directory required")
    report = _approved_inventory(root, commit)
    expected, directories = _expected_paths(report)
    output.mkdir(parents=True)
    try:
        for dirname in sorted(directories, key=lambda x: (x.count("/"), x)):
            (output / dirname).mkdir(exist_ok=True)
        for name, row in sorted(expected.items()):
            path = output / name
            raw = typed._git(root, "cat-file", "blob", row["oid"])
            if _hash(raw) != row["sha256"]:
                raise ValueError("original Git blob digest changed")
            if row["mode"] in VALID_MODES:
                with path.open("xb") as handle:
                    handle.write(raw)
                path.chmod(VALID_MODES[row["mode"]])
            elif row["mode"] == "120000":
                link = next((x for x in report["links"] if x["path"] == name), None)
                if link is None or link["resolution"] != "INTERNAL_REGULAR_FILE":
                    raise ValueError("unqualified symlink content")
                path.symlink_to(raw.decode("utf-8", errors="strict"))
            else:
                raise ValueError("unknown stage mode")
        verify_stage(root, commit, output)
    except Exception:
        shutil.rmtree(output)
        raise
    return {"schema": SCHEMA, "status": "STAGED_TYPED_SOURCE_NO_NATIVE_WARRANT",
            "source_commit": commit, "source_tree": report["git_tree"],
            "typed_manifest_sha256": report["manifest_sha256"],
            "counts": report["counts"], "unmaterialized_gitlinks": report["gitlinks"],
            "original_source_preserved": True,
            "native_execution_authority": "NOT_YET_WARRANTED"}


def _staged_files_and_directories(output):
    entries, directories = {}, set()
    def walk(path):
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            rel = child.relative_to(output).as_posix()
            if child.is_symlink():
                entries[rel] = "link"
            elif child.is_dir():
                if not stat.S_ISDIR(child.lstat().st_mode):
                    raise ValueError("unexpected directory type")
                directories.add(rel)
                walk(child)
            elif child.is_file() and stat.S_ISREG(child.lstat().st_mode):
                entries[rel] = "regular"
            else:
                raise ValueError("unexpected staged filesystem entry")
    walk(output)
    return entries, directories


def verify_stage(repo, commit, dest):
    root = _root(repo, exists=True)
    output = _root(dest, exists=True)
    report = _approved_inventory(root, commit)
    expected, dirs = _expected_paths(report)
    actual, actual_dirs = _staged_files_and_directories(output)
    if actual_dirs != dirs:
        raise ValueError("tracked source directory tree changed or gitlink was materialized")
    if set(actual) != set(expected):
        raise ValueError("untracked, missing or materialized opaque Git source entry")
    links = {row["path"]: row for row in report["links"]}
    for name, row in sorted(expected.items()):
        path = output / name
        if row["mode"] in VALID_MODES:
            if actual[name] != "regular" or path.is_symlink():
                raise ValueError("regular Git source replaced by link or device")
            if stat.S_IMODE(path.lstat().st_mode) != VALID_MODES[row["mode"]]:
                raise ValueError("protected regular mode changed")
            if _hash(path.read_bytes()) != row["sha256"]:
                raise ValueError("protected Git source bytes changed")
        elif row["mode"] == "120000":
            if actual[name] != "link":
                raise ValueError("symbolic-link mode not preserved")
            text = os.readlink(path)
            if _hash(os.fsencode(text)) != row["sha256"]:
                raise ValueError("original symlink target bytes altered")
            if path.resolve(strict=True) != (output / links[name]["resolved_path"]).resolve(strict=True):
                raise ValueError("symlink escaped protected original Git tree")
            if not path.resolve(strict=True).is_relative_to(output):
                raise ValueError("symlink resolved outside protected stage")
        else:
            raise ValueError("unsupported protected entry")
    return {"status": "PASS_TYPED_STAGE_IDENTITY",
            "schema": SCHEMA, "source_commit": commit,
            "typed_manifest_sha256": report["manifest_sha256"],
            "counts": report["counts"], "materialized_paths": len(expected),
            "opaque_gitlinks_unexecuted": [x["path"] for x in report["gitlinks"]]}


def _mtimes(output, report):
    return {row["path"]: (output / row["path"]).lstat().st_mtime_ns
            for row in report["manifest"] if row["mode"] != "160000"}


# Runs only in an independently launched, isolated-interpreter child process.
# All files reported by original project imports are checked against Git objects
# again in the parent. Arbitrary filesystem reads by trusted tests are not proven.
_NATIVE_BOOTSTRAP = r'''
import hashlib,json,os,pathlib,sys
world=pathlib.Path(sys.argv[1]).resolve()
receipt_path=pathlib.Path(sys.argv[2]).resolve()
junit_path=pathlib.Path(sys.argv[3]).resolve()
paths=json.loads(sys.argv[4])
sys.path[:0]=[str(world/"src"),str(world)]
import pytest
class Observation:
    def __init__(self):
        self.selected=[];self.calls=[];self.deselected=[];self.setup_skipped=[]
    def pytest_collection_modifyitems(self,session,config,items):
        self.selected=[item.nodeid for item in items]
    def pytest_deselected(self,items):
        self.deselected.extend(item.nodeid for item in items)
    def pytest_runtest_logreport(self,report):
        if report.when=="call":
            self.calls.append({"nodeid":report.nodeid,"outcome":report.outcome})
        elif report.when=="setup" and report.skipped:
            self.setup_skipped.append(report.nodeid)
monitor=Observation()
# The project-supplied pytest configuration is NOT removed or overwritten.
config=None
for name in ("pytest.ini",".pytest.ini","pyproject.toml","tox.ini","setup.cfg"):
    if (world/name).is_file():
        config=world/name
        break
argv=["-q","-p","no:cacheprovider","-p","pytest_cov",
      "--junitxml="+str(junit_path),"--rootdir="+str(world)]
if config is not None:argv.extend(["-c",str(config)])
argv.extend(str(world / name) for name in paths)
try:
    code=int(pytest.main(argv,plugins=[monitor]))
except BaseException as error:
    code=4
    bootstrap_error=type(error).__name__+": "+str(error)
else:
    bootstrap_error=None
imports=[]
for name,module in tuple(sys.modules.items()):
    path=getattr(module,"__file__",None)
    if not path:continue
    try:
        resolved=pathlib.Path(path).resolve(strict=True)
    except (OSError,RuntimeError,ValueError):continue
    if resolved.is_relative_to(world):
        imports.append({"module":name,"path":str(resolved.relative_to(world)),
                        "sha256":hashlib.sha256(resolved.read_bytes()).hexdigest()})
record={"pytest":pytest.__version__,"code":code,"collected":monitor.selected,
        "deselected":monitor.deselected,"calls":monitor.calls,
        "setup_skipped":monitor.setup_skipped,
        "imports":sorted(imports,key=lambda row:(row["path"],row["module"])),
        "bootstrap_error":bootstrap_error,"argv":argv}
receipt_path.write_text(json.dumps(record,sort_keys=True)+"\n")
raise SystemExit(code)
'''


def _prefix_match(value, prefix):
    return value == prefix or value.startswith(prefix + "[") or value.startswith(prefix + "::")


def run_protected(repo, commit, dest, *, required, interpreter=sys.executable,
                  timeout=55, paths=None):
    """Return measured PASS/FAIL/UNKNOWN for a *scoped*, trusted native suite.

    This is a limited, explicit pytest/source-import authority. No original
    worker or checker is modified, and source inventory alone cannot promote.
    """
    started = time.monotonic()
    root = _root(repo, exists=True)
    output = _root(dest, exists=True)
    verified = verify_stage(root, commit, output)
    original = _approved_inventory(root, commit)
    regular = {row["path"]: row for row in original["manifest"]
               if row["mode"] in VALID_MODES}
    alias_map = {link["path"]: link["resolved_path"] for link in original["links"]}
    if not isinstance(required, (tuple, list)) or not required or any(
            not isinstance(value, str) or not _NODE.fullmatch(value)
            for value in required):
        raise ValueError("nonempty frozen native protected obligation prefixes required")
    if paths is None:
        paths = ["tests"] if (output / "tests").is_dir() else ["."]
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("empty native source testpaths")
    for path in paths:
        if not isinstance(path, str) or path.startswith("/") or "\\" in path:
            raise ValueError("untrusted native testpaths")
        typed._path(path)
        if not (output / path).exists() or (output / path).is_symlink():
            raise ValueError("missing or symbolic native testpath")
    for name in required:
        prefix = name.split("::", 1)[0]
        typed._path(prefix)
    # A gitlink is never a certificate source. Ordinary protected tests must
    # be in exact tracked original regular files, not third-party submodules.
    for item in required:
        prefix = item.split("::", 1)[0]
        if prefix not in regular:
            return {"schema": RECEIPT_SCHEMA,"status":"UNKNOWN_PROTECTED_NOT_EXECUTED",
                    "junit":{"passed":0,"failed":0,"skipped":0,"errors":0},
                    "required":list(required),"executed":[],"deselected":[],
                    "imported_project_files":[],"native_exit":None,
                    "native_calls":0,"stage":verified,
                    "reason":"protected obligation has no directly tracked original regular test source"}
    before_times = _mtimes(output, original)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    env.pop("PYTHONPATH", None)
    env.pop("PYTEST_ADDOPTS", None)
    with tempfile.TemporaryDirectory(prefix="udm-v6-native-receipt-") as temp:
        tmp = Path(temp).resolve()
        env["COVERAGE_FILE"] = str(tmp / ".coverage")
        argv = [str(Path(interpreter).absolute()), "-I","-B","-c",
                _NATIVE_BOOTSTRAP,str(output),str(tmp/"result.json"),
                str(tmp/"junit.xml"),_canonical(list(paths))]
        try:
            process = subprocess.run(argv,cwd=tmp,env=env,capture_output=True,
                                     text=True,timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as error:
            return {"schema":RECEIPT_SCHEMA,"status":"UNKNOWN_NATIVE_TIMEOUT_OR_ENVIRONMENT",
                    "native_calls":1,"reason":type(error).__name__,
                    "junit":{"passed":0,"failed":0,"skipped":0,"errors":0},
                    "required":list(required),"executed":[],"deselected":[],
                    "imported_project_files":[],"native_exit":None}
        changed=False
        try:
            verify_stage(root,commit,output)
            changed = before_times != _mtimes(output,original)
        except ValueError:
            changed=True
        child={}
        if (tmp/"result.json").is_file():
            try:child=json.loads((tmp/"result.json").read_text())
            except (ValueError,UnicodeError):pass
        stdout=process.stdout or ""
        stderr=process.stderr or ""
        receipt={"schema":RECEIPT_SCHEMA, "status":"UNKNOWN_NATIVE_COLLECTION",
                 "source_commit":commit,"typed_manifest_sha256":original["manifest_sha256"],
                 "required":list(required),"selected":child.get("collected",[]),
                 "executed":[x["nodeid"] for x in child.get("calls",[])],
                 "deselected":child.get("deselected",[]),
                 "native_exit":process.returncode,"native_calls":1,
                 "python_interpreter":str(Path(interpreter).absolute()),
                 "pytest_version":child.get("pytest"),
                 "junit":{"passed":sum(x["outcome"]=="passed" for x in child.get("calls",[])),
                          "failed":sum(x["outcome"]=="failed" for x in child.get("calls",[])),
                          "skipped":sum(x["outcome"]=="skipped" for x in child.get("calls",[]))
                                      + len(child.get("setup_skipped",[])),
                          "errors":0},
                 "native_seconds":time.monotonic()-started,
                 "stdout_sha256":_hash(stdout.encode()),"stderr_sha256":_hash(stderr.encode()),
                 "stdout_tail":stdout[-1000:],"stderr_tail":stderr[-1000:],
                 "imported_project_files":[],"stage":verified,
                 "opaque_gitlinks":original["gitlinks"]}
        if changed:
            receipt["status"]="UNKNOWN_SOURCE_MUTATED"
            return receipt
        if not child or child.get("code") != process.returncode:
            receipt["status"]="UNKNOWN_NATIVE_ENVIRONMENT"
            return receipt
        imported=set()
        for row in child.get("imports",[]):
            path=row.get("path")
            if path not in regular or row.get("sha256") != regular[path]["sha256"]:
                receipt["status"]="UNKNOWN_IMPORT_IDENTITY"
                return receipt
            imported.add(path)
        receipt["imported_project_files"]=sorted(imported)
        if not (tmp/"junit.xml").is_file():
            receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
            return receipt
        import xml.etree.ElementTree as ET
        try:
            xml = ET.parse(str(tmp/"junit.xml")).getroot()
            suite = xml if xml.tag=="testsuite" else xml.find("testsuite")
            if suite is None:
                raise ValueError("no native JUnit suite")
            counts = {x: int(suite.attrib.get(x,"0")) for x in ("tests","failures","errors","skipped")}
        except (ET.ParseError,TypeError,ValueError):
            receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
            return receipt
        receipt["junit"]["errors"]=counts["errors"]
        calls=child.get("calls",[])
        nodes=receipt["executed"]
        selected=receipt["selected"]
        deselected=receipt["deselected"]
        if not isinstance(selected,list) or not isinstance(calls,list) or (
                any(node not in selected for node in nodes)):
            receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
            return receipt
        if any(not isinstance(row,dict) or row.get("outcome") not in
               ("passed","failed","skipped") for row in calls):
            receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
            return receipt
        # Collection/import errors are not a mere absent protected test. They
        # prevent establishing any native collection authority in this world.
        if counts["errors"] or process.returncode not in (0, 1):
            receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
            return receipt
        if (any(not any(_prefix_match(node,prefix) for node in nodes) for prefix in required)
                or any(any(_prefix_match(node,prefix) for node in deselected)
                       for prefix in required)
                or not nodes):
            receipt["status"]="UNKNOWN_PROTECTED_NOT_EXECUTED"
            return receipt
        if receipt["junit"]["skipped"] or counts["skipped"]:
            receipt["status"]="UNKNOWN_SKIPPED"
            return receipt
        if (receipt["junit"]["failed"]>0 and process.returncode==1
                and any(any(_prefix_match(row["nodeid"],prefix) for prefix in required)
                        and row.get("outcome")=="failed" for row in calls)):
            receipt["status"]="FAIL_NATIVE_PROTECTED"
            return receipt
        if (process.returncode==0 and child.get("code")==0
                and counts["errors"]==0 and counts["failures"]==0
                and receipt["junit"]["failed"]==0 and len(selected)==len(nodes)
                and all(row["outcome"]=="passed" for row in calls)):
            receipt["status"]="PASS_SCOPED_NATIVE"
            return receipt
        receipt["status"]="UNKNOWN_NATIVE_COLLECTION"
        return receipt
