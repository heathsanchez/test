"""V5 read-only, content-addressed Git source inventory with typed tree entries.

This is NOT a native execution/admission verifier. In particular, accepting a
Git symlink or a gitlink as a source fact does not authorize importing through
that entry, materializing a submodule, or following an external filesystem path.

The previously qualified regular-file-only verifier remains unmodified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from . import decisive_native_verify as original

SCHEMA = "UDM_TYPED_GIT_SOURCE_INVENTORY_V5"
SOURCE_STATUS = "TYPED_INVENTORY_ONLY"
REGULAR_MODES = frozenset(("100644", "100755"))
GIT_OID = re.compile(r"[0-9a-f]{40}\Z")


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _git(repo, *args):
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0")
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], env=env,
            stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=45,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as error:
        raise ValueError("source Git object unavailable or unauthenticated") from error


def _path(name):
    # Reuse the original verifier's exact bounded repository-path grammar.
    if not isinstance(name, str):
        raise ValueError("non-text Git source path")
    original._path(name)
    return name


def _normal_target(link_path, raw_target):
    """Interpret only POSIX lexical links; NEVER resolve a host filesystem path."""
    try:
        target = raw_target.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, None, "UNKNOWN_LINK_ENCODING"
    if not target or target.startswith("/") or "\x00" in target or "\\" in target:
        return target, None, "UNKNOWN_LINK_ESCAPE"
    parts = list(PurePosixPath(link_path).parent.parts)
    for part in target.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return target, None, "UNKNOWN_LINK_ESCAPE"
            parts.pop()
            continue
        if part in (".", "..") or not part:
            return target, None, "UNKNOWN_LINK_ESCAPE"
        parts.append(part)
    result = "/".join(parts)
    if not result:
        return target, None, "UNKNOWN_LINK_ESCAPE"
    try:
        _path(result)
    except ValueError:
        return target, None, "UNKNOWN_LINK_ESCAPE"
    return target, result, None


def _resolve_symlink(path, regular, links, gitlinks, seen=None):
    """Prove only internal lexical resolution; no filesystem traversal occurs."""
    seen = set() if seen is None else set(seen)
    if path in seen:
        return "UNKNOWN_LINK_CYCLE", None
    if path in regular:
        return "INTERNAL_REGULAR_FILE", path
    if any(path == p or path.startswith(p + "/") for p in gitlinks):
        return "UNKNOWN_GITLINK_TARGET", None
    if path in links:
        seen.add(path)
        _, target, error = _normal_target(path, links[path])
        if error:
            return error, None
        return _resolve_symlink(target, regular, links, gitlinks, seen)
    if any(p.startswith(path + "/") for p in (*regular, *links, *gitlinks)):
        return "UNKNOWN_DIRECTORY_LINK", None
    return "UNKNOWN_DANGLING_LINK", None


def snapshot(repo, commit):
    """Inventory exact committed modes and bytes. Typed identity is not authority."""
    root = Path(repo).absolute()
    if root.resolve() != root or not root.is_dir() or root.is_symlink():
        raise ValueError("source root must be an existing canonical directory")
    if not isinstance(commit, str) or not GIT_OID.fullmatch(commit):
        raise ValueError("exact 40-character source commit required")
    actual = _git(root, "rev-parse", "--verify", commit + "^{commit}").decode().strip()
    if actual != commit:
        raise ValueError("source commit identity mismatch")
    tree = _git(root, "rev-parse", "--verify", commit + "^{tree}").decode().strip()
    if not GIT_OID.fullmatch(tree):
        raise ValueError("wrong Git tree identity")
    rows = _git(root, "ls-tree", "-rz", "--full-tree", commit).split(b"\0")

    manifest, regular, symlink_blobs, gitlinks = [], {}, {}, {}
    seen_paths = set()
    for line in filter(None, rows):
        try:
            meta, name_bytes = line.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split()
            name = _path(name_bytes.decode("utf-8", errors="strict"))
        except (ValueError, UnicodeDecodeError, UnicodeError) as error:
            raise ValueError("invalid original Git tree entry") from error
        if name in seen_paths or not GIT_OID.fullmatch(oid):
            raise ValueError("duplicate or malformed Git tree entry")
        seen_paths.add(name)

        if mode in REGULAR_MODES and kind == "blob":
            raw = _git(root, "cat-file", "blob", oid)
            regular[name] = raw
            manifest.append({"path": name, "mode": mode, "kind": kind,
                             "oid": oid, "sha256": _sha256(raw)})
        elif mode == "120000" and kind == "blob":
            target_bytes = _git(root, "cat-file", "blob", oid)
            symlink_blobs[name] = target_bytes
            manifest.append({"path": name, "mode": mode, "kind": kind,
                             "oid": oid, "sha256": _sha256(target_bytes)})
        elif mode == "160000" and kind == "commit":
            # The referenced commit might not be available in this Git object DB.
            # Neither the source reader nor an importer may materialize it.
            gitlinks[name] = oid
            manifest.append({"path": name, "mode": mode, "kind": kind,
                             "oid": oid})
        else:
            raise ValueError("unknown or unsupported original Git tree entry mode")
    manifest.sort(key=lambda x: x["path"])

    links = []
    for name, target_bytes in sorted(symlink_blobs.items()):
        target, _, initial_error = _normal_target(name, target_bytes)
        resolution, resolved = _resolve_symlink(name, regular, symlink_blobs, gitlinks)
        if initial_error:
            resolution, resolved = initial_error, None
        links.append({
            "path": name, "target": target, "target_sha256": _sha256(target_bytes),
            "resolution": resolution, "resolved_path": resolved,
        })

    opaque_gitlinks = [
        {"path": path, "commit_oid": oid,
         "status": "OPAQUE_NOT_NATIVE_EXECUTION_AUTHORITY"}
        for path, oid in sorted(gitlinks.items())
    ]
    return {
        "schema": SCHEMA,
        "status": SOURCE_STATUS,
        "source_commit": commit,
        "git_tree": tree,
        "manifest": manifest,
        "manifest_sha256": _sha256(_canonical(manifest).encode("utf-8")),
        "counts": {
            "regular": len(regular),
            "symlink": len(symlink_blobs),
            "gitlink": len(gitlinks),
        },
        "links": links,
        "gitlinks": opaque_gitlinks,
        "executable_authority": "NONE",
        "all_original_content_identity_retained": True,
    }
