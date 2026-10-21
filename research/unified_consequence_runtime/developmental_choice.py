"""Source-pinned prospective Pareto choice over an explicit evidence carrier.

This module runs the original ``dominates`` and ``choose`` definitions only.
It does not execute the historical target fixture or experimental entrypoint.
The profile binding proves content consistency, not independent authority,
receipt authenticity, semantic correctness, liveness or future completeness.
Native callers must independently establish those obligations before admission.
"""
from __future__ import annotations

import ast
import builtins
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess


SOURCE_PIN = {
    'repository': 'heathsanchez/test',
    'branch': 'verified-prospective-repair-selection-v1',
    'commit': '6031466188046f56b4660d772d13ad731ed4c0f2',
    'path': 'experiments/verified_prospective_repair_selection_v1/run.py',
    'sha256': 'ef46969e2182a5ced64e3c80f5266c03f864d72dcd8133539e6b1a71c42a4b94',
}


def _source_bytes(source_repo: Path) -> bytes:
    return subprocess.run(
        ['git', '--no-replace-objects', '-C', str(source_repo), 'show',
         SOURCE_PIN['commit'] + ':' + SOURCE_PIN['path']],
        check=True, capture_output=True, timeout=30,
    ).stdout


def native_choice(source_repo: Path) -> dict:
    """Authenticate source on every invocation, including after a prior load."""
    source = _source_bytes(Path(source_repo))
    if hashlib.sha256(source).hexdigest() != SOURCE_PIN['sha256']:
        raise ValueError('original prospective repair source SHA256 mismatch')
    filename = 'git:' + SOURCE_PIN['commit'] + ':' + SOURCE_PIN['path']
    tree = ast.parse(source, filename=filename)
    names = ('dominates', 'choose')
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if tuple(node.name for node in nodes) != names:
        raise ValueError('original prospective repair definitions are missing')
    namespace = {'__builtins__': {name: getattr(builtins, name)
                                  for name in ('all', 'any', 'enumerate', 'len', 'zip')}}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), namespace)
    return {name: namespace[name] for name in names}


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def _validate_profiles(candidates, futures, profiles) -> None:
    for name, carrier in (('candidate', candidates), ('future', futures)):
        if not isinstance(carrier, tuple) or not carrier:
            raise ValueError(name + ' carrier must be a nonempty tuple')
        if any(not isinstance(item, str) or not item.strip() for item in carrier):
            raise ValueError(name + ' identifiers must be nonempty strings')
        if len(set(carrier)) != len(carrier):
            raise ValueError(name + ' identifiers must be unique')
    if not isinstance(profiles, dict) or set(profiles) != set(candidates):
        raise ValueError('profile candidate keys must exactly match the carrier')
    dimension = None
    for candidate in candidates:
        row = profiles[candidate]
        if not isinstance(row, dict) or set(row) != set(futures):
            raise ValueError('profile future keys must exactly match the carrier')
        for future in futures:
            vector = row[future]
            if not isinstance(vector, list) or not vector:
                raise ValueError('every outcome vector must be a nonempty list')
            if dimension is None:
                dimension = len(vector)
            if len(vector) != dimension:
                raise ValueError('all outcome vectors must have equal dimension')
            for value in vector:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError('outcome coordinates must be numeric and not Boolean')
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError('outcome coordinates must be finite')


def profile_binding(candidates: tuple[str], futures: tuple[str], profiles: dict, *, scope: dict) -> dict:
    """Content-bind profiles to exact source/carriers/scope; this is not a warrant.

    The independent native caller should put its source/task identifiers and
    independently checked receipt bindings in ``scope``. This pure helper does
    not authenticate any supplied scope, receipt or claimed verifier.
    """
    _validate_profiles(candidates, futures, profiles)
    if not isinstance(scope, dict) or not scope or any(not isinstance(k, str) for k in scope):
        raise ValueError('a nonempty JSON scope object is required')
    material = {'source': SOURCE_PIN, 'scope': scope,
                'candidates': list(candidates), 'futures': list(futures), 'profiles': profiles}
    digest = hashlib.sha256(_canonical(material)).hexdigest()
    return {'source': deepcopy(SOURCE_PIN), 'scope': deepcopy(scope), 'profiles_sha256': digest}


def choose_verified_profiles(
    source_repo: Path,
    candidates: tuple[str],
    futures: tuple[str],
    profiles: dict[str, dict[str, list[float]]],
    *,
    evidence_binding: dict,
) -> dict:
    """Use original choice over a complete declared finite profile carrier.

    ``AUTHORIZED_REPAIR`` records only the original Pareto algorithm's unique
    choice over well-formed, content-bound profiles. It grants no capability,
    evidence admission or external permission. UNKNOWN never licenses grammar
    expansion, and every result retains the caller's candidate frontier.
    """
    result = {
        'status': 'UNKNOWN_CHOICE',
        'candidates': list(candidates) if isinstance(candidates, (tuple, list)) else [],
        'selected': None,
        'sources': {'prospective_repair_selection': deepcopy(SOURCE_PIN)},
        'independent_authority': 'NOT_ESTABLISHED_BY_THIS_BINDING',
        'grammar_extension_licensed': False,
        'expressivity': 'UNKNOWN',
    }
    try:
        _validate_profiles(candidates, futures, profiles)
    except (TypeError, ValueError) as error:
        return {**result, 'reason': str(error)}
    try:
        native = native_choice(source_repo)
    except (OSError, subprocess.SubprocessError, ValueError, SyntaxError, UnicodeError) as error:
        return {**result, 'status': 'UNKNOWN_SOURCE', 'reason': str(error)}
    try:
        if not isinstance(evidence_binding, dict) or set(evidence_binding) != {
            'source', 'scope', 'profiles_sha256',
        }:
            raise ValueError('exact source, scope and profile digest binding required')
        expected = profile_binding(candidates, futures, profiles, scope=evidence_binding['scope'])
        if evidence_binding != expected:
            raise ValueError('profile evidence source/scope/carrier/content binding mismatch')
    except (TypeError, ValueError, OverflowError) as error:
        return {**result, 'status': 'UNKNOWN_EVIDENCE', 'reason': str(error)}
    ordered = [[profiles[candidate][future] for future in futures] for candidate in candidates]
    winners = native['choose'](ordered)
    if len(winners) != 1:
        return {**result, 'reason': 'declared profiles do not supply a unique Pareto dominator',
                'evidence_binding': deepcopy(expected)}
    return {**result, 'status': 'AUTHORIZED_REPAIR', 'selected': candidates[winners[0]],
            'evidence_binding': deepcopy(expected)}
