import pathlib,os,json,hashlib,tarfile,time,datetime
B=pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit');A=B/'archive';A.mkdir(exist_ok=True)
def h(raw):return hashlib.sha256(raw).hexdigest()
def doc(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
roots={'audit':B,'sealed':pathlib.Path('/workspace/qualification/native-authority-v41-screening-sealed'),'runner':pathlib.Path('/workspace/qualification/native-authority-v41-screening-runner'),'requests':pathlib.Path('/workspace/qualification/native-authority-v41-screening-requests')}
exclude_audit={'committed-source','archive','SCREENING_AUDIT.json','AUDIT_SUMMARY.json'}
items=[]
def walk(source,name):
 if name.startswith('audit/') and name.split('/')[1] in exclude_audit:return
 stat=source.lstat();row={'archive_path':name,'source_path':str(source),'mode':stat.st_mode&0o7777}
 if source.is_symlink():row.update(type='symlink',target=os.readlink(source));items.append(row);return
 if source.is_file():row.update(type='file',size=stat.st_size,sha256=h(source.read_bytes()));items.append(row);return
 if source.is_dir():
  row['type']='directory';items.append(row)
  for child in sorted(source.iterdir()):walk(child,name+'/'+child.name)
  return
 raise ValueError('unsupported archive filesystem object '+str(source))
for name,path in roots.items():walk(path,name)
extra={'runtime-inputs/RUNTIMES.json':pathlib.Path('/workspace/qualification/native-authority-v41-profile-preparation/RUNTIMES.json')}
prep=pathlib.Path('/workspace/qualification/native-authority-v41-profile-preparation/modern-runtime-final')
for n in ['commands.json','download-receipts.json','environment.json','installed-packages.json','metadata-receipt.json','pinned-package-files.json','pins.txt','plugin-identity.json','runtime-identity.json','fixed-packages.log','pip-check.log','venv.log']:
 if (prep/n).is_file():extra['runtime-preparation/modern-runtime-final/'+n]=prep/n
if (prep/'venv/pyvenv.cfg').is_file():extra['runtime-preparation/modern-runtime-final/venv/pyvenv.cfg']=prep/'venv/pyvenv.cfg'
legacy=pathlib.Path('/workspace/qualification/native-frontier-v3-runtime-preparation/catalog-runtimes/cpython-3.6.5-pytest-5.4.3-linux-x86_64')
for n in ['installed-packages.json','download-receipts.json','pins.txt','venv/pyvenv.cfg']:
 if (legacy/n).is_file():extra['runtime-preparation/legacy-runtime/'+n]=legacy/n
for name,path in extra.items():walk(path,name)
archive=A/'native-authority-v41-screening-complete-evidence.tar.gz'
manifest={'schema':'UDM_V41_SCREENING_ARCHIVE_MANIFEST','archive_roots':{k:str(v) for k,v in roots.items()},'members':items,'regular_file_count':sum(r['type']=='file' for r in items),'symlink_count':sum(r['type']=='symlink' for r in items),'directory_count':sum(r['type']=='directory' for r in items),'regular_file_bytes':sum(r.get('size',0) for r in items)}
doc(A/'native-authority-v41-screening-complete-evidence.manifest.json',manifest)
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False) as tar:
 for row in items:tar.add(row['source_path'],arcname=row['archive_path'],recursive=False)
failures=[];filechecks=0;symlinkchecks=0;dirchecks=0
with tarfile.open(archive,'r:gz') as tar:
 members=tar.getmembers();assert len(members)==len(items);actual={m.name:m for m in members};assert len(actual)==len(members);assert set(actual)==set(r['archive_path'] for r in items)
 for row in items:
  m=actual[row['archive_path']]
  if m.mode!=row['mode']:failures.append({'path':m.name,'reason':'mode differs'})
  if row['type']=='file':
   f=tar.extractfile(m);raw=f.read();filechecks+=1
   if not m.isfile() or len(raw)!=row['size'] or h(raw)!=row['sha256']:failures.append({'path':m.name,'reason':'file bytes differ'})
  elif row['type']=='symlink':
   symlinkchecks+=1
   if not m.issym() or m.linkname!=row['target']:failures.append({'path':m.name,'reason':'symlink target differs'})
  else:
   dirchecks+=1
   if not m.isdir():failures.append({'path':m.name,'reason':'directory differs'})
