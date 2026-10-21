"""Generated-module overlay gate derived from 35d79943; no warrant authority.

Installed wheel paths are mapped to an unambiguous tracked flat/src package.
Only supplemental Python modules may be added. Native tests/configuration and
Git-tracked bytes stay authoritative. Arbitrary wheel installation is outside
this deliberately bounded interface.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

class UnknownBuildOverlay(ValueError):pass


def _members(wheel_path):
    files={}
    with zipfile.ZipFile(wheel_path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise UnknownBuildOverlay('duplicate wheel members')
        for info in archive.infolist():
            name=info.filename;path=PurePosixPath(name)
            if (path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name
                    or name.rstrip('/')!=str(path)):
                raise UnknownBuildOverlay('unsafe wheel path')
            mode=info.external_attr>>16
            if stat.S_ISLNK(mode):raise UnknownBuildOverlay('wheel symlink member')
            if name.endswith('/'):continue
            files[name]=archive.read(info)
    return files


def wheel_content_digest(wheel_path):
    """Compare exact member bytes while excluding irrelevant ZIP timestamps."""
    manifest={name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(_members(wheel_path).items())}
    return hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def generated_overlay(wheel_path, tracked_source, *, expected_wheel_sha256, allow_declared_addopts=False):
    """Return generated-only source bytes, after independent build authentication."""
    import fnmatch
    from .decisive_native_verify import _test_patterns
    raw=Path(wheel_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_wheel_sha256:
        raise UnknownBuildOverlay('wheel digest mismatch')
    # Pattern extraction grants no execution authority. The native worker separately
    # validates the exact optional suite authority before allowing declared addopts.
    patterns=_test_patterns(tracked_source,allow_declared_addopts=allow_declared_addopts)
    packages={}
    for name in tracked_source:
        if not name.endswith('/__init__.py'):continue
        source_package=name[:-len('/__init__.py')]
        package=source_package[4:] if source_package.startswith('src/') else source_package
        packages.setdefault(package,[]).append(source_package)
    additions={}
    for name,value in _members(wheel_path).items():
        path=PurePosixPath(name)
        if path.parts[0].endswith('.dist-info'):continue
        if any(part.endswith('.data') for part in path.parts):
            raise UnknownBuildOverlay('unsupported wheel installation scheme')
        roots=[(package,roots) for package,roots in packages.items() if name.startswith(package+'/')]
        if not roots:raise UnknownBuildOverlay('generated module outside tracked package: '+name)
        package,roots=max(roots,key=lambda row:len(row[0]))
        if len(roots)!=1:raise UnknownBuildOverlay('ambiguous flat/src wheel mapping')
        target=roots[0]+name[len(package):]
        candidates=[x for x in (name,'src/'+name) if x in tracked_source]
        if len(candidates)>1:raise UnknownBuildOverlay('ambiguous tracked wheel mapping')
        if target in tracked_source:
            if tracked_source[target]!=value:raise UnknownBuildOverlay('wheel alters Git-tracked source: '+target)
            continue
        if (not target.endswith('.py') or any(part in ('tests','test','.github') for part in PurePosixPath(target).parts)
                or path.name.startswith('test_') or path.name.endswith('_test.py')
                or path.name in ('conftest.py','pytest.py','setup.py')
                or any(fnmatch.fnmatch(path.name,pattern) or fnmatch.fnmatch(target,pattern) for pattern in patterns)):
            raise UnknownBuildOverlay('unapproved generated member: '+target)
        additions[target]=value
    if not additions:raise UnknownBuildOverlay('no generated Python modules')
    return additions
