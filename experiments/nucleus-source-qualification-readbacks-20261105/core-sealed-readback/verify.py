from pathlib import Path
import argparse,hashlib,json,statistics,sys,math,shutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
from resume import verify,sha,CANDIDATE,PARENT,HOT,FRONTIER,REFERENCE,COMPONENT
p=argparse.ArgumentParser();p.add_argument('--completion-zip',type=Path,required=True);p.add_argument('--completion',type=Path,required=True);p.add_argument('--source-zip',type=Path,required=True);p.add_argument('--parent-zip',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--oracle',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False)
assert sha(a.completion_zip)=='0167b15caae9b474ae0d6540466ec68ef6fac2786b3eb263554d5e94c055adbb'
q,old,own,base,full=verify(a.completion,a.parent,a.out,a.source_zip,a.parent_zip)
report=json.loads((a.completion/'core-conversion-reuse.json').read_text());assert report['status']=='PROMOTABLE_CORE_CONVERSION_REUSE'and report['qualified']and report['source_qualified']and report['fresh_protected_replay'];assert report['binary_sha']==CANDIDATE and report['parent_binary']==PARENT
assert sha(a.completion/'candidate/nucleus')==CANDIDATE
controls=report['controls'];assert len(controls)==61
for row in controls:
 assert row['results']==dict(candidate=row['expected_rc'],parent=row['expected_rc'])
 if row['prior_recorded_input_hash']is not None:assert row['prior_recorded_input_hash']==row['sha256']
 source=own/row['source_path']if not row['source_path'].startswith('original-frontier-prefix/')else a.completion/'protected-prefixes'/(row['sha256']+'.ndjson')
 assert sha(source)==row['sha256']
assert sum(row['prior_recorded_input_hash']is None for row in controls)==17
assert sha(a.completion/'hot.ndjson')==HOT and(a.completion/'hot.ndjson').stat().st_size==11654159
oracle=json.loads(a.oracle.read_text());assert oracle['status']=='VERIFIED_REFERENCE_ACCEPT'and oracle['reference_binary_sha256']==REFERENCE and oracle['input_sha256']==HOT and oracle['input_bytes']==11654159 and oracle['parse_rc']==oracle['kernel_rc']==0
assert len(oracle['rows'])==2 and all(r['rc']==0 for r in oracle['rows'])
prior_full=json.loads((a.parent/'full.json').read_text());assert prior_full['frontier_official_reference']==dict(binary_sha=REFERENCE,parse_rc=0,rc=0,source_sha=FRONTIER)
rows=report['timing']['rows'];assert len(rows)==4 and[r['arm']for r in rows]==['candidate','parent','parent','candidate']
for row in rows:
 assert row['rc']==0 and not row['stderr']and row['input_sha256']==HOT
 assert row['binary_sha256']==(CANDIDATE if row['arm']=='candidate'else PARENT)
 assert math.isclose(row['cpu'],row['user']+row['system'],abs_tol=1e-9)
b=[r['cpu']for r in rows if r['arm']=='candidate'];c=[r['cpu']for r in rows if r['arm']=='parent'];br=[r['rss_kib']for r in rows if r['arm']=='candidate'];cr=[r['rss_kib']for r in rows if r['arm']=='parent'];assert max(b)<min(c)*.99
cpu=statistics.median(b)/statistics.median(c);rss=statistics.median(br)/statistics.median(cr);assert math.isclose(cpu,report['timing']['median_cpu_ratio'],abs_tol=1e-12)and math.isclose(rss,report['timing']['median_rss_ratio'],abs_tol=1e-12)
receipt=dict(status='VERIFIED_SEALED_CORE_CONVERSION_REUSE',qualification_completion_run=41954263475,completion_source_commit='f70620dfc4e68efa5e666beb5a8e558099070649',completion_artifact=13381489248,completion_artifact_sha256=sha(a.completion_zip),source_run=41947915219,source_artifact=13381050552,source_artifact_sha256=sha(a.source_zip),parent_artifact_sha256=sha(a.parent_zip),binary_sha256=CANDIDATE,parent_binary_sha256=PARENT,source_tar_sha256=sha(a.completion/'candidate/source.tar.gz'),source_manifest_sha256=sha(a.completion/'candidate/source-manifest.json'),component_sha256=COMPONENT,source_files=368,exact_file_sets=True,source_controls=119,protected_controls=61,fresh_protected_controls=61,legacy_control_input_hashes_completed=17,native_targets=42,native_counts=report['native_counts'],known_failures=report['known_failures'],frozen208_unchanged=True,complete_mathlib_accept=False,full_frontier_unchanged=True,hot_oracle_receipt_sha256=sha(a.oracle),hot_oracle_reference_sha256=REFERENCE,hot_oracle_source_sha256=HOT,hot_oracle_parse_rc=0,hot_oracle_kernel_rc=0,parent_official_frontier_receipt_verified=True,median_parent_cpu=statistics.median(c),median_candidate_cpu=statistics.median(b),median_cpu_ratio=cpu,cpu_reduction_percent=100*(1-cpu),median_parent_rss_kib=statistics.median(cr),median_candidate_rss_kib=statistics.median(br),median_rss_ratio=rss,rss_reduction_percent=100*(1-rss),accepted_prefix_only=True,speed_win=True,qualified=True,promoted=False,no_rank_claim=True)
(a.out/'verified-readback.json').write_text(json.dumps(receipt,indent=2)+'\n');shutil.copyfile(a.oracle,a.out/'hot-oracle.json');print(json.dumps(receipt))
