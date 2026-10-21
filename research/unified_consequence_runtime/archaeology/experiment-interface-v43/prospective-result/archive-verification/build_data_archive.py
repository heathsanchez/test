#!/usr/bin/env python3
"""Local standard-library data archiver; never extracts or executes source bytes."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile

SCHEMA = 'UDM_CONTENT_ADDRESSED_RAW_SCREENING_EVIDENCE_ARCHIVE_V43'
SCOPE = 'NEGATIVE_SCREENING_EVIDENCE_ONLY_NO_G2'
BOUNDARY = ('Data-only lossless content-addressed record of screening and audit evidence. '
            'Unique regular-file bytes are stored under SHA256; original relative paths, '
            'sizes, modes, directories, and exact symlink text are in this manifest. '
            'Original symlinks were never followed. No scientific promotion, learner, agent, or G2.')
CHUNK = 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW


def safe_path(path):
    if not path or path.startswith('/') or any(part in ('', '.', '..') for part in path.split('/')):
        raise ValueError('unsafe relative path: ' + repr(path))


def opened_file(root_fd, relative):
    safe_path(relative)
    parts = relative.split('/')
    fd = os.dup(root_fd)
    try:
        for name in parts[:-1]:
            child = os.open(name, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        file_fd = os.open(parts[-1], FILE_FLAGS, dir_fd=fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            os.close(file_fd)
            raise ValueError('not a regular file: ' + relative)
        return os.fdopen(file_fd, 'rb')
    finally:
        os.close(fd)


def inventory(root):
    files = {}
    objects = {}
    total_bytes = 0
    with _directory(root) as root_fd:
        root_mode = stat.S_IMODE(os.fstat(root_fd).st_mode)
        def scan(fd, parent):
            nonlocal total_bytes
            for name in sorted(os.listdir(fd)):
                relative = parent + '/' + name if parent else name
                safe_path(relative)
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                mode = stat.S_IMODE(info.st_mode)
                if stat.S_ISLNK(info.st_mode):
                    files[relative] = {'kind': 'symlink', 'mode': mode,
                                       'linkname': os.readlink(name, dir_fd=fd)}
                elif stat.S_ISDIR(info.st_mode):
                    files[relative] = {'kind': 'directory', 'mode': mode}
                    child = os.open(name, DIR_FLAGS, dir_fd=fd)
                    try:
                        scan(child, relative)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    digest = hashlib.sha256()
                    size = 0
                    leaf = os.open(name, FILE_FLAGS, dir_fd=fd)
                    with os.fdopen(leaf, 'rb') as stream:
                        before = os.fstat(stream.fileno())
                        if (before.st_dev, before.st_ino, before.st_mode, before.st_size) != (info.st_dev, info.st_ino, info.st_mode, info.st_size):
                            raise ValueError('source changed during inventory: ' + relative)
                        while True:
                            chunk = stream.read(CHUNK)
                            if not chunk:
                                break
                            digest.update(chunk)
                            size += len(chunk)
                        after = os.fstat(stream.fileno())
                        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode):
                            raise ValueError('source changed during read: ' + relative)
                    if size != info.st_size:
                        raise ValueError('source size changed: ' + relative)
                    sha = digest.hexdigest()
                    files[relative] = {'kind': 'file', 'mode': mode, 'bytes': size, 'sha256': sha}
                    total_bytes += size
                    if sha in objects and objects[sha]['bytes'] != size:
                        raise ValueError('inconsistent digest sizes')
                    objects.setdefault(sha, {'bytes': size, 'relative': relative})
                else:
                    raise ValueError('unsupported source entry: ' + relative)
        scan(root_fd, '')
    return root_mode, files, objects, total_bytes


class _directory:
    def __init__(self, path):
        self.path = path
    def __enter__(self):
        self.fd = os.open(self.path, DIR_FLAGS)
        return self.fd
    def __exit__(self, *args):
        os.close(self.fd)


class HashingReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.bytes = 0
    def read(self, size=-1):
        chunk = self.stream.read(size)
        self.digest.update(chunk)
        self.bytes += len(chunk)
        return chunk


def member(name, size):
    result = tarfile.TarInfo(name)
    result.size = size
    result.mode = 0o644
    result.type = tarfile.REGTYPE
    result.uid = result.gid = result.mtime = 0
    result.uname = result.gname = result.linkname = ''
    return result


def digest_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        while True:
            chunk = stream.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build(root, archive, manifest_path, summary_path):
    root = Path(root).absolute()
    archive = Path(archive).absolute()
    manifest_path = Path(manifest_path).absolute()
    summary_path = Path(summary_path).absolute()
    if any(path == root or root in path.parents for path in (archive, manifest_path, summary_path)):
        raise ValueError('archive outputs must be outside source tree')
    if any(path.exists() for path in (archive, manifest_path, summary_path)):
        raise ValueError('refusing to overwrite existing output')
    root_mode, files, objects, total = inventory(root)
    manifest = {'schema': SCHEMA, 'scope': SCOPE, 'boundary': BOUNDARY,
                'source_root': str(root), 'root_mode': root_mode, 'files': files,
                'objects': len(objects), 'regular_bytes': total,
                'unique_object_bytes': sum(value['bytes'] for value in objects.values())}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode('utf-8')
    for path in (archive, manifest_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(archive.name + '.PARTIAL')
    with _directory(root) as root_fd, open(temporary, 'xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=9, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
                tar.addfile(member('MANIFEST.json', len(manifest_bytes)), io.BytesIO(manifest_bytes))
                for sha, entry in sorted(objects.items()):
                    with opened_file(root_fd, entry['relative']) as stream:
                        if stat.S_IMODE(os.fstat(stream.fileno()).st_mode) != files[entry['relative']]['mode']:
                            raise ValueError('source mode changed')
                        reader = HashingReader(stream)
                        tar.addfile(member('objects/' + sha, entry['bytes']), reader)
                        if reader.bytes != entry['bytes'] or reader.digest.hexdigest() != sha or stream.read(1):
                            raise ValueError('source changed while archiving: ' + entry['relative'])
    after_mode, after_files, after_objects, after_total = inventory(root)
    if (root_mode, files, total) != (after_mode, after_files, after_total):
        raise ValueError('source tree changed during archive creation')
    if archive.exists() or manifest_path.exists():
        raise ValueError('output appeared during creation')
    temporary.rename(archive)
    with open(manifest_path, 'xb') as output:
        output.write(manifest_bytes)
    summary = {'archive': str(archive), 'archive_sha256': digest_file(archive),
               'archive_bytes': archive.stat().st_size, 'manifest': str(manifest_path),
               'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
               'manifest_bytes': len(manifest_bytes), 'entries': len(files),
               'kinds': {kind: sum(value['kind'] == kind for value in files.values())
                         for kind in ('file', 'directory', 'symlink')},
               'objects': len(objects), 'regular_bytes': total,
               'unique_object_bytes': manifest['unique_object_bytes'],
               'source_inventory_stable': True, 'independent_readback_verified': False}
    if summary['archive_bytes'] >= 100000000 or len(manifest_bytes) >= 100000000:
        raise ValueError('output exceeds per-file 100 MB limit')
    with open(summary_path, 'x') as output:
        json.dump(summary, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source')
    p.add_argument('archive')
    p.add_argument('manifest')
    p.add_argument('summary')
    a = p.parse_args()
    build(a.source, a.archive, a.manifest, a.summary)
