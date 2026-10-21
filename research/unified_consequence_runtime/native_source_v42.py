"""Versioned exact-source inventory and bounded native materialization.

The inventory binds original Git objects, including raw link text and opaque
submodule pointers. Only internal file aliases have a readable projection.
Directory aliases and unavailable submodules acquire no execution authority.
The inherited pytest collector, assertion authority and verifier remain separate.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tarfile

from . import decisive_native_verify as original
from . import native_admission_v2 as admission

SCHEMA = 'UDM_TYPED_NATIVE_SOURCE_V42'
PREVIOUS_SHA256 = '12269c8ca2dd586ccec4b162736375bcaac5717aaf07f441b67e5511b0ed4670'
ADMISSION_SHA256 = '4056cb0fd40af3badbe41225919e660d560cac7bb2fda25580399e865778977e'
_LOADED_SHA256 = original.sha256(Path(__file__).read_bytes())
sha256 = original.sha256
fingerprint = original.fingerprint
_BASE = {'path', 'mode', 'blob', 'sha256'}
_LINK = _BASE | {'target', 'resolved_path', 'content_sha256'}
_REGULAR = ('100644', '100755')
_CONFIG_NAMES = {'pytest.ini', '.pytest.ini', 'pyproject.toml', 'setup.cfg', 'tox.ini',
                 'conftest.py', 'setup.py', 'pytest.py'}


class SourceFiles(dict):
    """Convenience projection, not an independent evidence authority.

    Every native context reconstructs this from the immutable commit. Helpers
    also revalidate the complete manifest before trusting these projected bytes.
    """
    def __init__(self, files, manifest, identity=None):
        super().__init__(files)
        self.manifest = copy.deepcopy(manifest)
        self.identity = copy.deepcopy(identity)


def _guard():
    if (sha256(Path(original.__file__).read_bytes()) != PREVIOUS_SHA256
            or sha256(Path(admission.__file__).read_bytes()) != ADMISSION_SHA256
            or sha256(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_TYPED_SOURCE_OPERATION_CHANGED')


def _name(value):
    path = original._path(value)
    if not path.parts or any(part.casefold() == '.git' for part in path.parts):
        raise ValueError('UNKNOWN_TYPED_SOURCE_ADMIN_OR_EMPTY_PATH')
    return path.as_posix()


def _blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def _directories(rows):
    result = {''}
    for name in rows:
        for parent in PurePosixPath(name).parents:
            if str(parent) != '.':
                result.add(parent.as_posix())
    return result


def _resolve_link(name, rows, directories, active=()):
    if name in active:
        raise ValueError('UNKNOWN_TYPED_SOURCE_SYMLINK_CYCLE:' + name)
    target = rows[name]['target']
    if (not isinstance(target, str) or not target or '\x00' in target
            or '\\' in target or target.startswith('/')):
        raise ValueError('UNKNOWN_TYPED_SOURCE_UNSAFE_SYMLINK:' + name)
    parts = list(PurePosixPath(name).parent.parts)
    pending = target.split('/')
    while pending:
        part = pending.pop(0)
        if part in ('', '.'):
            continue
        if part == '..':
            if not parts:
                raise ValueError('UNKNOWN_TYPED_SOURCE_SYMLINK_ESCAPE:' + name)
            parts.pop()
            continue
        if part.casefold() == '.git':
            raise ValueError('UNKNOWN_TYPED_SOURCE_SYMLINK_ADMIN:' + name)
        parts.append(part)
        path = '/'.join(parts)
        if path in rows:
            row = rows[path]
            if row['mode'] == '160000':
                raise ValueError('UNKNOWN_TYPED_SOURCE_SYMLINK_GITLINK:' + name)
            if row['mode'] == '120000':
                resolved = _resolve_link(path, rows, directories, (*active, name))
                if pending:
                    raise ValueError('UNKNOWN_TYPED_SOURCE_DIRECTORY_ALIAS:' + name)
                return resolved
            if pending:
                raise ValueError('UNKNOWN_TYPED_SOURCE_NON_DIRECTORY_PARENT:' + name)
            return path
        if path not in directories:
            raise ValueError('UNKNOWN_TYPED_SOURCE_DANGLING_SYMLINK:' + name)
    raise ValueError('UNKNOWN_TYPED_SOURCE_DIRECTORY_ALIAS:' + name)


def _validate(files, manifest):
    _guard()
    if not isinstance(files, dict) or not isinstance(manifest, (list, tuple)):
        raise ValueError('typed source files and manifest required')
    rows = {}
    for row in manifest:
        if not isinstance(row, dict):
            raise ValueError('invalid typed source entry')
        name = _name(row.get('path'))
        mode = row.get('mode')
        fields = _LINK if mode == '120000' else _BASE
        if (set(row) != fields or name in rows or mode not in (*_REGULAR, '120000', '160000')
                or not isinstance(row.get('blob'), str)
                or not re.fullmatch('[0-9a-f]{40}', row['blob'])):
            raise ValueError('invalid typed source entry fields')
        rows[name] = row
    if list(rows) != sorted(rows):
        raise ValueError('typed source manifest must have canonical path order')
    for name in rows:
        if any(parent.as_posix() in rows for parent in PurePosixPath(name).parents
               if str(parent) != '.'):
            raise ValueError('typed source entry has a non-directory tracked parent')
    if set(files) != {name for name, row in rows.items() if row['mode'] != '160000'}:
        raise ValueError('typed source readable projection differs from inventory')
    directories = _directories(rows)
    for name, row in rows.items():
        if row['mode'] == '160000':
            if row['sha256'] is not None:
                raise ValueError('opaque gitlink has no readable blob authority')
            continue
        raw = files[name]
        if not isinstance(raw, bytes):
            raise ValueError('typed source projection must contain bytes')
        if row['mode'] in _REGULAR:
            if sha256(raw) != row['sha256'] or _blob(raw) != row['blob']:
                raise ValueError('typed source regular blob differs')
        else:
            target = row['target']
            if not isinstance(target, str):
                raise ValueError('typed source link target must be text')
            link = target.encode('utf-8')
            resolved = _resolve_link(name, rows, directories)
            if (sha256(link) != row['sha256'] or _blob(link) != row['blob']
                    or resolved != row['resolved_path']
                    or raw != files[resolved] or sha256(raw) != row['content_sha256']):
                raise ValueError('typed source symlink projection differs')
    return rows


def snapshot(repo, commit):
    """Read raw immutable objects; checkout bytes never provide source authority."""
    _guard()
    root = Path(repo).absolute()
    if root.resolve() != root or not root.is_dir():
        raise ValueError('repository path must be canonical, not a symlink')
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('exact commit required')
    try:
        if original._git(root, 'rev-parse', commit+'^{commit}').decode().strip() != commit:
            raise ValueError('wrong source commit')
        tree = original._git(root, 'rev-parse', commit+'^{tree}').decode().strip()
        manifest, regular, rows = [], {}, {}
        for item in filter(None, original._git(root, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0')):
            meta, raw_name = item.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            name = _name(raw_name.decode('utf-8'))
            if name in rows:
                raise ValueError('duplicate immutable source entry')
            if mode == '160000' and kind == 'commit':
                row = {'path': name, 'mode': mode, 'blob': oid, 'sha256': None}
            elif mode in (*_REGULAR, '120000') and kind == 'blob':
                raw = original._git(root, 'cat-file', 'blob', oid)
                if _blob(raw) != oid:
                    raise ValueError('immutable source blob OID differs')
                row = {'path': name, 'mode': mode, 'blob': oid, 'sha256': sha256(raw)}
                if mode == '120000':
                    row['target'] = raw.decode('utf-8')
                else:
                    regular[name] = raw
            else:
                raise ValueError('UNKNOWN_TYPED_SOURCE_ENTRY_KIND:' + name)
            rows[name] = row
        directories = _directories(rows)
        files = dict(regular)
        for name, row in sorted(rows.items()):
            if row['mode'] == '120000':
                resolved = _resolve_link(name, rows, directories)
                row.update(resolved_path=resolved, content_sha256=sha256(regular[resolved]))
                files[name] = regular[resolved]
            manifest.append(row)
        files = dict(sorted(files.items()))
        _validate(files, manifest)
        identity = {'git_tree': tree, 'tracked_tree_sha256': fingerprint(manifest), 'file_count': len(files)}
        return identity, SourceFiles(files, manifest, identity), manifest
    except subprocess.CalledProcessError as error:
        raise ValueError('wrong or unavailable immutable source commit') from error
    except UnicodeError as error:
        raise ValueError('UNKNOWN_TYPED_SOURCE_NON_UTF8_PATH_OR_LINK') from error


_snapshot = snapshot


def source_identity(repo, commit):
    return snapshot(repo, commit)[0]


def require_executable(manifest):
    _guard()
    for row in manifest:
        if row.get('mode') == '160000':
            raise ValueError('UNKNOWN_UNINITIALIZED_GITLINK:' + str(row.get('path')))


def _canonical_root(root, *, create=False):
    root = Path(root).absolute()
    if root.resolve() != root or root.is_symlink():
        raise ValueError('typed source root must be canonical')
    if not root.exists() and create:
        if root.parent.resolve() != root.parent or not root.parent.is_dir():
            raise ValueError('typed source parent must be canonical')
        root.mkdir()
    if not root.is_dir():
        raise ValueError('typed source root directory required')
    return root


def _parents(root, name):
    parts = PurePosixPath(name).parts[:-1]
    path = root
    for part in parts:
        path = path/part
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError('typed source parent is redirected or non-directory: ' + name)


def _selected(rows, skip_bytecode):
    omitted = {name for name in rows if skip_bytecode and name.endswith(('.pyc', '.pyo'))}
    for name, row in rows.items():
        if row['mode'] != '120000' or name in omitted:
            continue
        current = name
        # The complete graph has already been validated: file-only aliases and
        # no cycles. Retain the intermediate links too, rather than authenticating
        # only a final target that an omitted .pyc alias would make unreachable.
        while rows[current]['mode'] == '120000':
            current = posixpath.normpath(posixpath.join(posixpath.dirname(current), rows[current]['target']))
            if current in omitted:
                raise ValueError('UNKNOWN_TYPED_SOURCE_ALIAS_TO_OMITTED_BYTECODE:' + name)
    return {name: row for name, row in rows.items() if name not in omitted}


def materialize(root, files, manifest, *, tracked_checkout=False, skip_bytecode=False):
    """Restore exact regular blobs and real aliases without following writes.

    A build checkout may contain the known tracked leaves and Git administration;
    no untracked source or redirected directory grants materialization authority.
    """
    rows = _validate(files, manifest)
    require_executable(manifest)
    selected = _selected(rows, skip_bytecode)
    root = _canonical_root(root, create=True)
    if not tracked_checkout and any(root.iterdir()):
        raise ValueError('new empty typed source directory required')
    if tracked_checkout:
        directories = _directories(rows)
        def check(directory):
            for path in directory.iterdir():
                name = path.relative_to(root).as_posix()
                info = path.lstat()
                if name == '.git':
                    if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                        raise ValueError('redirected Git administration')
                    continue
                if name in rows:
                    if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                        raise ValueError('tracked source leaf has invalid filesystem type')
                    continue
                if stat.S_ISDIR(info.st_mode) and name in directories:
                    check(path)
                else:
                    raise ValueError('untracked or redirected checkout content: ' + name)
        check(root)
    # Check every parent before changing any tracked leaf.
    for name in rows:
        _parents(root, name)
    for name in sorted(rows, key=lambda x: (-len(PurePosixPath(x).parts), x)):
        path = root/name
        if os.path.lexists(path):
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                raise ValueError('tracked source leaf is not removable file')
    for name, row in selected.items():
        if row['mode'] not in _REGULAR:
            continue
        path = root/name
        _parents(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(files[name])
        path.chmod(int(row['mode'], 8) & 0o777)
    for name, row in selected.items():
        if row['mode'] == '120000':
            path = root/name
            _parents(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(row['target'])
    validate_materialized(root, files, manifest, strict=True, skip_bytecode=skip_bytecode)
    return root


def validate_materialized(root, files, manifest, candidate=None, *, strict=False, skip_bytecode=False):
    rows = _validate(files, manifest)
    require_executable(manifest)
    selected = _selected(rows, skip_bytecode)
    root = _canonical_root(root)
    replacements = {}
    if candidate is not None:
        validate_candidate(candidate, files, manifest)
        replacements = {row['path']: row['replacement'].encode('utf-8') for row in candidate['replacements']}
    mutations = []
    for name, row in selected.items():
        path = root/name
        try:
            _parents(root, name)
            info = path.lstat()
            if row['mode'] in _REGULAR:
                expected = replacements.get(name, files[name])
                valid = (stat.S_ISREG(info.st_mode)
                    and stat.S_IMODE(info.st_mode) == (int(row['mode'], 8) & 0o777)
                    and path.read_bytes() == expected)
            else:
                expected = replacements.get(row['resolved_path'], files[row['resolved_path']])
                valid = (stat.S_ISLNK(info.st_mode)
                    and os.readlink(path) == row['target']
                    and path.resolve(strict=True) == root/row['resolved_path']
                    and path.read_bytes() == expected)
            if not valid:
                mutations.append(name)
        except (OSError, ValueError, RuntimeError):
            mutations.append(name)
    for name in rows.keys() - selected.keys():
        if os.path.lexists(root/name):
            mutations.append(name)
    mutations = sorted(set(mutations))
    if strict and mutations:
        raise ValueError('typed source topology, mode or bytes differ: ' + ','.join(mutations))
    return mutations


def tracked_archive(files, manifest):
    rows = _validate(files, manifest)
    require_executable(manifest)
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for name, row in rows.items():
            entry = tarfile.TarInfo(name)
            entry.uid = entry.gid = entry.mtime = 0
            entry.uname = entry.gname = ''
            if row['mode'] == '120000':
                entry.type = tarfile.SYMTYPE
                entry.mode = 0o777
                entry.linkname = row['target']
                archive.addfile(entry)
            else:
                entry.mode = int(row['mode'], 8) & 0o777
                entry.size = len(files[name])
                archive.addfile(entry, io.BytesIO(files[name]))
    return gzip.compress(stream.getvalue(), mtime=0)


def safe_overlay(names, manifest, files=None):
    _guard()
    rows = {row['path']: row for row in manifest}
    if files is not None:
        rows = _validate(files, manifest)
    targets = {row['resolved_path'] for row in manifest if row['mode'] == '120000'}
    for name in names:
        name = _name(name)
        if (name in rows and rows[name]['mode'] not in _REGULAR) or name in targets:
            raise ValueError('UNKNOWN_TYPED_SOURCE_REDIRECTED_OVERLAY:' + name)
        if any(parent.as_posix() in rows for parent in PurePosixPath(name).parents if str(parent) != '.'):
            raise ValueError('UNKNOWN_TYPED_SOURCE_OVERLAY_NON_DIRECTORY_PARENT:' + name)
    return True


def validate_overlay_paths(repo, files, manifest, author_tests):
    safe_overlay(author_tests, manifest, files)
    root = _canonical_root(repo)
    for name in author_tests:
        _parents(root, name)
        path = root/name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError('UNKNOWN_TYPED_SOURCE_REDIRECTED_OVERLAY:' + name)
    return True


def validate_candidate(candidate, files, manifest=None):
    if manifest is None:
        manifest = getattr(files, 'manifest', None)
    rows = _validate(files, manifest)
    admission.validate_candidate(candidate, files)
    config = admission.configuration(files)
    protected = set()
    for name, row in rows.items():
        if row['mode'] != '120000':
            continue
        testpaths = config['ini_options'].get('testpaths', [])
        if (PurePosixPath(name).name in _CONFIG_NAMES or admission._test_scope(name, config)
                or any(prefix == '.' or name == prefix.rstrip('/')
                       or name.startswith(prefix.rstrip('/')+'/') for prefix in testpaths)):
            protected.add(row['resolved_path'])
    for replacement in candidate['replacements']:
        name = replacement['path']
        if rows[name]['mode'] not in _REGULAR or name in protected:
            raise ValueError('candidate cannot replace source alias or protected alias target')
    return True
