"""Verify an immutable corpus without replaying a newly changed checker."""
from pathlib import Path
import argparse,hashlib,json,collections
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('corpus',type=Path);a=p.parse_args();root=a.corpus;m=json.loads((root/'manifest.json').read_text());assert m['schema']=='nucleus-checked-inputs-v1'and m['status']=='SEALED_CHECKED_INPUT_CORPUS'and m['requires_fresh_new_candidate_execution']
 assert m['entries_count']==len(m['entries'])==388 and m['source_controls']==119 and m['protected_controls']==61 and m['frozen_controls']==208
 assert m['candidate_binary_sha256']=='72ee79b8e1757ff65b06ee37d9321315b9b113f9503cbda635e3ebe1e3b99a41'
 assert m['reference_binary_sha256']=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'
 for name,digest in m['receipt_hashes'].items():assert sha(root/'receipts'/name)==digest
 report=json.loads((root/'receipts/core-conversion-reuse.json').read_text());assert report['qualified']and report['source_qualified']and report['binary_sha']==m['candidate_binary_sha256']
 frozen={r['case']:r for r in json.loads((root/'receipts/frozen208-verdicts.json').read_text())};source_count=0;protected_count=0;frozen_count=0;unique={}
 for entry in m['entries']:
  digest=entry['sha256'];assert len(digest)==64 and all(x in'0123456789abcdef'for x in digest)
  path=root/'inputs'/(digest+'.ndjson');assert path.stat().st_size==entry['bytes']and sha(path)==digest
  assert entry['candidate_binary_sha256']==m['candidate_binary_sha256'];unique[digest]=entry['bytes'];group=entry['group']
  if group.startswith('source119/'):
   source_count+=1;name=group.split('/',1)[1];r=json.loads((root/'receipts'/name).read_text());assert r['reference_binary']==m['reference_binary_sha256']and r['candidate_binary']==m['candidate_binary_sha256']
   matches=[x for x in r['rows']if x['case']==entry['case']and x['sha256']==digest];assert len(matches)==1 and matches[0]['pass_']and entry['metadata']==matches[0]and entry['authority_run']==41947915219
  elif group=='protected61':
   protected_count+=1;row=entry['metadata'];assert row['case']==entry['case']and row['sha256']==digest and row['results']==dict(parent=row['expected_rc'],candidate=row['expected_rc'])and entry['authority_run']==41954263475
   assert row in report['controls']
  elif group=='frozen208':
   frozen_count+=1;row=frozen[entry['case']];assert row['sha256']==digest and entry['metadata']==row and entry['authority_run']==41947915219
  else:raise AssertionError(group)
 registry=json.loads((root/'receipts/input-registry.json').read_text());assert len(registry)==119
 signature=lambda rows:collections.Counter(json.dumps(row,sort_keys=True,separators=(',',':'))for row in rows)
 assert signature([(e['group'],e['case'],e['sha256'])for e in m['entries']if e['group'].startswith('source119/')])==signature([('source119/'+r['group'],r['row']['case'],r['row']['sha256'])for r in registry])
 assert signature([e['metadata']for e in m['entries']if e['group']=='protected61'])==signature(report['controls'])
 assert signature([e['metadata']for e in m['entries']if e['group']=='frozen208'])==signature(list(frozen.values()))
 assert(source_count,protected_count,frozen_count)==(119,61,208)
 assert len(unique)==m['unique_inputs']and sum(unique.values())==m['uncompressed_unique_bytes']
 assert{p.name for p in(root/'inputs').iterdir()}=={x+'.ndjson'for x in unique}
 print(json.dumps(dict(status='VERIFIED_CHECKED_INPUT_CORPUS',manifest_sha256=sha(root/'manifest.json'),entries=388,source_controls=119,protected_controls=61,frozen208=208,unique_inputs=len(unique),raw_bytes=sum(unique.values()),requires_fresh_new_candidate_execution=True,no_rank_claim=True)),flush=True)
if __name__=='__main__':main()
