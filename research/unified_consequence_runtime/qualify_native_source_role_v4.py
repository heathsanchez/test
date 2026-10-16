"""V4 native smoke qualification: actual isolated pytest execution, not G2.

Runs only independent generated fixtures; no previously exposed source tasks
are replayed and no old verifier is modified. This is weaker than independently
certified generic V3 native admission, and must never be labelled as such.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from . import native_environment_selection_v4 as v4

INVALID = b"if True:\n\tpass\n    pass\n"
META = b'[project]\nrequires-python=">=3.12"\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    result={}
    for path in root.rglob("*"):
        if path.is_file() and not any(x in ("__pycache__", ".pytest_cache", ".git") for x in path.relative_to(root).parts):
            rel=path.relative_to(root).as_posix()
            result[rel]=path.read_bytes()
    return result


def environment_profile():
    return {"schema":"UDM_NATIVE_ENVIRONMENT_CATALOG_V3", "profiles":[{
        "id":"cpython-3.12-pytest-8.4.1","python_version":"3.12.15",
        "python_implementation":"CPython","pytest_version":"8.4.1",
        "packages":["pytest==8.4.1"],"plugins":[]}]}


def invoke(root):
    env=dict(os.environ, PYTHONHASHSEED="0",PYTHONDONTWRITEBYTECODE="1",
             PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    before=snapshot(root)
    tic=time.monotonic()
    proc=subprocess.run([sys.executable,"-B","-m","pytest","-q","-p","no:cacheprovider"],
                        cwd=root,env=env,capture_output=True,text=True,timeout=60)
    after=snapshot(root)
    if after != before:
        raise AssertionError("native pytest changed protected tracked source bytes")
    return {"status":"PASS" if proc.returncode==0 else "FAIL",
            "exit_code":proc.returncode,"wall_seconds":time.monotonic()-tic,
            "stdout_sha256":digest(proc.stdout.encode()),
            "stderr_sha256":digest(proc.stderr.encode()),
            "stdout_tail":proc.stdout[-900:],"stderr_tail":proc.stderr[-900:],
            "protected_tree_sha256":digest(json.dumps(
                {k:digest(v) for k,v in sorted(before.items())},sort_keys=True).encode())}


def execute():
    import pytest
    if pytest.__version__!="8.4.1":
        raise AssertionError("native pytest version not pinned")
    if sys.version_info[:2]!=(3,12):
        raise AssertionError("native interpreter minor not pinned")
    with tempfile.TemporaryDirectory(prefix="udm-v4-native-") as tmp:
        root=Path(tmp)
        (root/"tests/data").mkdir(parents=True)
        (root/"pyproject.toml").write_bytes(META)
        (root/"tests/data/broken.py").write_bytes(INVALID)
        (root/"tests/test_positive.py").write_text("def test_protected():\n    assert 42 == 42\n")

        source=snapshot(root)
        catalog=environment_profile()
        # Actual patch may differ from specified micro patch release; use a
        # runtime-exact profile identity and preserve separate verifiers.
        catalog["profiles"][0]["python_version"]=".".join(map(str,sys.version_info[:3]))
        selected=v4.select_profile(source,catalog)
        if selected["status"]!="CANDIDATE_SOURCE_ENVIRONMENT":
            raise AssertionError("source metadata refused valid fixture data")
        if selected["constraints"]["deferred_python_sources"] != {
                "tests/data/broken.py":digest(INVALID)}:
            raise AssertionError("source role or byte binding absent")
        positive=invoke(root)
        if positive["exit_code"]!=0 or "1 passed" not in positive["stdout_tail"]:
            raise AssertionError("unrelated original native assertion not executed")

        # Dynamic import of the *same* invalid .py must fail natively.
        (root/"tests/test_import.py").write_text(
            "import importlib.util\nfrom pathlib import Path\n"
            "def test_dynamic_import():\n"
            "    path=Path(__file__).parent/'data'/'broken.py'\n"
            "    spec=importlib.util.spec_from_file_location('invalid_fixture',path)\n"
            "    module=importlib.util.module_from_spec(spec)\n"
            "    spec.loader.exec_module(module)\n")
        imported=invoke(root)
        if (imported["exit_code"]!=1 or "broken.py" not in imported["stdout_tail"] or
                not any(name in imported["stdout_tail"] for name in ("TabError","IndentationError"))):
            raise AssertionError("native execution did not expose imported broken fixture: "+json.dumps(imported,sort_keys=True))

        # A collected malformed test cannot inherit fixture-data exemption.
        (root/"tests/test_invalid.py").write_bytes(INVALID)
        refused=v4.select_profile(snapshot(root),catalog)
        if refused["reason"]!="UNKNOWN_SOURCE_PARSER":
            raise AssertionError("malformed collected test escaped conservative selector")
        collected=invoke(root)
        if (collected["exit_code"]==0 or
                not any(name in collected["stdout_tail"] for name in ("TabError","IndentationError"))):
            raise AssertionError("native pytest failed to report broken test collection")

        return {"schema":"UDM_V4_SOURCE_ROLE_NATIVE_SMOKE_V1",
                "scope":"generated-source native pytest control; not generic independent admission",
                "pytest":pytest.__version__,"python":sys.version.split()[0],
                "source_identity_with_invalid_data":selected["constraints"]["source_sha256"],
                "selects_despite_data_fixture":True,
                "positive":positive,"imported":imported,"collected":collected,
                "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN"}


if __name__=="__main__":
    result=execute()
    target=Path("qualification-v4/NATIVE_SMOKE.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"PASS_NATIVE_SMOKE_ONLY",
          "positive_exit":result["positive"]["exit_code"],
          "imported_exit":result["imported"]["exit_code"],
          "collection_exit":result["collected"]["exit_code"],
          "G2":"UNKNOWN"},sort_keys=True))
