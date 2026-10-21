"""Controlled source-free fixture negatives for independent CAS reader."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tarfile

base = Path('/workspace/qualification/experiment-interface-v43-negative-archive-prep')
spec = importlib.util.spec_from_file_location('independent_cas', base/'independent_verify_cas.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
fixture = base/'FIXTURE_CAS.tar.gz'
manifest_path = base/'FIXTURE_CAS.MANIFEST.json'
manifest_bytes = manifest_path.read_bytes()
raw = gzip.decompress(fixture.read_bytes())
neg = base/'fixture-negative-copies'
neg.mkdir(exist_ok=True)


def zip_raw(data):
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb', filename='', mtime=0) as stream:
        stream.write(data)
    return out.getvalue()


def make_tar(items):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w', format=tarfile.USTAR_FORMAT) as stream:
        for name, data, mode in items:
            item = tarfile.TarInfo(name)
            item.mode = mode
            item.size = len(data)
            item.mtime = 0
            stream.addfile(item, io.BytesIO(data))
    return zip_raw(out.getvalue())


items = []
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as stream:
    for item in stream:
        items.append((item.name, stream.extractfile(item).read(), item.mode))

cases = {}
cases['compressed_trailing_bytes'] = (fixture.read_bytes() + b'X', manifest_bytes, None)
cases['concatenated_gzip_stream'] = (fixture.read_bytes() + zip_raw(b'\0' * 10240), manifest_bytes, None)
cases['nonzero_after_tar_end'] = (zip_raw(raw + b'X' * 512), manifest_bytes, None)
extra = tarfile.TarInfo('objects/' + 'f' * 64)
extra.mode = 0o644
extra.size = 1
extra.mtime = 0
cases['hidden_member_after_tar_end'] = (zip_raw(raw + extra.tobuf(format=tarfile.USTAR_FORMAT) + b'X' + b'\0' * 511 + b'\0' * 1024), manifest_bytes, None)
cases['extra_member_before_tar_end'] = (make_tar(items + [('objects/' + 'f' * 64, b'X', 0o644)]), manifest_bytes, None)
changed_manifest = bytearray(manifest_bytes)
changed_manifest[changed_manifest.index(b'Data') if b'Data' in changed_manifest else 4] ^= 1
cases['external_manifest_corruption'] = (fixture.read_bytes(), bytes(changed_manifest), None)
internal = bytearray(items[0][1])
internal[internal.index(b'boundary') + len(b'boundary') + 4] ^= 1
cases['internal_manifest_corruption'] = (make_tar([(items[0][0], bytes(internal), items[0][2])] + items[1:]), manifest_bytes, None)
object_index = next(i for i, x in enumerate(items) if x[0].startswith('objects/') and x[1])
changed_items = list(items)
name, payload, mode = changed_items[object_index]
payload = bytes([payload[0] ^ 1]) + payload[1:]
changed_items[object_index] = name, payload, mode
cases['object_byte_corruption'] = (make_tar(changed_items), manifest_bytes, None)
changed_items = list(items)
name, payload, mode = changed_items[1]
changed_items[1] = name, payload, 0o755
cases['object_archive_mode_corruption'] = (make_tar(changed_items), manifest_bytes, None)
# Copy only the small artificial fixture, preserving link identities, then alter its bytes.
source_copy = neg/'fixture-source-copy'
if source_copy.exists():
    shutil.rmtree(source_copy)
shutil.copytree(base/'fixture-source', source_copy, symlinks=True)
manifest = json.loads(manifest_bytes)
manifest['source_root'] = str(source_copy)
changed_external = (json.dumps(manifest, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode()
first_regular = next(path for path, entry in manifest['files'].items() if entry['kind'] == 'file')
(source_copy/first_regular).write_bytes(b'changed artificial fixture')
cases['source_byte_mismatch'] = (make_tar([('MANIFEST.json', changed_external, 0o644)] + items[1:]), changed_external, source_copy)

results = {}
for name, (archive_bytes, external_bytes, source) in cases.items():
    archive = neg/(name + '.tar.gz')
    external = neg/(name + '.MANIFEST.json')
    archive.write_bytes(archive_bytes)
    external.write_bytes(external_bytes)
    try:
        v.verify(archive, external, source)
    except Exception as error:
        results[name] = {'rejected': True, 'reason': type(error).__name__ + ': ' + str(error), 'archive_sha256': hashlib.sha256(archive_bytes).hexdigest()}
    else:
        results[name] = {'rejected': False}
require_all = all(value['rejected'] for value in results.values())
verdict = {'status': 'PASS' if require_all else 'FAIL', 'cases': results, 'negative_case_count': len(results), 'native_tests_executed': False, 'archive_data_extracted_or_executed': False, 'original_fixture_mutated': False}
(base/'FIXTURE_INDEPENDENT_REJECTION_CHECKS.json').write_text(json.dumps(verdict, sort_keys=True, indent=2) + '\n')
print(json.dumps(verdict, sort_keys=True, indent=2))
if not require_all:
    raise SystemExit(1)
