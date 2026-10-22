"""Source-native packaging observation over the qualified immutable builder.

An original wheel is an observation of its original backend, not a native test
warrant.  Independent verification always builds again.  The process-local
typed result authorizes selection only in this trusted research process;
serialized receipts require a fresh verification before they regain that role.
This is not a reference monitor for hostile trusted-host Python code.
"""
from __future__ import annotations

from contextvars import ContextVar
from email import policy as email_policy
from email.parser import BytesParser
import json
from pathlib import Path
import re
import stat
import time
import zipfile

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from . import decisive_native_verify as source
from . import generic_build_materialization as build
from . import generated_overlay_gate as wheel_gate
from . import generated_wheel_evidence as provenance

EVIDENCE_SCHEMA = 'UDM_SOURCE_NATIVE_METADATA_EVIDENCE_V44'
OBSERVATION_SCHEMA = 'UDM_SOURCE_NATIVE_METADATA_OBSERVATION_V44'
_LOADED_SHA256 = source.sha256(Path(__file__).read_bytes())
_SOURCE_PINS = {
    'generic_build_materialization.py': 'bf08dae2ef55a8a2aac368f5404a6e6c4777ddcc7f581f967a0e0f5c7693b980',
    'generated_wheel_evidence.py': '446515e2257cb0c932759b4e98972a6feefe70a7a65765846e113da488632772',
    'generated_overlay_gate.py': '0628d8067bc46d1e918959ba47b05c95bedfdaa93cff6659e3888cc9670d9c89',
    'decisive_native_verify.py': '12269c8ca2dd586ccec4b162736375bcaac5717aaf07f441b67e5511b0ed4670',
}
_AUTHORITY = object()
_NAME = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z')
_ATTEMPTS = ContextVar('udm_source_native_metadata_build_attempts_v44', default=())


def attempt_snapshot():
    """Process-local actual original backend attempts; nested costs are not additive."""
    rows = json.loads(source.canonical(list(_ATTEMPTS.get())))
    return {'build_calls': sum(row['build_calls'] for row in rows),
            'build_seconds': sum(row['build_seconds'] for row in rows), 'records': rows}


def _original_build(phase, files, output, **kwargs):
    started = time.monotonic()
    try:
        return build.materialize_files(files, output, **kwargs)
    finally:
        attempt_path = Path(output) / 'build-attempt.json'
        attempt = None
        if attempt_path.is_file():
            attempt = json.loads(attempt_path.read_text(), object_pairs_hook=_pairs)
            if (attempt.get('schema') != 'udm.generic-build-attempt.v1'
                    or attempt.get('build_calls') != 1):
                raise ValueError('UNKNOWN_ORIGINAL_METADATA_BUILD_ATTEMPT_RECORD')
        row = {'schema': 'UDM_SOURCE_NATIVE_METADATA_BUILD_ATTEMPT_V44', 'phase': phase,
               'output': str(Path(output).absolute()), 'seconds': time.monotonic() - started,
               'build_calls': 1 if attempt is not None else 0,
               'build_seconds': attempt.get('build_seconds', 0.0) if attempt is not None else 0.0,
               'status': attempt.get('status') if attempt is not None else 'UNKNOWN_BEFORE_NATIVE_BUILD',
               'original_attempt': attempt, 'inclusive_not_additive': True}
        _ATTEMPTS.set((*_ATTEMPTS.get(), row))


def _guard():
    if source.sha256(Path(__file__).read_bytes()) != _LOADED_SHA256:
        raise ValueError('UNKNOWN_METADATA_OBSERVER_SOURCE_CHANGED')
    for module in (source, build, provenance, wheel_gate):
        if source.sha256(Path(module.__file__).read_bytes()) != _SOURCE_PINS[Path(module.__file__).name]:
            raise ValueError('UNKNOWN_METADATA_OBSERVER_DEPENDENCY_CHANGED')


def _pins():
    return dict(_SOURCE_PINS, native_metadata_v44=_LOADED_SHA256)


def _regular(path):
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_file() or path.is_symlink():
        raise ValueError('UNKNOWN_METADATA_ARTIFACT_MISSING_OR_REDIRECTED')
    return path


