"""Separate-process archive readback; reads members without extraction or link traversal."""
from pathlib import Path,PurePosixPath
import gzip,hashlib,json,os,stat,struct,tarfile,zipfile,zlib
B=Path('/workspace/qualification/native-authority-v42-screening-archive')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for c in iter(lambda:stream.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def byte_identity(p):
 h=hashlib.sha256();crc=0;size=0
 with p.open('rb') as stream:
  for c in iter(lambda:stream.read(1024*1024),b''):
   h.update(c);crc=zlib.crc32(c,crc);size+=len(c)
 return size,h.hexdigest(),f'{crc&0xffffffff:08x}'
descriptor=json.loads((B/'native-authority-v42-screening-raw-evidence.descriptor.json').read_text())
for key in ['manifest','verification','exclusions']:
 d=descriptor[key];p=Path(d['path']);assert p.stat().st_size==d['size_bytes'] and digest(p)==d['sha256']
manifest=json.loads(Path(descriptor['manifest']['path']).read_text())
exclusions=json.loads(Path(descriptor['exclusions']['path']).read_text())
expected={r['archive_path']:r for r in manifest['members']};assert len(expected)==len(manifest['members'])
seen=set();filechecks=linkchecks=dirchecks=sourcechecks=member_crc_checks=0;shards=[]
for shard in descriptor['shards']:
 p=Path(shard['path']);assert p.stat().st_size==shard['size_bytes'] and digest(p)==shard['sha256'];assert p.stat().st_size<90_000_000
 subdoc=shard['manifest'];subp=Path(subdoc['path']);assert subp.stat().st_size==subdoc['size_bytes'] and digest(subp)==subdoc['sha256']
 sub=json.loads(subp.read_text());subexpected={r['archive_path']:r for r in sub['members']};actual=set()
 with tarfile.open(p,'r|gz') as tar:
  for member in tar:
   name=member.name;pure=PurePosixPath(name)
   assert name and not pure.is_absolute() and '..' not in pure.parts and '\\' not in name
   assert name not in seen and name not in actual and name in expected and name in subexpected
   row=expected[name];assert row==subexpected[name] and member.mode==row['mode']
   if row['type']=='file':
    assert member.isfile();stream=tar.extractfile(member);sha=hashlib.sha256();crc=0;size=0
    for chunk in iter(lambda:stream.read(1024*1024),b''):
     sha.update(chunk);crc=zlib.crc32(chunk,crc);size+=len(chunk)
    assert size==row['size']==member.size and sha.hexdigest()==row['sha256'] and f'{crc&0xffffffff:08x}'==row['crc32']
    filechecks+=1;member_crc_checks+=1
   elif row['type']=='symlink':assert member.issym() and member.linkname==row['target'];linkchecks+=1
   else:assert row['type']=='directory' and member.isdir();dirchecks+=1
   actual.add(name);seen.add(name)
 assert actual==set(subexpected)
 crc=0;size=0
 with gzip.open(p,'rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):crc=zlib.crc32(chunk,crc);size+=len(chunk)
 with p.open('rb') as stream:stream.seek(-8,2);footer_crc,footer_size=struct.unpack('<II',stream.read(8))
 assert footer_crc==crc&0xffffffff and footer_size==size&0xffffffff and f'{footer_crc:08x}'==shard['gzip_crc32']
 shards.append({'path':str(p),'sha256':digest(p),'size_bytes':p.stat().st_size,'members':len(actual),'gzip_crc32':f'{footer_crc:08x}','gzip_isize_mod_2_32':footer_size})
assert seen==set(expected)
# Compare the complete raw roots, including every specifically omitted venv file.
omitted=exclusions['exclusions'][0]['omitted_regular_files'];omitted_by_name={r['archive_path']:r for r in omitted};assert not set(omitted_by_name)&set(expected)
source_inventory=set()
for name,rootstr in manifest['archive_roots'].items():
 root=Path(rootstr);stack=[(root,name)]
 while stack:
  p,arc=stack.pop();source_inventory.add(arc);row=expected.get(arc,omitted_by_name.get(arc));assert row is not None,arc
  s=p.lstat();assert s.st_mode&0o7777==row['mode']
  if stat.S_ISLNK(s.st_mode):assert row['type']=='symlink' and os.readlink(p)==row['target']
  elif stat.S_ISDIR(s.st_mode):
   assert row['type']=='directory'
   for child in p.iterdir():stack.append((child,arc+'/'+child.name))
  else:
   assert stat.S_ISREG(s.st_mode) and row['type']=='file'
   assert byte_identity(p)==(row['size'],row['sha256'],row['crc32']);sourcechecks+=1
assert source_inventory=={n for n in set(expected)|set(omitted_by_name) if n.split('/')[0] in manifest['archive_roots']}
# Generated source identity: build, original wheel and installed baseline version.
native=Path(manifest['archive_roots']['sealed'])/'case-000/source-environment/native'
built=native/'base-build/src/chardet/_version.py';installed=native/'venv/lib/python3.12/site-packages/chardet/_version.py'
assert built.read_bytes()==installed.read_bytes()
wheel=next((native/'wheels').glob('*.whl'))
with zipfile.ZipFile(wheel) as archive:
 assert archive.testzip() is None
 version=archive.read('chardet/_version.py');assert version==built.read_bytes()
assert not (native/'source/src/chardet/_version.py').exists()
attestation='controller/ORIGINAL_SCREENING_ACTOR_BOUNDARY_ATTESTATION.json';assert expected[attestation]['sha256']=='a50d6887013a773c2b4f2393fa58a3fbfbf8634db585b4215adddb9ce62fbfdd'
# All index identities remain identical; no index restoration is performed.
pre=json.loads((B/'pre_git_index_snapshot/MANIFEST.json').read_text());indexes=[]
for row in pre['index_files']:
 p=Path(row['source']);raw=p.read_bytes();assert len(raw)==row['size'] and hashlib.sha256(raw).hexdigest()==row['sha256'];indexes.append({'source':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'unchanged':True})
for row in pre['roots_index_presence']:assert (Path(row['gitdir'])/'index').is_file()==row['index_present']
report={'schema':'UDM_V42_SCREENING_ARCHIVE_SEPARATE_PROCESS_MANIFEST_READBACK','status':'PASS','reader_script':{'path':str(Path(__file__)),'sha256':digest(Path(__file__))},'descriptor_sha256':digest(B/'native-authority-v42-screening-raw-evidence.descriptor.json'),'aggregate_manifest_sha256':descriptor['manifest']['sha256'],'shards':shards,'exact_unique_inventory':True,'regular_file_byte_size_sha256_crc32_checks':filechecks,'symlink_targets_checked':linkchecks,'directories_modes_checked':dirchecks,'current_source_regular_files_checked_including_omitted_venv_identity':sourcechecks,'omitted_venv_duplicate_file_count':len(omitted),'all_raw_root_objects_exactly_included_or_specifically_omitted':True,'no_archive_extraction_or_link_traversal':True,'gzip_crc_and_isize_verified_for_all_shards':True,'actor_attestation_preserved':expected[attestation],'generated_version':{'size_bytes':built.stat().st_size,'sha256':digest(built),'build_wheel_and_installed_bytes_equal':True,'original_tracked_source_version_absent':True,'original_baseline_wheel_sha256':digest(wheel)},'common_current_all_linked_indexes_unchanged':True,'index_postcheck':indexes,'no_git_mutations_or_source_fetch_or_native_execution':True,'audit_directory_untouched':True,'independence_boundary':'Separate Python process and distinct streaming reader from V41 serializer/checker; same archive-preparation actor, not a separate scientific auditor.'}
(B/'native-authority-v42-screening-raw-evidence.independent-readback.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
