"""V42 data configuration of the retained V41 archive writer and reopen checker."""
from pathlib import Path
import gzip,hashlib,json,os,struct,zlib
REFERENCE=Path('/workspace/udm-v54/research/unified_consequence_runtime/archaeology/native-authority-v41/SCREENING_INDEPENDENT_AUDIT/archive_evidence.py')
OUTPUT=Path('/workspace/qualification/native-authority-v42-screening-archive')
SOURCE_COMMIT='c56d29fae856cceaa0a00000b1c3b782ea1df346'
reference=REFERENCE.read_text()
prefix=reference[:reference.index("archive=A/'native-authority-v41-screening-complete-evidence.tar.gz'")]
prefix=prefix.replace("B=pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit');A=B/'archive';A.mkdir(exist_ok=True)",f"B=pathlib.Path({str(OUTPUT)!r});A=B;A.mkdir(exist_ok=True)")
original_roots="roots={'audit':B,'sealed':pathlib.Path('/workspace/qualification/native-authority-v41-screening-sealed'),'runner':pathlib.Path('/workspace/qualification/native-authority-v41-screening-runner'),'requests':pathlib.Path('/workspace/qualification/native-authority-v41-screening-requests')}"
configured_roots="roots={'sealed':pathlib.Path('/workspace/qualification/native-authority-v42-screening-sealed'),'controller':pathlib.Path('/workspace/qualification/native-authority-v42-screening-controller'),'requests':pathlib.Path('/workspace/qualification/native-authority-v42-screening-requests')}"
assert original_roots in prefix
prefix=prefix.replace(original_roots,configured_roots)
ns={}
exec(compile(prefix,str(REFERENCE)+' [V42 data paths]','exec'),ns)
walk,doc,h=ns['walk'],ns['doc'],ns['h']
items,A=ns['items'],ns['A']
# The V41 walker inventories bytes first; V42 omits only configured duplicate venv
# files from the payload, keeping an exact identity inventory for every omission.
venv_prefix='sealed/case-000/source-environment/native/venv'
venv_rows=[r for r in items if r['archive_path']==venv_prefix or r['archive_path'].startswith(venv_prefix+'/')]
for row in items:
 if row['type']=='file':row['crc32']=f'{zlib.crc32(Path(row["source_path"]).read_bytes())&0xffffffff:08x}'
keep_files={venv_prefix+'/pyvenv.cfg',venv_prefix+'/lib/python3.12/site-packages/chardet/_version.py',venv_prefix+'/lib/python3.12/site-packages/chardet/__pycache__/_version.cpython-312.pyc'}
keep_tree=venv_prefix+'/lib/python3.12/site-packages/chardet-7.4.2.dev1+gea7e547aa.dist-info/'
omitted=[r for r in items if r['archive_path'].startswith(venv_prefix+'/') and r['type']=='file' and r['archive_path'] not in keep_files and not r['archive_path'].startswith(keep_tree)]
omitted_names={r['archive_path'] for r in omitted}
items[:]=[r for r in items if r['archive_path'] not in omitted_names]
receipts=A/'archive-input-receipts';receipts.mkdir(exist_ok=True)
doc(receipts/'CASE000_VENV_FULL_IDENTITY.json',{'schema':'UDM_V42_ARCHIVE_CASE000_VENV_FULL_IDENTITY','source_root':str(Path('/workspace/qualification/native-authority-v42-screening-sealed/case-000/source-environment/native/venv')),'method':'V41 archive walker lstat and exact regular-file SHA256/size/mode/CRC32; symlinks inventoried as raw targets, never followed. This is a post-screening archive identity receipt, not a screening execution.','members':venv_rows,'regular_files':sum(r['type']=='file' for r in venv_rows),'regular_file_bytes':sum(r.get('size',0) for r in venv_rows),'omitted_payload_regular_files':len(omitted),'omitted_payload_regular_file_bytes':sum(r['size'] for r in omitted),'retained_file_paths':sorted(r['archive_path'] for r in venv_rows if r['type']=='file' and r['archive_path'] not in omitted_names),'retained_all_symlink_targets':True})
config_root=Path('/workspace/udm-v54/research/unified_consequence_runtime/archaeology/native-authority-v42')
for name in ['SCREENING_AUTHORITY.json','FROZEN_POOL.json','FRONTIER_PROTOCOL.json','QUALIFIED_GATE.json','UNIVERSE_INFORMATION_BOUNDARY.json','DECLARED_UNIVERSE.json','ACCEPTANCE_PROTOCOL.json','ACCEPTANCE_TEST_FREEZE.json','SUPPLEMENTARY_REVIEW_FREEZE.json','ENVIRONMENT_INTERFACE_FREEZE.json','LEGACY_FIXTURE_PROTOCOL.json','LEGACY_FIXTURE_PROTOCOL_V421.json']:
 walk(config_root/name,'screening-authority/'+name)
