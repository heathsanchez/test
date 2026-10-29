"""Thin stdlib-only caller of existing pinned CAS readback; no native replay."""
import argparse,hashlib,importlib.util,json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--set',required=True,type=Path);p.add_argument('--set-sha256',required=True);args=p.parse_args()
raw=args.set.read_bytes()
if args.set.is_symlink()or hashlib.sha256(raw).hexdigest()!=args.set_sha256:raise ValueError('externally pinned archive-set bytes differ')
value=json.loads(raw);unknown={f'G{i}':'UNKNOWN'for i in range(2,7)}
if value['schema']!='REQUEST_V1_COMPLETED_DATA_ARCHIVE_SET'or value['scientific_verdicts']!=unknown:raise ValueError('archive-only scientific scope differs')
source=args.repo/'research/unified_consequence_runtime/archaeology/native-bootstrap-v44/prospective-result/ARCHIVE_ONLY_CHECK.py'
if source.is_symlink()or hashlib.sha256(source.read_bytes()).hexdigest()!='73c24083f15b145dcc28aac8e6cda67b6682f370e879a234ad3c2beedaaaad11':raise ValueError('existing archive readback caller changed')
spec=importlib.util.spec_from_file_location('existing_v44_archive_readback',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
root=args.set.parent;verified=[]
for item in value['archives']:
 files={}
 for role,rec in item['files'].items():files[role]=module.bound(root,rec['name'],{'sha256':rec['sha256'],'bytes':rec['bytes']})
 actual=module.cas_verifier(args.repo).verify(files['archive'],files['manifest'],None)
 retained=module.strict(files['readback'].read_bytes());old=retained['original_verdict'];manifest=module.strict(files['manifest'].read_bytes())
 if retained['status']!='PASS_ARCHIVE_READBACK_ONLY'or retained['verdicts']!=unknown or old['source_lstat_and_bytes_verified']is not True:raise ValueError('original source/readback witness is absent')
 if manifest['source_root']!=item['source_root']:raise ValueError('source scope differs')
 for key in('archive_sha256','archive_bytes','external_manifest_sha256','external_manifest_bytes','source_counts','source_entries','unique_objects','source_regular_bytes','unique_object_bytes'):
  if old[key]!=actual[key]:raise ValueError('fresh archive-only readback differs: '+key)
 verified.append({'prefix':item['prefix'],'archive_sha256':actual['archive_sha256'],'manifest_sha256':actual['external_manifest_sha256'],'status':'PASS_EXISTING_CAS_ARCHIVE_ONLY_READBACK','original_source_lstat_verified':True,'fresh_source_lstat_verified':actual['source_lstat_and_bytes_verified']})
print(json.dumps({'schema':'REQUEST_V1_DATA_ONLY_ARCHIVE_SET_READBACK','status':'PASS_ARCHIVE_INTEGRITY_ONLY_NO_NATIVE_REPLAY','archive_set_sha256':args.set_sha256,'archives':verified,'native_calls':0,'model_calls':0,'new_source_queries':0,'scientific_verdicts':unknown,'boundary':'Fresh archive structure/hash checks only; scientific results and original negative outcomes remain exactly their separately pinned evidence.'},sort_keys=True,indent=2))
