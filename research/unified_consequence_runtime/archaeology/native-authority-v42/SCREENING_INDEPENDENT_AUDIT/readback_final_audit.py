"""Distinct streaming manifest reader; never extracts members or follows links."""
from pathlib import Path,PurePosixPath
import gzip,hashlib,json,os,stat,struct,tarfile,zlib
B=Path('/workspace/qualification/native-authority-v42-final-delivery/auditarchive')
STEM='native-authority-v42-screening-independent-audit'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
d=json.loads((B/(STEM+'.descriptor.json')).read_text())
for k in ['manifest','verification','exclusions']:
 v=d[k];p=Path(v['path']);assert sha(p)==v['sha256'] and p.stat().st_size==v['size_bytes']
p=Path(d['path']);assert sha(p)==d['sha256'] and p.stat().st_size==d['size_bytes']
manifest=json.loads(Path(d['manifest']['path']).read_text());expected={r['archive_path']:r for r in manifest['members']};assert len(expected)==len(manifest['members'])
seen=set();files=links=dirs=0;nested=None
with tarfile.open(p,'r|gz') as tar:
 for m in tar:
  name=m.name;pure=PurePosixPath(name)
  assert name and not pure.is_absolute() and '..' not in pure.parts and '\\' not in name and name not in seen
  row=expected[name];assert m.mode==row['mode']
  if row['type']=='file':
   assert m.isfile();raw=tar.extractfile(m).read();assert len(raw)==m.size==row['size'] and hashlib.sha256(raw).hexdigest()==row['sha256'] and f'{zlib.crc32(raw)&0xffffffff:08x}'==row['crc32'];files+=1
   if name=='audit/source-identity/SOURCE_IDENTITY_AUDIT.full.json.gz':
    import io
    h=hashlib.sha256();size=0;crc=0
    with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as stream:
     for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk);size+=len(chunk);crc=zlib.crc32(chunk,crc)
    footer_crc,footer_size=struct.unpack('<II',raw[-8:]);assert footer_crc==crc&0xffffffff and footer_size==size&0xffffffff
    nested={'compressed_sha256':hashlib.sha256(raw).hexdigest(),'compressed_size_bytes':len(raw),'uncompressed_sha256':h.hexdigest(),'uncompressed_size_bytes':size,'gzip_crc32':f'{crc&0xffffffff:08x}','gzip_crc_and_isize_verified':True}
  elif row['type']=='symlink':assert m.issym() and m.linkname==row['target'];links+=1
  else:assert row['type']=='directory' and m.isdir();dirs+=1
  seen.add(name)
assert seen==set(expected)
source_seen=set();source_files=0
for name,root in manifest['archive_roots'].items():
 stack=[(Path(root),name)]
 while stack:
  current,arc=stack.pop();r=expected[arc];s=current.lstat();assert s.st_mode&0o7777==r['mode'];source_seen.add(arc)
  if stat.S_ISLNK(s.st_mode):assert r['type']=='symlink' and os.readlink(current)==r['target']
  elif stat.S_ISDIR(s.st_mode):
   assert r['type']=='directory'
   for child in current.iterdir():stack.append((child,arc+'/'+child.name))
  else:
   raw=current.read_bytes();assert stat.S_ISREG(s.st_mode) and r['type']=='file' and len(raw)==r['size'] and hashlib.sha256(raw).hexdigest()==r['sha256'] and f'{zlib.crc32(raw)&0xffffffff:08x}'==r['crc32'];source_files+=1
assert source_seen=={n for n in expected if n.split('/')[0] in manifest['archive_roots']}
summary=json.loads(Path(manifest['archive_roots']['audit']).joinpath('source-identity/SUMMARY.json').read_text())['raw_audit']
assert nested['compressed_sha256']==summary['sha256'] and nested['compressed_size_bytes']==summary['bytes'] and nested['uncompressed_sha256']==summary['uncompressed_sha256'] and nested['uncompressed_size_bytes']==summary['uncompressed_bytes']
roundtrip=json.loads(Path(manifest['archive_roots']['audit']).joinpath('source-identity/GZIP_ROUNDTRIP.json').read_text());assert nested['uncompressed_sha256']==roundtrip['sha256'] and nested['uncompressed_size_bytes']==roundtrip['gzip_roundtrip_bytes']
crc=0;size=0
with gzip.open(p,'rb') as stream:
 for chunk in iter(lambda:stream.read(1024*1024),b''):crc=zlib.crc32(chunk,crc);size+=len(chunk)
with p.open('rb') as stream:stream.seek(-8,2);footer_crc,footer_size=struct.unpack('<II',stream.read(8))
assert footer_crc==crc&0xffffffff and footer_size==size&0xffffffff and f'{footer_crc:08x}'==d['gzip_crc32']
report={'schema':'UDM_V42_FINAL_AUDIT_SEPARATE_PROCESS_MANIFEST_READBACK','status':'PASS','archive':{'path':str(p),'sha256':sha(p),'size_bytes':p.stat().st_size,'gzip_crc32':d['gzip_crc32']},'descriptor_sha256':sha(B/(STEM+'.descriptor.json')),'manifest_sha256':d['manifest']['sha256'],'all_members_exact_unique':True,'regular_file_sha_size_crc_mode_checks':files,'symlink_target_checks':links,'directory_mode_checks':dirs,'all_current_audit_root_files_checked':source_files,'current_audit_root_objects_excluded':0,'nested_full_source_identity_lossless_roundtrip':nested,'final_audit_sha256_verified':expected['audit/AUDIT.json']['sha256'],'final_summary_sha256_verified':expected['audit/SUMMARY.txt']['sha256'],'gzip_crc_isize_verified':True,'no_extraction_or_link_traversal':True,'no_git_reads_or_index_interval_or_native_source_execution':True,'reader_script_sha256':sha(Path(__file__)),'independence_boundary':'Distinct streaming reader in a separate Python process by the archive actor; original independent scientific auditor outputs are retained verbatim.'}
(B/(STEM+'.independent-readback.json')).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
