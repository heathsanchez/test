"""Generated-wheel source authentication, strengthened from 35d79943.

Caller-supplied hashes are bindings, not authority. Every verification performs
an independent PEP517 rebuild from immutable tracked source and compares all
wheel member bytes before permitting a generated-only Python overlay.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .generated_overlay_gate import generated_overlay, wheel_content_digest
from . import generic_build_materialization as build

REQUIRED={'schema','source_commit','source_tree_sha256','wheel_path','wheel_sha256',
          'wheel_content_sha256','build_recipe_sha256','build_environment_sha256','builder_sha256'}


def evidence_digest(evidence):
    # Location is transport metadata; exact artifact/source/recipe bytes are authority inputs.
    return hashlib.sha256(json.dumps({k:v for k,v in evidence.items() if k!='wheel_path'},
        sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_evidence(evidence, *, source_commit, source_tree_sha256, environment_sha256):
    if not isinstance(evidence,dict) or set(evidence)!=REQUIRED or evidence['schema']!=build.SCHEMA:
        raise ValueError('UNKNOWN_BUILD_EVIDENCE_SCHEMA')
    for name in REQUIRED-{'schema','wheel_path'}:
        if not isinstance(evidence[name],str) or not re.fullmatch('[0-9a-f]{'+('40' if name=='source_commit' else '64')+'}',evidence[name]):
            raise ValueError('UNKNOWN_BUILD_EVIDENCE_IDENTITY')
    if (evidence['source_commit']!=source_commit or evidence['source_tree_sha256']!=source_tree_sha256
            or evidence['build_environment_sha256']!=environment_sha256
            or evidence['build_recipe_sha256']!=build.recipe_digest()
            or evidence['builder_sha256']!=build.sha256(build.__file__)):
        raise ValueError('build evidence source, recipe or environment mismatch')
    wheel=Path(evidence['wheel_path']).absolute()
    if wheel.resolve()!=wheel or not wheel.is_file() or not wheel.name.endswith('.whl'):
        raise ValueError('build wheel artifact missing or redirected')
    if build.sha256(wheel)!=evidence['wheel_sha256'] or wheel_content_digest(wheel)!=evidence['wheel_content_sha256']:
        raise ValueError('build wheel artifact content mismatch')
    return wheel


def authenticated_generated_modules(source_files, evidence, *, source_commit,
                                    source_tree_sha256, interpreter, environment_sha256,
                                    output_dir, source_manifest=(), allow_declared_addopts=False):
    """Rebuild and compare, never accept a supplied wheel based on its digest alone."""
    wheel=validate_evidence(evidence,source_commit=source_commit,
        source_tree_sha256=source_tree_sha256,environment_sha256=environment_sha256)
    actual=build.materialize_files(source_files,output_dir,source_commit=source_commit,
        source_tree_sha256=source_tree_sha256,python=interpreter,environment_sha256=environment_sha256,
        source_manifest=source_manifest)
    if actual['generated_wheel_evidence']['wheel_content_sha256']!=evidence['wheel_content_sha256']:
        raise ValueError('independent build differs from retained wheel artifact')
    additions=generated_overlay(wheel,source_files,expected_wheel_sha256=evidence['wheel_sha256'],
        allow_declared_addopts=allow_declared_addopts)
    return additions,actual
