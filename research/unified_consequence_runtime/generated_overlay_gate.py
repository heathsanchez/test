"""Bounded source-pinned generated-module overlay admission.

This is a pure gate between a separately authenticated wheel build and the
immutable Git source snapshot. It does not execute a verifier or grant a warrant.
"""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
import zipfile


class UnknownBuildOverlay(ValueError):
    pass


def generated_overlay(wheel_path, tracked_source, *, expected_wheel_sha256):
    """Return additional importable Python bytes; never replace Git-tracked bytes.

    tracked_source maps canonical POSIX relative paths to their exact Git bytes.
    Caller must separately bind wheel origin, backend, environment and source.
    """
    from pathlib import Path
    raw = Path(wheel_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_wheel_sha256:
        raise UnknownBuildOverlay("wheel digest mismatch")
    additions = {}
    with zipfile.ZipFile(wheel_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise UnknownBuildOverlay("duplicate wheel members")
        for info in archive.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            path = PurePosixPath(name)
            if (path.is_absolute() or ".." in path.parts or "\\" in name
                    or name != str(path)):
                raise UnknownBuildOverlay("unsafe wheel path")
            if name in tracked_source:
                if archive.read(info) != tracked_source[name]:
                    raise UnknownBuildOverlay("wheel alters Git-tracked source: " + name)
                continue
            if ".dist-info/" in name or ".data/" in name:
                continue
            if (not name.endswith(".py") or name.startswith(("tests/", "test/", ".github/"))
                    or path.name.startswith("test_") or path.name in ("conftest.py", "pytest.py", "setup.py")):
                raise UnknownBuildOverlay("unapproved generated member: " + name)
            additions[name] = archive.read(info)
    if not additions:
        raise UnknownBuildOverlay("no generated Python modules")
    return additions
