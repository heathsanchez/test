#!/usr/bin/env python3
"""Metadata-only reconnaissance; absolutely no numeric row values or results read."""
import urllib.request,zipfile,tempfile,pathlib,hashlib,json
url='https://thecellmap.org/costanzo2016/data_files/Raw%20genetic%20interaction%20datasets%3A%20Matrix%20format.zip'
expected='53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f'
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'source.zip'
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'yeast-metadata-only/1.0'}),timeout=120) as src,p.open('wb') as f:
  import shutil;shutil.copyfileobj(src,f)
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 assert h==expected, "ARCHIVE ID MISMATCH"
 rows=[]
 with zipfile.ZipFile(p) as z:
  for info in z.infolist():
   if not info.filename.endswith('.cdt'):continue
   with z.open(info) as f:
    meta=[f.readline().decode('utf-8-sig').rstrip('\r\n').split('\t') for _ in range(6)]
   hdr=meta[0]
   samples=[{'label':line[:8],'prefixes':[s[:12] for s in line[6:15]]} for line in meta[1:]]
   rows.append({'member':info.filename,'bytes':info.file_size,'header_width':len(hdr),
                'header_prefix':hdr[:15],'metadata':samples})
 print('METADATA_ONLY='+json.dumps({'archive_sha256':h,'matrices':rows},sort_keys=True),flush=True)
