"""Typed-source binding of the unchanged native V2 assertion authority.

The extension authenticates source kinds before invoking the original static
configuration, declaration and assertion-delta algorithms. It adds no plugin,
collection, execution-time or external-effect authority.
"""
from pathlib import Path
from types import FunctionType

from . import native_admission_v2 as previous
from . import native_source_v42 as source

SCHEMA = 'UDM_NATIVE_SUITE_AUTHORITY_V42'
CONFIG_SCHEMA = previous.CONFIG_SCHEMA
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
PREVIOUS_SHA256 = '4056cb0fd40af3badbe41225919e660d560cac7bb2fda25580399e865778977e'
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())


def assert_source_identity():
    previous.assert_source_identity()
    if sha256(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256:
        raise ValueError('UNKNOWN_V42_FROZEN_ADMISSION_SOURCE_CHANGED')
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_V42_ADMISSION_SOURCE_CHANGED')
    source._guard()


def _snapshot(repo, commit):
    result = source.snapshot(repo, commit)
    source.require_executable(result[2])
    return result


_namespace = dict(vars(previous), SCHEMA=SCHEMA, _snapshot=_snapshot,
                  assert_source_identity=assert_source_identity)
for _name, _function in vars(previous).items():
    if (isinstance(_function, FunctionType)
            and _function.__module__ == previous.__name__
            and _name != 'assert_source_identity'):
        _bound = FunctionType(_function.__code__, _namespace, _name,
                              _function.__defaults__, _function.__closure__)
        _bound.__kwdefaults__ = _function.__kwdefaults__
        _namespace[_name] = _bound
        globals()[_name] = _bound
_original_derive = _namespace['derive_suite_contract']
_original_candidate = _namespace['validate_candidate']


def derive_suite_contract(repo, base_commit, augmented_commit, protocol_binding, *, repository):
    """Check raw typed deltas, then retain the original assertion derivation."""
    assert_source_identity()
    _, _, before = _snapshot(repo, base_commit)
    _, files, after = _snapshot(repo, augmented_commit)
    old = {row['path']: row for row in before}
    new = {row['path']: row for row in after}
    configuration = _namespace['configuration'](files)
    for name in old.keys() | new.keys():
        if old.get(name) == new.get(name):
            continue
        if (name not in new or new[name]['mode'] not in ('100644', '100755')
                or name in old and old[name]['mode'] not in ('100644', '100755')
                or not _namespace['_test_scope'](name, configuration)):
            raise ValueError('UNKNOWN_TYPED_SOURCE_DELTA: original source kinds or non-test entries changed')
    return _original_derive(repo, base_commit, augmented_commit,
                            protocol_binding, repository=repository)


def validate_candidate(candidate, files):
    """Require the authenticated typed projection before original V2 grammar."""
    assert_source_identity()
    manifest = getattr(files, 'manifest', None)
    if manifest is None:
        raise ValueError('UNKNOWN_TYPED_CANDIDATE_SOURCE: authenticated source manifest required')
    source.validate_candidate(candidate, files, manifest)
    return _original_candidate(candidate, files)


_namespace.update(derive_suite_contract=derive_suite_contract,
                  validate_candidate=validate_candidate)
assert_source_identity()
del _name, _function, _bound