for name in ['SUMMARY.json','SUMMARY.txt','archive-source-scope-index-audit.json','git-source-audit.json']:
 walk(Path('/workspace/qualification/native-authority-v42-ci-independent-audit')/name,'qualified-gate-identity/'+name)
for name in ['ARTIFACT_12338856551_AUDIT.json','OBSERVATION_39582982718.json']:
 walk(Path('/workspace/qualification/native-authority-v42-ci-observer')/name,'qualified-gate-identity/'+name)
walk(A/'pre_git_index_snapshot','archive-index-precheck')
walk(receipts,'archive-input-receipts')
walk(REFERENCE,'archive-method/reference-v41-archive_evidence.py')
walk(Path(__file__),'archive-method/archive_evidence_v42.py')
# Complete the CRC32 column for the configured additional evidence.
for row in items:
 if row['type']=='file' and 'crc32' not in row:row['crc32']=f'{zlib.crc32(Path(row["source_path"]).read_bytes())&0xffffffff:08x}'
ns['items']=items
body=reference[reference.index("archive=A/'native-authority-v41-screening-complete-evidence.tar.gz'"):reference.index("owned=json.loads((B/'metadata-preaudit/FULL_SOURCE_IDENTITY.json').read_text())")]
# Only member-list partitioning changes: retain the V41 writer and reopen checker.
partition_prefix='sealed/case-000/source-environment/native/base-build'
groups=[[r for r in items if r['archive_path']==partition_prefix or r['archive_path'].startswith(partition_prefix+'/')],[r for r in items if r['archive_path']!=partition_prefix and not r['archive_path'].startswith(partition_prefix+'/')]]
assert sum(map(len,groups))==len(items)
shards=[]
for index,group in enumerate(groups,1):
 stem=f'native-authority-v42-screening-raw-evidence-{index:03d}-of-{len(groups):03d}'
 configured_body=body.replace('native-authority-v41-screening-complete-evidence',stem).replace('UDM_V41_','UDM_V42_')
 ns['items']=group
 exec(compile(configured_body,str(REFERENCE)+' [V42 evidence data shard]','exec'),ns)
 archive=ns['archive'];verification=ns['verification']
 crc=0;uncompressed_bytes=0
 with gzip.open(archive,'rb') as stream:
  while True:
   chunk=stream.read(1024*1024)
   if not chunk:break
   crc=zlib.crc32(chunk,crc);uncompressed_bytes+=len(chunk)
 with archive.open('rb') as stream:stream.seek(-8,2);footer_crc,footer_size=struct.unpack('<II',stream.read(8))
 assert crc&0xffffffff==footer_crc and uncompressed_bytes&0xffffffff==footer_size
 verification.update(gzip_crc32=f'{footer_crc:08x}',gzip_isize_mod_2_32=footer_size,gzip_uncompressed_bytes=uncompressed_bytes,gzip_full_stream_crc_and_size_verified=True,maximum_blob_size_bytes=90_000_000,below_90MB=archive.stat().st_size<90_000_000,source_commit=SOURCE_COMMIT)
 assert verification['status']=='PASS' and verification['below_90MB']
 verification_path=A/(stem+'.verification.json');doc(verification_path,verification)
 manifest_path=A/(stem+'.manifest.json')
 shards.append({'path':str(archive),'sha256':verification['archive_sha256'],'size_bytes':verification['archive_size_bytes'],'gzip_crc32':verification['gzip_crc32'],'members':len(group),'manifest':{'path':str(manifest_path),'sha256':h(manifest_path.read_bytes()),'size_bytes':manifest_path.stat().st_size},'verification':{'path':str(verification_path),'sha256':h(verification_path.read_bytes()),'size_bytes':verification_path.stat().st_size}})
