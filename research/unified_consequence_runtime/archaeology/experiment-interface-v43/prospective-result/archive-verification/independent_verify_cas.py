"""Independent data-only CAS verification. Never extracts or executes archive data."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tarfile
import zlib

CHUNK = 1024 * 1024
SCHEMA = 'UDM_CONTENT_ADDRESSED_RAW_SCREENING_EVIDENCE_ARCHIVE_V43'
SCOPE = 'NEGATIVE_SCREENING_EVIDENCE_ONLY_NO_G2'
HEX = re.compile(r'[0-9a-f]{64}\Z')
TOP_KEYS = {'schema', 'scope', 'boundary', 'source_root', 'root_mode', 'files', 'objects', 'regular_bytes', 'unique_object_bytes'}


def require(value, message):
    if not value:
        raise ValueError(message)


def strict_json(data):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    return json.loads(data, object_pairs_hook=pairs)


def integer(value):
    return type(value) is int


def safe_relative(path):
    return isinstance(path, str) and bool(path) and not path.startswith('/') and all(piece not in ('', '.', '..') for piece in path.split('/')) and '\x00' not in path


def stat_identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def file_hash(path, dir_fd=None, expected=None):
    h = hashlib.sha256()
    size = 0
    flags = os.O_RDONLY | os.O_NOFOLLOW
    fd = os.open(path, flags, dir_fd=dir_fd)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'hash input is not a regular file')
        if expected is not None:
            require(stat_identity(expected) == stat_identity(before), 'source replaced before file hash')
        while True:
            block = stream.read(CHUNK)
            if not block:
                break
            h.update(block)
            size += len(block)
        after = os.fstat(stream.fileno())
    require(stat_identity(before) == stat_identity(after), 'source changed during hash')
    require(size == before.st_size, 'source size changed during hash')
    return h.hexdigest(), size, stat.S_IMODE(before.st_mode)


def source_inventory(root):
    # Anchor every traversal operation to an open directory. O_NOFOLLOW applies
    # to every child open, so a concurrent directory/link swap cannot redirect it.
    root = Path(root)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(root, flags)
    out = {}
    def descend(directory_fd, prefix):
        directory_before = os.fstat(directory_fd)
        names = sorted(os.listdir(directory_fd), key=os.fsencode)
        for name in names:
            relative = prefix + name
            require(safe_relative(relative), 'unsafe source path')
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISREG(info.st_mode):
                digest, size, read_mode = file_hash(name, dir_fd=directory_fd, expected=info)
                require(mode == read_mode, 'source mode changed during hash')
                out[relative] = {'kind': 'file', 'mode': mode, 'bytes': size, 'sha256': digest}
            elif stat.S_ISDIR(info.st_mode):
                child_fd = os.open(name, flags, dir_fd=directory_fd)
                try:
                    require(stat_identity(info) == stat_identity(os.fstat(child_fd)), 'source directory replaced before traversal')
                    out[relative] = {'kind': 'directory', 'mode': mode}
                    descend(child_fd, relative + '/')
                finally:
                    os.close(child_fd)
            elif stat.S_ISLNK(info.st_mode):
                linkname = os.readlink(name, dir_fd=directory_fd)
                require(stat_identity(info) == stat_identity(os.stat(name, dir_fd=directory_fd, follow_symlinks=False)), 'source link replaced during inventory')
                out[relative] = {'kind': 'symlink', 'mode': mode, 'linkname': linkname}
            else:
                raise ValueError('special source file is forbidden: ' + relative)
        require(names == sorted(os.listdir(directory_fd), key=os.fsencode), 'source directory entries changed during inventory')
        require(stat_identity(directory_before) == stat_identity(os.fstat(directory_fd)), 'source directory changed during inventory')
    try:
        mode = stat.S_IMODE(os.fstat(root_fd).st_mode)
        descend(root_fd, '')
        return mode, out
    finally:
        os.close(root_fd)


def inspect_manifest(data):
    m = strict_json(data)
    require(type(m) is dict and set(m) == TOP_KEYS, 'unexpected manifest shape')
    require(m['schema'] == SCHEMA and m['scope'] == SCOPE, 'schema or scope mismatch')
    require(type(m['boundary']) is str and bool(m['boundary']), 'missing authority boundary')
    require(type(m['source_root']) is str and m['source_root'].startswith('/'), 'source root must be an absolute identity string')
    require(integer(m['root_mode']) and 0 <= m['root_mode'] <= 0o7777, 'invalid root mode')
    require(type(m['files']) is dict, 'files map missing')
    objects = {}
    regular_bytes = 0
    counts = {'file': 0, 'directory': 0, 'symlink': 0}
    for path, item in m['files'].items():
        require(safe_relative(path), 'unsafe manifest path')
        require(type(item) is dict and item.get('kind') in counts, 'invalid manifest entry')
        kind = item['kind']
        require(integer(item.get('mode')) and 0 <= item['mode'] <= 0o7777, 'invalid entry mode')
        counts[kind] += 1
        if kind == 'file':
            require(set(item) == {'kind', 'mode', 'bytes', 'sha256'}, 'unexpected file keys')
            require(integer(item['bytes']) and item['bytes'] >= 0, 'invalid file size')
            require(type(item['sha256']) is str and HEX.fullmatch(item['sha256']), 'invalid object hash')
            digest = item['sha256']
            require(digest not in objects or objects[digest] == item['bytes'], 'conflicting object sizes')
            objects[digest] = item['bytes']
            regular_bytes += item['bytes']
        elif kind == 'directory':
            require(set(item) == {'kind', 'mode'}, 'unexpected directory keys')
        else:
            require(set(item) == {'kind', 'mode', 'linkname'} and type(item['linkname']) is str and '\x00' not in item['linkname'], 'invalid symlink metadata')
        parts = path.split('/')
        for i in range(1, len(parts)):
            parent = '/'.join(parts[:i])
            require(m['files'].get(parent, {}).get('kind') == 'directory', 'missing parent directory or symlink traversal')
    require(integer(m['objects']) and m['objects'] == len(objects), 'object count mismatch')
    require(integer(m['regular_bytes']) and m['regular_bytes'] == regular_bytes, 'regular byte total mismatch')
    require(integer(m['unique_object_bytes']) and m['unique_object_bytes'] == sum(objects.values()), 'unique byte total mismatch')
    return m, objects, counts


def verify_member_metadata(member):
    require(member.type == tarfile.REGTYPE, 'archive contains nonregular member')
    require(member.mode == 0o644, 'archive member mode is not normalized 0644')
    require(member.uid == 0 and member.gid == 0 and member.uname == '' and member.gname == '' and member.mtime == 0, 'archive member identity or time is not normalized')
    require(member.linkname == '' and member.devmajor == 0 and member.devminor == 0 and not member.pax_headers and member.sparse is None, 'archive member carries links, devices, PAX, or sparse data')


def verify_gzip_and_tar_envelope(archive, raw_manifest, objects):
    # Check one complete gzip stream, with no concatenated stream or trailing data.
    with archive.open('rb') as compressed:
        header = compressed.read(10)
        require(len(header) == 10 and header[:4] == b'\x1f\x8b\x08\x00' and header[4:8] == b'\x00' * 4, 'gzip header is not deterministic without optional fields')
        compressed.seek(0)
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        while True:
            block = compressed.read(CHUNK)
            if not block:
                break
            decoder.decompress(block, CHUNK)
            while decoder.unconsumed_tail:
                decoder.decompress(decoder.unconsumed_tail, CHUNK)
            if decoder.eof:
                require(not decoder.unused_data and not compressed.read(1), 'gzip stream has concatenated stream or trailing bytes')
                break
        require(decoder.eof, 'gzip stream is truncated')
    # Do not let tarfile hide blocks after its first terminator or skip invalid data.
    expected = [('MANIFEST.json', len(raw_manifest), hashlib.sha256(raw_manifest).hexdigest())]
    expected.extend(('objects/' + digest, objects[digest], digest) for digest in sorted(objects))
    count = 0
    raw_bytes = 0
    zero_started = False
    with gzip.open(archive, 'rb') as uncompressed:
        while True:
            header = uncompressed.read(512)
            if not header:
                break
            require(len(header) == 512, 'partial raw tar block')
            raw_bytes += 512
            if header == b'\x00' * 512:
                zero_started = True
                # Every remaining byte must be zero, including any hidden header.
                trailing_bytes = 0
                while True:
                    tail = uncompressed.read(CHUNK)
                    if not tail:
                        break
                    trailing_bytes += len(tail)
                    require(not any(tail), 'nonzero bytes after tar end marker')
                raw_bytes += trailing_bytes
                require(trailing_bytes >= 512, 'tar lacks its second zero terminator')
                break
            require(not zero_started and count < len(expected), 'unexpected raw tar header')
            require(header[257:265] == b'ustar\x0000', 'raw tar header is not USTAR')
            member = tarfile.TarInfo.frombuf(header, 'utf-8', 'surrogateescape')
            verify_member_metadata(member)
            name, size, digest = expected[count]
            require(member.name == name and member.size == size, 'raw tar member name/size differs')
            count += 1
            hashed = hashlib.sha256()
            remaining = size
            while remaining:
                payload = uncompressed.read(min(CHUNK, remaining))
                require(bool(payload), 'raw tar payload truncated')
                hashed.update(payload)
                remaining -= len(payload)
                raw_bytes += len(payload)
            require(hashed.hexdigest() == digest, 'raw tar payload hash mismatch')
            pad_size = -size % 512
            padding = uncompressed.read(pad_size)
            require(len(padding) == pad_size and not any(padding), 'raw tar member padding is not zero')
            raw_bytes += len(padding)
    require(zero_started and count == len(expected), 'raw tar missing members or end marker')
    require(raw_bytes % 10240 == 0, 'raw tar is not padded to complete records')
    return raw_bytes


def verify(archive, external, source):
    archive = Path(archive)
    external = Path(external)
    for path in (archive, external):
        s = path.lstat()
        require(stat.S_ISREG(s.st_mode), 'artifact is not a direct regular file')
        require(s.st_size < 100_000_000, 'artifact is not below strict 100 MB limit')
    raw_manifest = external.read_bytes()
    m, expected_objects, counts = inspect_manifest(raw_manifest)
    require(raw_manifest == (json.dumps(m, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode('utf-8'), 'manifest is not canonical JSON')
    raw_tar_bytes = verify_gzip_and_tar_envelope(archive, raw_manifest, expected_objects)
    expected_names = ['MANIFEST.json'] + ['objects/' + digest for digest in sorted(expected_objects)]
    seen = []
    with tarfile.open(archive, mode='r|gz', ignore_zeros=True) as stream:
        for member in stream:
            verify_member_metadata(member)
            require(len(seen) < len(expected_names), 'extra archive member')
            require(member.name == expected_names[len(seen)], 'archive member path/order mismatch')
            seen.append(member.name)
            payload = stream.extractfile(member)
            require(payload is not None, 'member has no regular payload')
            if member.name == 'MANIFEST.json':
                require(member.size == len(raw_manifest), 'manifest member size mismatch')
                require(payload.read() == raw_manifest, 'internal and external manifest bytes differ')
            else:
                digest = member.name.split('/')[1]
                require(member.size == expected_objects[digest], 'object member size mismatch')
                actual = hashlib.sha256()
                size = 0
                while True:
                    block = payload.read(CHUNK)
                    if not block:
                        break
                    actual.update(block)
                    size += len(block)
                require(size == member.size and actual.hexdigest() == digest, 'object member hash mismatch')
    require(seen == expected_names, 'missing archive members')
    source_verified = False
    if source is not None:
        root = Path(source)
        require(str(root) == m['source_root'], 'source identity string differs')
        mode, files = source_inventory(root)
        require(mode == m['root_mode'], 'source root mode mismatch')
        require(files == m['files'], 'source path metadata or byte hash mismatch')
        source_verified = True
    sha, size, mode = file_hash(archive)
    manifest_sha, manifest_size, manifest_mode = file_hash(external)
    return {'status': 'PASS', 'schema': 'UDM_INDEPENDENT_CAS_READBACK_V43', 'archive_path': str(archive), 'archive_sha256': sha, 'archive_bytes': size, 'external_manifest_path': str(external), 'external_manifest_sha256': manifest_sha, 'external_manifest_bytes': manifest_size, 'raw_tar_bytes': raw_tar_bytes, 'single_gzip_stream_no_trailing_bytes': True, 'strict_raw_tar_headers_and_zero_end_verified': True, 'archive_members': len(seen), 'source_entries': len(m['files']), 'source_counts': counts, 'source_regular_bytes': m['regular_bytes'], 'unique_objects': len(expected_objects), 'unique_object_bytes': m['unique_object_bytes'], 'every_member_regular': True, 'every_member_hash_size_mode_verified': True, 'exact_member_inventory_no_extra': True, 'external_manifest_identical': True, 'original_path_map_preserved': True, 'source_lstat_and_bytes_verified': source_verified, 'source_symlinks_never_followed': True, 'archive_data_never_extracted_or_executed': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive')
    parser.add_argument('manifest')
    parser.add_argument('--source')
    parser.add_argument('--output')
    args = parser.parse_args()
    verdict = verify(args.archive, args.manifest, args.source)
    raw = json.dumps(verdict, sort_keys=True, indent=2) + '\n'
    if args.output:
        output = Path(args.output)
        base = Path('/workspace/qualification/experiment-interface-v43-negative-archive-prep')
        require(output.absolute().is_relative_to(base), 'verdict output must remain in prep directory')
        output.write_text(raw)
    print(raw, end='')


if __name__ == '__main__':
    main()