def _descriptor(path):
    path = _regular(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': source.sha256(raw), 'bytes': len(raw)}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('UNKNOWN_METADATA_DUPLICATE_RECEIPT_FIELD')
        result[key] = value
    return result


def _record(descriptor):
    if not isinstance(descriptor, dict) or set(descriptor) != {'path', 'sha256', 'bytes'}:
        raise ValueError('UNKNOWN_METADATA_RECEIPT_DESCRIPTOR')
    path = _regular(descriptor['path'])
    if _descriptor(path) != descriptor:
        raise ValueError('UNKNOWN_METADATA_RECEIPT_CHANGED')
    return json.loads(path.read_text(), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def _text(value):
    value = str(value)
    if not value or value != value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('UNKNOWN_CORE_METADATA_FIELD')
    return value


def parse_wheel_metadata(wheel):
    """Read one unambiguous regular core-metadata member as data, never code."""
    _guard()
    wheel = _regular(wheel)
    members = wheel_gate._members(wheel)
    with zipfile.ZipFile(wheel) as archive:
        for info in archive.infolist():
            mode = info.external_attr >> 16
            if not info.is_dir() and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError('UNKNOWN_CORE_METADATA_NONREGULAR_WHEEL_MEMBER')
    names = [name for name in members if len(Path(name).parts) == 2
             and Path(name).parts[0].endswith('.dist-info') and Path(name).name == 'METADATA']
    if len(names) != 1:
        raise ValueError('UNKNOWN_CORE_METADATA_MEMBER_COUNT')
    name = names[0]
    prefix = name.split('/')[0]
    if any(part.endswith('.dist-info') and part != prefix
           for member in members for part in member.split('/')):
        raise ValueError('UNKNOWN_CORE_METADATA_MULTIPLE_DISTRIBUTIONS')
    raw = members[name]
    try:
        raw.decode('utf-8')
        if b'\x00' in raw:
            raise ValueError('NUL core metadata')
        parsed = BytesParser(policy=email_policy.default).parsebytes(raw)
        if parsed.defects:
            raise ValueError('malformed core metadata headers')
        for field in ('Metadata-Version', 'Name', 'Version', 'Requires-Python'):
            values = parsed.get_all(field, [])
            if len(values) > 1 or (field != 'Requires-Python' and len(values) != 1):
                raise ValueError('missing or duplicate singleton metadata: ' + field)
        metadata_version = _text(parsed['Metadata-Version'])
        if metadata_version not in ('1.0', '1.1', '1.2', '2.1', '2.2', '2.3', '2.4'):
            raise ValueError('unsupported core metadata version')
        distribution, version = _text(parsed['Name']), _text(parsed['Version'])
        if not _NAME.fullmatch(distribution):
            raise ValueError('invalid distribution name')
        Version(version)
        stem = prefix[:-len('.dist-info')]
        dist_name, separator, dist_version = stem.rpartition('-')
        if (not separator or canonicalize_name(dist_name) != canonicalize_name(distribution)
                or Version(dist_version) != Version(version)):
            raise ValueError('metadata directory differs from distribution identity')
        requires_python = parsed.get('Requires-Python')
        if requires_python is not None:
            requires_python = _text(requires_python)
            SpecifierSet(requires_python)
        requires_dist = [_text(value) for value in parsed.get_all('Requires-Dist', [])]
        for value in requires_dist:
            if Requirement(value).url:
                raise ValueError('direct dependency URL is not frozen package authority')
        extras = [_text(value) for value in parsed.get_all('Provides-Extra', [])]
        if any(not _NAME.fullmatch(value) for value in extras):
            raise ValueError('invalid extra name')
        if len({canonicalize_name(value) for value in extras}) != len(extras):
            raise ValueError('duplicate extra identity')
        classifiers = [_text(value) for value in parsed.get_all('Classifier', [])]
        if len(classifiers) != len(set(classifiers)):
            raise ValueError('duplicate classifier')
        if any(str(value).lower() in ('requires-python', 'requires-dist', 'classifier', 'provides-extra')
               for value in parsed.get_all('Dynamic', [])):
            raise ValueError('wheel environment metadata is still dynamic')
    except (UnicodeError, ValueError, TypeError, AttributeError) as error:
        raise ValueError('UNKNOWN_CORE_METADATA: ' + str(error)) from error
    return {'name': distribution, 'version': version, 'requires_python': requires_python,
            'requires_dist': requires_dist, 'classifiers': classifiers, 'provides_extra': extras}


def _file_digest(files):
    if not isinstance(files, dict) or any(not isinstance(raw, bytes) for raw in files.values()):
        raise ValueError('UNKNOWN_METADATA_SOURCE_FILES')
    return source.fingerprint({name: source.sha256(raw) for name, raw in sorted(files.items())})


def _bindings(repo, commit, interpreter, environment_sha256):
    _guard()
    if not isinstance(environment_sha256, str) or not re.fullmatch('[0-9a-f]{64}', environment_sha256):
        raise ValueError('UNKNOWN_METADATA_ENVIRONMENT_BINDING')
    repo = Path(repo).absolute()
    interpreter = str(Path(interpreter).absolute())
    identity, files, manifest = source._snapshot(repo, commit)
    if 'pyproject.toml' not in files:
        raise ValueError('UNKNOWN_METADATA_BUILD_CONTRACT: original pyproject.toml required')
    environment = source.environment_identity(interpreter)
    if source.fingerprint(environment) != environment_sha256:
        raise ValueError('UNKNOWN_METADATA_ENVIRONMENT_CHANGED')
    value = {'repo_path': str(repo), 'commit': commit, 'source_identity': identity,
             'source_manifest_sha256': source.fingerprint(manifest),
             'source_files_sha256': _file_digest(files), 'interpreter': interpreter,
             'environment_sha256': environment_sha256, 'environment': environment,
             'source_pins': _pins()}
    return value, files, manifest


def _new_output(output):
    path = Path(output).absolute()
    if path.resolve() != path or path.exists() and any(path.iterdir()):
        raise ValueError('new canonical metadata output required')
    return path


def _build_record(report, output):
    path = Path(output) / 'build-receipt.json'
    descriptor = _descriptor(path)
    if _record(descriptor) != report:
        raise ValueError('UNKNOWN_METADATA_BUILD_RECEIPT_NOT_RETAINED')
    return {'report': descriptor, 'generated_wheel_evidence': report['generated_wheel_evidence']}


def _check_build(value, binding, files):
    if not isinstance(value, dict) or set(value) != {'report', 'generated_wheel_evidence'}:
        raise ValueError('UNKNOWN_METADATA_BUILD_RECORD')
    report = _record(value['report'])
    evidence = value['generated_wheel_evidence']
    wheel = provenance.validate_evidence(evidence, source_commit=binding['commit'],
        source_tree_sha256=binding['source_identity']['tracked_tree_sha256'],
        environment_sha256=binding['environment_sha256'])
    if (report.get('schema') != 'udm.generic-build-materialization.v2'
            or report.get('status') != 'BUILT_NOT_SCIENTIFICALLY_VERIFIED'
            or report.get('source_commit') != binding['commit']
            or report.get('source_tree_sha256') != binding['source_identity']['tracked_tree_sha256']
            or report.get('source_pyproject_sha256') != source.sha256(files['pyproject.toml'])
            or report.get('interpreter') != binding['interpreter']
            or report.get('generated_wheel_evidence') != evidence
            or report.get('wheel_filename') != wheel.name
            or report.get('wheel_sha256') != evidence['wheel_sha256']
            or report.get('build', {}).get('returncode') != 0
            or report.get('costs', {}).get('build_calls') != 1):
        raise ValueError('UNKNOWN_METADATA_ORIGINAL_BUILD_RECEIPT_BINDING')
    expected = [binding['interpreter'], *build.BUILD_RECIPE['command']]
    argv = report['build'].get('argv', [])
    if argv[:len(expected)] != expected or len(argv) != len(expected) + 3 or argv[-3] != '--wheel-dir':
        raise ValueError('UNKNOWN_METADATA_ORIGINAL_BUILD_COMMAND')
    if Path(argv[-2]).absolute() != wheel.parent:
        raise ValueError('UNKNOWN_METADATA_WHEEL_OUTPUT_BINDING')
    return parse_wheel_metadata(wheel)


def observe(repo, commit, interpreter, out, *, environment_sha256, timeout=300):
    """Execute the exact original backend once; this is not yet independent evidence."""
    started = time.monotonic()
    binding, files, manifest = _bindings(repo, commit, interpreter, environment_sha256)
    output = _new_output(out)
    report = _original_build('observe', files, output, source_commit=commit,
        source_tree_sha256=binding['source_identity']['tracked_tree_sha256'],
        python=binding['interpreter'], timeout=timeout, environment_sha256=environment_sha256,
        source_manifest=manifest)
    built = _build_record(report, output)
    metadata = _check_build(built, binding, files)
    if _bindings(repo, commit, interpreter, environment_sha256)[0] != binding:
        raise ValueError('UNKNOWN_METADATA_INPUT_CHANGED_DURING_BUILD')
    value = {'schema': EVIDENCE_SCHEMA, 'status': 'OBSERVED_NOT_INDEPENDENTLY_VERIFIED',
             **binding, 'build': built, 'metadata': metadata,
             'costs': dict(report['costs'], total_seconds=time.monotonic() - started)}
    (output / 'metadata-evidence.json').write_text(source.canonical(value) + '\n')
    return value


def _check_evidence(evidence, binding, files):
    if (not isinstance(evidence, dict) or evidence.get('schema') != EVIDENCE_SCHEMA
            or evidence.get('status') != 'OBSERVED_NOT_INDEPENDENTLY_VERIFIED'
            or any(evidence.get(key) != value for key, value in binding.items())):
        raise ValueError('UNKNOWN_METADATA_EVIDENCE_SOURCE_OR_ENVIRONMENT')
    metadata = _check_build(evidence.get('build'), binding, files)
    if evidence.get('metadata') != metadata or evidence.get('costs', {}).get('build_calls') != 1:
        raise ValueError('UNKNOWN_METADATA_EVIDENCE_CONTENT')
    return metadata


class VerifiedObservation(dict):
    """A process-local verified result, not a persisted proof or capability registry."""
    def __init__(self, value, *, _authority=None):
        if _authority is not _AUTHORITY:
            raise ValueError('independent metadata verification required')
        dict.__init__(self, json.loads(source.canonical(value)))
        self._authority = _authority
        self._frozen_digest = source.fingerprint(self)

    def _immutable(self, *args, **kwargs):
        raise TypeError('verified metadata observations are immutable')

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable


def require_verified(observation):
    _guard()
    if (type(observation) is not VerifiedObservation
            or getattr(observation, '_authority', None) is not _AUTHORITY
            or source.fingerprint(observation) != getattr(observation, '_frozen_digest', None)):
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_NOT_INDEPENDENTLY_VERIFIED_IN_PROCESS')
    return observation


def verify(repo, commit, interpreter, evidence, out, *, environment_sha256, timeout=300):
    """Independently rebuild all original wheel bytes before minting selection authority."""
    started = time.monotonic()
    binding, files, manifest = _bindings(repo, commit, interpreter, environment_sha256)
    metadata = _check_evidence(evidence, binding, files)
    output = _new_output(out)
    report = _original_build('verify', files, output, source_commit=commit,
        source_tree_sha256=binding['source_identity']['tracked_tree_sha256'],
        python=binding['interpreter'], timeout=timeout, environment_sha256=environment_sha256,
        source_manifest=manifest)
    independently_built = _build_record(report, output)
    independent_metadata = _check_build(independently_built, binding, files)
    if (independently_built['generated_wheel_evidence']['wheel_content_sha256']
            != evidence['build']['generated_wheel_evidence']['wheel_content_sha256']
            or independent_metadata != metadata):
        raise ValueError('UNKNOWN_METADATA_INDEPENDENT_BUILD_DIFFERS')
    if _bindings(repo, commit, interpreter, environment_sha256)[0] != binding:
        raise ValueError('UNKNOWN_METADATA_INPUT_CHANGED_DURING_VERIFICATION')
    value = {'schema': OBSERVATION_SCHEMA, 'status': 'VERIFIED_SOURCE_NATIVE_METADATA_OBSERVATION',
             **binding, 'metadata': independent_metadata, 'evidence': evidence,
             'independent_build': independently_built,
             'costs': dict(report['costs'], verification_seconds=time.monotonic() - started,
                           total_seconds=time.monotonic() - started)}
    (output / 'verified-metadata-observation.json').write_text(source.canonical(value) + '\n')
    return VerifiedObservation(value, _authority=_AUTHORITY)


def validate_observation(repo, commit, interpreter, observation, *, environment_sha256):
    """Check retained bytes/bindings; this deliberately mints no fresh authority."""
    binding, files, _ = _bindings(repo, commit, interpreter, environment_sha256)
    if (not isinstance(observation, dict) or observation.get('schema') != OBSERVATION_SCHEMA
            or observation.get('status') != 'VERIFIED_SOURCE_NATIVE_METADATA_OBSERVATION'
            or any(observation.get(key) != value for key, value in binding.items())):
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_BINDING')
    metadata = _check_evidence(observation.get('evidence'), binding, files)
    independent = _check_build(observation.get('independent_build'), binding, files)
    if (metadata != independent or observation.get('metadata') != independent
            or observation['independent_build']['generated_wheel_evidence']['wheel_content_sha256']
            != observation['evidence']['build']['generated_wheel_evidence']['wheel_content_sha256']
            or observation.get('costs', {}).get('build_calls') != 1):
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_CONTENT')
    return independent
