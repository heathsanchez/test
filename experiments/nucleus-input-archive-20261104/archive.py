"""Split an existing byte-pinned export archive without regenerating it."""
import hashlib
import json
from pathlib import Path

source=Path('/tmp/mathlib-original.zip')
archive_sha='3dd3fbb522816bdaa9d9cd2808196e075bfa27e3d6c82648731140594f87ce2b'
with source.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==archive_sha
assert source.stat().st_size==1012342513
out=Path('/tmp/nucleus-input-archive');out.mkdir(exist_ok=True)
parts=[];chunk_size=350*1024*1024
with source.open('rb')as f:
    for index in range(1,4):
        p=out/f'mathlib-22c5de8346940895-export.zip.part{index:03d}'
        remaining=chunk_size;sha=hashlib.sha256()
        with p.open('wb')as target:
            while remaining:
                data=f.read(min(4*1024*1024,remaining))
                if not data:break
                target.write(data);sha.update(data);remaining-=len(data)
        parts.append(dict(index=index,file=p.name,bytes=p.stat().st_size,sha256=sha.hexdigest()))
    assert not f.read(1)
assert sum(p['bytes']for p in parts)==source.stat().st_size
manifest=dict(status='BYTE_IDENTICAL_ARCHIVE_PARTS',source_artifact=13231986845,source_run=41636598495,original_archive_bytes=source.stat().st_size,original_archive_sha256=archive_sha,decoded_mathlib_bytes=6184415052,decoded_mathlib_sha256='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6',parts=parts,reassembly='Concatenate parts in index order, verify original archive SHA256, then unzip; decode mathlib.ndjson.zst and verify decoded SHA256.',no_new_export_or_kernel_result=True)
(out/'nucleus-mathlib-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