aggregate={'schema':'UDM_V42_SCREENING_SHARDED_ARCHIVE_MANIFEST','archive_roots':{k:str(v) for k,v in ns['roots'].items()},'members':items,'regular_file_count':sum(r['type']=='file' for r in items),'symlink_count':sum(r['type']=='symlink' for r in items),'directory_count':sum(r['type']=='directory' for r in items),'regular_file_bytes':sum(r.get('size',0) for r in items),'shards':shards,'partition':'Shard 001 contains case000 native/base-build; shard 002 contains every other member. No duplicate or missing member.'}
doc(A/'native-authority-v42-screening-raw-evidence.manifest.json',aggregate)
verification={'schema':'UDM_V42_SCREENING_SHARDED_ARCHIVE_REOPEN_VERIFICATION','status':'PASS','shards':shards,'total_members':len(items),'reopened_regular_files_checked':aggregate['regular_file_count'],'reopened_symlinks_checked':aggregate['symlink_count'],'reopened_directories_checked':aggregate['directory_count'],'failures':[],'method':'Unmodified V41 tar writer and reopen checker, member-list partition data only. Each closed tar.gz reopened; all bytes/SHA256/size/modes/link targets/directories verified without extraction. Separate full gzip drains checked CRC32/ISIZE.','all_shards_below_90MB':True}
doc(A/'native-authority-v42-screening-raw-evidence.verification.json',verification)
gate=Path('/workspace/qualification/native-authority-v42-ci-observer/native-authority-v42-39582982718.zip')
exclusions={'schema':'UDM_V42_SCREENING_RAW_ARCHIVE_EXCLUSIONS','exclusions':[{'path':venv_prefix,'scope':'Only duplicate regular files listed in omitted_regular_files; all directory entries, every original symlink target, pyvenv.cfg, generated chardet/_version.py and its observed pyc, and chardet dist-info retained.','reason':'Do not copy the venv or third-party package copies. Exact full venv identity, all six original frozen runtime inventories, original environment/plugin/package receipts, source build outputs, and original baseline wheel remain retained. No failed generated build output outside the venv is omitted.','identity_receipt':'archive-input-receipts/CASE000_VENV_FULL_IDENTITY.json','omitted_regular_file_count':len(omitted),'omitted_regular_file_bytes':sum(r['size'] for r in omitted),'omitted_regular_files':omitted},{'path':str(gate),'size_bytes':gate.stat().st_size,'sha256':h(gate.read_bytes()),'reason':'Already independently audited qualified gate archive contains SOURCE.tar.gz and qualification raw evidence; do not duplicate its 228MB bytes. Exact gate archive descriptor and independent gate/source audit retained. Screening source commit is separately bound by authority, controller receipts, all raw indexes and independent screening audit; gate source commit is f1779c7443ae6035dee502a201d95d778056c05d.','source_tar_sha256':'dd3c31f1d3b3308c51a4dc721a893e494c663ca04d062237f113e089ee884d63'},{'paths':'External runtime interpreter executables, standard libraries, venv/site-packages and downloaded runtime wheel bytes','reason':'Preexisting binary runtime storage omitted under V41 archive policy. Runtime preparation/download identities, pins, configs, commands and all frozen runtime inventories are retained. Baseline project wheel in case000 native/wheels is included.'},{'path':'/workspace/qualification/native-authority-v42-screening-audit','reason':'Ongoing independent auditor owns this directory. Untouched and excluded from this raw-screening archive; final auditor outputs will accompany a separate archive after authorization.'}],'all_failed_case_artifacts_preserved':True,'all_foreign_git_objects_indexes_symlinks_gitlink_directories_retained':True,'no_foreign_source_or_test_omissions':True,'no_venv_copy':True,'no_runs_retries_repairs_or_source_fetch':True}
doc(A/'native-authority-v42-screening-raw-evidence.exclusions.json',exclusions)
manifest_path=A/'native-authority-v42-screening-raw-evidence.manifest.json'
exclusions_path=A/'native-authority-v42-screening-raw-evidence.exclusions.json'
verification_path=A/'native-authority-v42-screening-raw-evidence.verification.json'
descriptor={'schema':'UDM_V42_SCREENING_RAW_EVIDENCE_ARCHIVE','shards':shards,'total_compressed_bytes':sum(r['size_bytes'] for r in shards),'manifest':{'path':str(manifest_path),'sha256':h(manifest_path.read_bytes()),'size_bytes':manifest_path.stat().st_size},'verification':{'path':str(verification_path),'sha256':h(verification_path.read_bytes()),'size_bytes':verification_path.stat().st_size},'exclusions':{'path':str(exclusions_path),'sha256':h(exclusions_path.read_bytes()),'size_bytes':exclusions_path.stat().st_size},'archive_reference_script':{'path':str(REFERENCE),'sha256':h(REFERENCE.read_bytes())},'data_adapter_script':{'path':str(Path(__file__)),'sha256':h(Path(__file__).read_bytes())},'source_commit':SOURCE_COMMIT,'reopened_and_all_members_verified':True,'all_foreign_symlinks_retained':True,'all_case000_venv_link_targets_retained':True,'all_shards_below_90MB':True,'independent_auditor_archive_separate':True}
doc(A/'native-authority-v42-screening-raw-evidence.descriptor.json',descriptor)
print(json.dumps(descriptor,indent=2))
