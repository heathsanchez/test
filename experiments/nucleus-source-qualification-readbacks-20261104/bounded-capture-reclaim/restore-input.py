from pathlib import Path
import argparse,json,hashlib,zipfile,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--parts',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();R=a.out;R.mkdir(parents=True,exist_ok=True);start=time.monotonic()
m=json.loads((a.parts/'nucleus-mathlib-source-manifest.json').read_text());assert m['original_archive_sha256']=='3dd3fbb522816bdaa9d9cd2808196e075bfa27e3d6c82648731140594f87ce2b';assert m['decoded_mathlib_sha256']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'
archive=R/'mathlib-original.zip';whole=hashlib.sha256();parts=[]
with archive.open('wb')as out:
 for row in sorted(m['parts'],key=lambda x:x['index']):
  h=hashlib.sha256();size=0
  with(a.parts/row['file']).open('rb')as stream:
   while chunk:=stream.read(1024*1024):h.update(chunk);whole.update(chunk);out.write(chunk);size+=len(chunk)
  assert h.hexdigest()==row['sha256']and size==row['bytes'];parts.append(dict(index=row['index'],sha256=h.hexdigest(),bytes=size));print('Verified input part',row['index'],flush=True)
assert whole.hexdigest()==m['original_archive_sha256']and archive.stat().st_size==m['original_archive_bytes']
compressed=R/'mathlib.ndjson.zst'
with zipfile.ZipFile(archive)as z:
 files=[n for n in z.namelist()if n.endswith('.ndjson.zst')];assert len(files)==1,z.namelist()
 with z.open(files[0])as source,compressed.open('wb')as out:
  while chunk:=source.read(1024*1024):out.write(chunk)
print('Verified original archive, decoding input',flush=True)
source=R/'mathlib.ndjson';h=hashlib.sha256();size=0;records=0
with source.open('wb')as out,(R/'zstd.stderr').open('wb')as err:
 child=subprocess.Popen(['zstd','-dc',str(compressed)],stdout=subprocess.PIPE,stderr=err)
 while chunk:=child.stdout.read(1024*1024):out.write(chunk);h.update(chunk);size+=len(chunk);records+=chunk.count(b'\n')
 assert child.wait()==0
assert size==6184415052 and h.hexdigest()=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'and records==109790519
report=dict(status='VERIFIED_BYTE_IDENTICAL_INPUT_RESTORATION',source_sha256=h.hexdigest(),source_bytes=size,records=records,archive_sha256=whole.hexdigest(),parts=parts,wall=time.monotonic()-start,no_new_kernel_result=True)
(R/'restoration.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
