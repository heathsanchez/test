"""Data-only final-audit roots for retained V41 archive walker/writer/readback."""
from pathlib import Path
import gzip,hashlib,json,struct,zlib
REFERENCE=Path('/workspace/udm-v54/research/unified_consequence_runtime/archaeology/native-authority-v41/SCREENING_INDEPENDENT_AUDIT/archive_evidence.py')
ROOT=Path('/workspace/qualification/native-authority-v42-screening-audit')
OUTPUT=Path('/workspace/qualification/native-authority-v42-final-delivery/auditarchive')
STEM='native-authority-v42-screening-independent-audit'
reference=REFERENCE.read_text()
prefix=reference[:reference.index("extra={'runtime-inputs/RUNTIMES.json':")]
old="B=pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit');A=B/'archive';A.mkdir(exist_ok=True)"
new=f"B=pathlib.Path({str(ROOT)!r});A=pathlib.Path({str(OUTPUT)!r});A.mkdir(exist_ok=True)"
assert old in prefix;prefix=prefix.replace(old,new)
old="roots={'audit':B,'sealed':pathlib.Path('/workspace/qualification/native-authority-v41-screening-sealed'),'runner':pathlib.Path('/workspace/qualification/native-authority-v41-screening-runner'),'requests':pathlib.Path('/workspace/qualification/native-authority-v41-screening-requests')}"
assert old in prefix;prefix=prefix.replace(old,"roots={'audit':B}")
prefix=prefix.replace("exclude_audit={'committed-source','archive','SCREENING_AUDIT.json','AUDIT_SUMMARY.json'}","exclude_audit=set()")
assert hashlib.sha256((ROOT/'AUDIT.json').read_bytes()).hexdigest()=='5dd040cc4af1f8748a3bf85c6d289680786897ba4b1bd26ab0142a193fca980a'
assert hashlib.sha256((ROOT/'SUMMARY.txt').read_bytes()).hexdigest()=='87cf3abea9f221a72e4f4bc46e54d5d48da87126a60eb9dbd8d4f09bfd45791c'
ns={};exec(compile(prefix,str(REFERENCE)+' [final V42 audit data]','exec'),ns)
walk,doc,h=ns['walk'],ns['doc'],ns['h']
walk(REFERENCE,'archive-method/reference-v41-archive_evidence.py')
walk(Path(__file__),'archive-method/archive_final_audit.py')
for row in ns['items']:
 if row['type']=='file':row['crc32']=f'{zlib.crc32(Path(row["source_path"]).read_bytes())&0xffffffff:08x}'
body=reference[reference.index("archive=A/'native-authority-v41-screening-complete-evidence.tar.gz'"):reference.index("owned=json.loads((B/'metadata-preaudit/FULL_SOURCE_IDENTITY.json').read_text())")]
body=body.replace('native-authority-v41-screening-complete-evidence',STEM).replace('UDM_V41_','UDM_V42_')
exec(compile(body,str(REFERENCE)+' [final V42 audit data]','exec'),ns)
archive=ns['archive'];verification=ns['verification']
assert verification['status']=='PASS' and archive.stat().st_size<90_000_000
crc=0;total=0
with gzip.open(archive,'rb') as stream:
 for chunk in iter(lambda:stream.read(1024*1024),b''):crc=zlib.crc32(chunk,crc);total+=len(chunk)
with archive.open('rb') as stream:stream.seek(-8,2);footer_crc,footer_size=struct.unpack('<II',stream.read(8))
assert crc&0xffffffff==footer_crc and total&0xffffffff==footer_size
verification.update(gzip_crc32=f'{footer_crc:08x}',gzip_isize_mod_2_32=footer_size,gzip_full_stream_crc_and_size_verified=True,below_90MB=True)
verification_path=OUTPUT/(STEM+'.verification.json');doc(verification_path,verification)
identity=json.loads((ROOT/'source-identity/SUMMARY.json').read_text())['raw_audit']
exclusions={'schema':'UDM_V42_FINAL_AUDIT_ARCHIVE_EXCLUSIONS','current_audit_root_objects_excluded':[],'all_current_audit_root_files_and_helper_failures_retained':True,'uncompressed_full_source_identity_duplicate':{'uncompressed_size_bytes':identity['uncompressed_bytes'],'uncompressed_sha256':identity['uncompressed_sha256'],'lossless_retained_archive_path':'audit/source-identity/SOURCE_IDENTITY_AUDIT.full.json.gz','compressed_size_bytes':identity['bytes'],'compressed_sha256':identity['sha256'],'roundtrip_descriptor_archive_path':'audit/source-identity/GZIP_ROUNDTRIP.json','current_compact_summary_retained_archive_path':'audit/source-identity/SOURCE_IDENTITY_AUDIT.json','reason':'Auditor already replaced the 742726538-byte duplicate raw JSON with a compact summary while retaining complete original bytes as lossless gzip. This archive includes every current object; the raw JSON is recovered exactly by gzip decompression.'},'raw_screening_inputs':'Separate canonical raw-screening shards retain original source/test/Git/runtime evidence; they are referenced by the included auditor manifests and are not duplicated into this audit packet.','source_snapshot':'Included OWNED_SOURCE_IDENTITY.json binds the complete committed source inventory; qualified-gate source snapshot is retained in the separately bound existing gate archive. No full committed-source directory exists in this final audit root.','no_audit_root_mutations':True,'no_new_git_or_native_or_source_execution':True}
exclusions_path=OUTPUT/(STEM+'.exclusions.json');doc(exclusions_path,exclusions)
manifest_path=OUTPUT/(STEM+'.manifest.json')
def file_descriptor(path):return {'path':str(path),'sha256':h(path.read_bytes()),'size_bytes':path.stat().st_size}
descriptor={'schema':'UDM_V42_FINAL_SCREENING_AUDIT_ARCHIVE','path':str(archive),'sha256':verification['archive_sha256'],'size_bytes':verification['archive_size_bytes'],'gzip_crc32':verification['gzip_crc32'],'manifest':file_descriptor(manifest_path),'verification':file_descriptor(verification_path),'exclusions':file_descriptor(exclusions_path),'archive_reference_script':file_descriptor(REFERENCE),'data_adapter_script':file_descriptor(Path(__file__)),'final_audit_sha256':'5dd040cc4af1f8748a3bf85c6d289680786897ba4b1bd26ab0142a193fca980a','final_summary_sha256':'87cf3abea9f221a72e4f4bc46e54d5d48da87126a60eb9dbd8d4f09bfd45791c','scientific_interval_closed_at_source_commit':'c56d29fae856cceaa0a00000b1c3b782ea1df346','all_current_audit_root_objects_retained':True,'complete_source_identity_losslessly_retained':True,'reopened_all_members_verified':True,'below_90MB':True}
doc(OUTPUT/(STEM+'.descriptor.json'),descriptor)
print(json.dumps(descriptor,indent=2))