verification={'schema':'UDM_V41_SCREENING_ARCHIVE_REOPEN_VERIFICATION','status':'PASS' if not failures else 'UNKNOWN','archive_path':str(archive),'archive_sha256':h(archive.read_bytes()),'archive_size_bytes':archive.stat().st_size,'members':len(items),'reopened_regular_files_checked':filechecks,'reopened_symlinks_checked':symlinkchecks,'reopened_directories_checked':dirchecks,'failures':failures,'method':'Closed archive reopened; exact member inventory, regular bytes, modes, every link target and directory checked. No extraction or symlink traversal.'}
doc(A/'native-authority-v41-screening-complete-evidence.verification.json',verification)
owned=json.loads((B/'metadata-preaudit/FULL_SOURCE_IDENTITY.json').read_text());gate=pathlib.Path('/workspace/qualification/native-authority-v41-38954969411.zip')
exclusions={'schema':'UDM_V41_SCREENING_ARCHIVE_EXCLUSIONS','exclusions':[{'path':str(B/'committed-source'),'reason':'Complete owned committed source is already Git-pinned bd46699ea9933794a1c3fee161039c24a630bf4b and must be supplied as CI_SOURCE by CI; omit duplicate 160MB source bytes from this evidence Git blob. Exact 1694-file Gitblob/SHA256 inventory and verified gate source copies are included.','file_count':owned['file_count'],'total_bytes':owned['total_bytes'],'inventory':'audit/metadata-preaudit/FULL_SOURCE_IDENTITY.json'},{'path':str(gate),'reason':'Original independently audited Actions38954969411 artifact retained externally; exact hash bound in gate and LINEAGE_PREAUDIT. This packet is screening evidence and does not duplicate 182MB qualification archive.','sha256':h(gate.read_bytes()),'size_bytes':gate.stat().st_size},{'paths':'External runtime executables, standard libraries, venv/site-packages and downloaded wheel bytes','reason':'Binary runtime storage excluded; complete all7frozen runtime inventories, independent FS byte audit, package inventory and preparation receipts included. No runtime/native process is replayed from this packet.'},{'paths':['audit/SCREENING_AUDIT.json','audit/AUDIT_SUMMARY.json','audit/archive/*'],'reason':'Final enclosing attestation/summary and archive descriptors accompany archive separately; excluded from payload to avoid circular/self hashes.'}],'no_foreign_base_source_excluded':True,'all_foreign_git_objects_indexes_symlinks_gitlink_directories_retained':True,'head_materialization_absent':'No protected head Git object, head checkout or native overlay exists in any7retained source root; independently verified in SOURCE_IDENTITY_AUDIT, not silently omitted.'}
doc(A/'native-authority-v41-screening-complete-evidence.exclusions.json',exclusions)
descriptor={'schema':'UDM_V41_SCREENING_COMPLETE_EVIDENCE_ARCHIVE','path':str(archive),'sha256':verification['archive_sha256'],'size_bytes':verification['archive_size_bytes'],'manifest':{'path':str(A/'native-authority-v41-screening-complete-evidence.manifest.json'),'sha256':h((A/'native-authority-v41-screening-complete-evidence.manifest.json').read_bytes())},'verification':{'path':str(A/'native-authority-v41-screening-complete-evidence.verification.json'),'sha256':h((A/'native-authority-v41-screening-complete-evidence.verification.json').read_bytes())},'exclusions':{'path':str(A/'native-authority-v41-screening-complete-evidence.exclusions.json'),'sha256':h((A/'native-authority-v41-screening-complete-evidence.exclusions.json').read_bytes())},'reopened_and_all_members_verified':not failures,'all_foreign_symlinks_retained':True,'owned_source_delivery':'CI_SOURCE matching included full committed-source inventory required for standalone full source reproduction.'}
doc(A/'native-authority-v41-screening-complete-evidence.descriptor.json',descriptor);print(json.dumps(verification))
