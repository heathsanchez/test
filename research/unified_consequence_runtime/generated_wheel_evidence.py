"""Immutable generated-wheel provenance for source-pinned native execution.

This is an externally supplied build witness, not a developmental acquisition.
The caller must independently authenticate the build recipe/environment before
passing its wheel to the existing verifier.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .generated_overlay_gate import generated_overlay


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticated_generated_modules(source_files, evidence):
    """Fail closed unless wheel bytes and their exact source binding agree."""
    required = {"schema", "source_commit", "source_tree_sha256",
                "wheel_path", "wheel_sha256", "build_recipe_sha256",
                "build_environment_sha256"}
    if not isinstance(evidence, dict) or set(evidence) != required:
        raise ValueError("UNKNOWN_BUILD_EVIDENCE_SCHEMA")
    if evidence["schema"] != "UDM_AUTHENTICATED_GENERATED_WHEEL_V1":
        raise ValueError("UNKNOWN_BUILD_EVIDENCE_SCHEMA")
    for name in ("source_commit", "source_tree_sha256", "wheel_sha256",
                 "build_recipe_sha256", "build_environment_sha256"):
        value=evidence[name]
        if not isinstance(value,str) or len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
            if name != "source_commit" or not isinstance(value,str) or len(value)!=40 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("UNKNOWN_BUILD_EVIDENCE_IDENTITY")
    wheel=Path(evidence["wheel_path"]).resolve(strict=True)
    return generated_overlay(wheel,source_files,expected_wheel_sha256=evidence["wheel_sha256"])


def evidence_digest(evidence):
    return sha(json.dumps(evidence,sort_keys=True,separators=(",",":")).encode())
