"""Independent final V44 archive readback. Never executes archived/native code."""
import argparse,ast,hashlib,importlib.util,inspect,io,json,os,re,tarfile,time,types,zipfile
from pathlib import Path

PROOF=Path('/workspace/qualification/native-bootstrap-v44-independent-audit/audit_v44.py')
PROOF_SHA='772ecb351d03bbf9656ced960980ab94c746e59ae871c72ebd9a375ca24bae75'
CAS=Path('/workspace/udm-v54/research/unified_consequence_runtime/archaeology/experiment-interface-v43/prospective-result/archive-verification/independent_verify_cas.py')
CAS_SHA='05ea4d635494f045ab5c39c1420c2143ffec22110577e6492b9d9d1bfa92a018'
ROOT='research/unified_consequence_runtime/archaeology/native-bootstrap-v44/prospective-result/'
PREFIX='research/unified_consequence_runtime/'
WORKFLOW='.github/workflows/udm-native-frontier-evidence-v44.yml'
SOURCE='5a5573431658d08ea7da7fffbc39006e80aed536'
EXPECTATION_SHA='04c335873062f8d25043d38a053c1513cd4716a4b7ff1ac5c8ebaaa0a14e30ff'
NATIVE_WRAPPER_SHA='33700c20fa7a0324560a69ebb66eba84d19753be261e03944532f9579c35b365'
UNKNOWN={f'G{i}':'UNKNOWN' for i in range(2,7)}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def strict(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
def load(path,name,digest):
    if path.is_symlink() or sha(path.read_bytes())!=digest:raise ValueError('trusted data auditor changed')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zip',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--repo',type=Path,default=Path('/workspace/udm-v54'));parser.add_argument('--run',type=int,required=True);parser.add_argument('--artifact',type=int,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    proof=load(PROOF,'trusted_final_v44_pure_artifact_auditor',PROOF_SHA);old=proof.old;check=old.Checks();started=time.monotonic()
    report={'schema':'UDM_V44_INDEPENDENT_FINAL_ARCHIVE_AUDIT_V1','source_commit':SOURCE,'run_id':args.run,'artifact_id':args.artifact,
      'auditor_sha256':sha(Path(__file__).read_bytes()),'trusted_artifact_auditor_sha256':PROOF_SHA,'trusted_cas_verifier_sha256':CAS_SHA,
      'native_admission':'RETAINED_SEPARATE_WARRANTED_BOUNDED_GATE','scientific_verdicts':UNKNOWN,
      'scope':'ARCHIVE_ONLY_NO_NATIVE_REPLAY_NO_NEW_SCIENTIFIC_PROMOTION'}
    before=old.index_snapshot(args.repo,args.out,'root-index-before')
    components={k:old.index_snapshot(Path('/workspace/components')/k,args.out,'component-'+k+'-before') for k in ('development','metatron','flash')}
    try:
        run,run_fetch=old.fetch_api(f'actions/runs/{args.run}',args.out/'API_RUN.json')
        listing,artifact_fetch=old.fetch_api(f'actions/runs/{args.run}/artifacts?per_page=100',args.out/'API_ARTIFACTS.json')
        artifacts=[row for row in listing['artifacts'] if row['id']==args.artifact]
        if len(artifacts)!=1:raise ValueError('exact artifact missing from independently read Actions API')
        artifact=artifacts[0]
        check('actual_run_identity',run['head_sha']==SOURCE and run['head_branch']=='research/udm-native-bootstrap-v44-20261022'
              and run['path']==WORKFLOW and run['repository']['full_name']=='heathsanchez/test' and run['event']=='workflow_dispatch')
        check('actual_archive_workflow_green',run['status']=='completed' and run['conclusion']=='success')
        check('actual_artifact_identity',not artifact['expired'] and artifact['workflow_run']['id']==args.run
              and artifact['workflow_run']['head_sha']==SOURCE and artifact['name']==f'native-frontier-v44-archive-only-{SOURCE}-{run["run_attempt"]}')
        digest=proof.verify_artifact_digest(args.zip,artifact);check('actual_zip_digest_size_match_independent_API',True)
        report['api']={'run':run,'artifact':artifact,'run_fetch':run_fetch,'artifact_fetch':artifact_fetch,'zip_sha256':digest}
        source,evidence=old.Store(args.out/'source-by-sha256'),old.Store(args.out/'evidence-by-sha256')
        with zipfile.ZipFile(args.zip) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or not all(old.safe_name(n) for n in names) or z.testzip() is not None:raise ValueError('unsafe duplicate or corrupt ZIP')
            check('complete_zip_crc_unique_safe',True)
            outer=[]
            for name in names:
                if name=='MANIFEST.json' or name.endswith('/MANIFEST.json'):
                    value=strict(z.read(name))
                    if value.get('schema')=='UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43' and value.get('source_commit')==SOURCE and str(value.get('run_id'))==str(args.run):outer.append(name)
            if len(outer)!=1:raise ValueError('exact actual outer archive manifest is not unique')
            outer_prefix=outer[0][:-len('MANIFEST.json')]
            def one(suffix):
                if outer_prefix+suffix in names:return outer_prefix+suffix
                matches=[n for n in names if n==suffix or n.endswith('/'+suffix)]
                if len(matches)!=1:raise ValueError('actual uploaded member not unique: '+suffix)
                return matches[0]
            manifest=strict(z.read(one('MANIFEST.json')))
            check('actual_outer_manifest_identity',manifest['schema']=='UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43'
                  and manifest['source_commit']==SOURCE and str(manifest['run_id'])==str(args.run) and str(manifest['run_attempt'])==str(run['run_attempt']))
            for name,store,pin in [('SOURCE.tar.gz',source,'source_sha256'),('EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz',evidence,'archive_sha256')]:
                with z.open(one(name)) as raw:check('complete_uploaded_archive_sha:'+name,old.hash_stream(raw)==manifest[pin])
                with z.open(one(name)) as raw:
                    with tarfile.open(fileobj=raw,mode='r|gz') as archive:
                        for member in archive:
                            if member.isdir():
                                if not old.safe_name(member.name):raise ValueError('unsafe TAR directory')
                                continue
                            store.add(member,archive.extractfile(member) if member.isfile() else None)
                        if name=='SOURCE.tar.gz':check('full_source_commit_identity',archive.pax_headers.get('comment')==SOURCE)
            actual={n:{k:v for k,v in row.items() if k in ('kind','sha256','target')} for n,row in evidence.entries.items()}
            check('every_evidence_member_closed',actual==manifest['files'],{'actual':len(actual),'declared':len(manifest['files'])})
            tree,baseline=old.git_tree(args.repo,SOURCE),old.git_tree(args.repo,proof.BASE)
            check('full_source_inventory',set(source.entries)==set(tree))
            for name,row in tree.items():
                entry=source.entries[name];raw=source.raw(name)
                check('source_exact_blob_mode:'+name,row['kind']=='blob' and old.object_id('blob',raw)==row['oid'] and '100'+format(entry['mode'],'03o')==row['mode'])
            check('all_original_2628_files_and_modes_preserved',len(baseline)==2628 and all(tree.get(n)==row for n,row in baseline.items()))
            source_check=evidence.js('SOURCE_ARCHIVE_CHECK.json')
            check('source_check_matches_actual_complete_archive',source_check=={'status':'PASS_EXACT_FULL_SOURCE','source_commit':SOURCE,'files':len(tree),'source_sha256':manifest['source_sha256']})
            ci_raw=z.read(one('CI_ARCHIVE_RESULT.json'));ci=strict(ci_raw)
            (args.out/'CI_ARCHIVE_RESULT.json').write_bytes(ci_raw)
            core={one(n) for n in ('MANIFEST.json','SOURCE.tar.gz','EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz','CI_ARCHIVE_RESULT.json')}
            closed={}
            for name in names:
                if name.endswith('/') or name in core:continue
                hits=[]
                for label,store in [('source',source),('evidence',evidence)]:
                    for key,row in store.entries.items():
                        if row['kind']=='file' and (name==key or name.endswith('/'+key)):hits.append((label,key,row['sha256']))
                hashes={h for _,_,h in hits}
                if not hits or len(hashes)!=1 or sha(z.read(name)) not in hashes:raise ValueError('unindexed or changed uploaded member: '+name)
                closed[name]=[(label,key) for label,key,_ in hits]
            check('every_uploaded_regular_member_bound',len(closed)+len(core)==sum(not n.endswith('/') for n in names))
            report['uploaded_members']=closed
        expected_raw=source.raw(ROOT+'ARCHIVE_EXPECTATION.json');expected=strict(expected_raw)
        check('exact_committed_expectation',sha(expected_raw)==EXPECTATION_SHA and expected['schema']=='UDM_V44_FINAL_EVIDENCE_EXPECTATION_V1' and expected['mode']=='ARCHIVE_ONLY_NO_SCIENTIFIC_PROMOTION')
        check('workflow_exact_expectation_and_archive_boundary',EXPECTATION_SHA.encode() in source.raw(WORKFLOW)
              and b'ARCHIVE_ONLY_CHECK.py check' in source.raw(WORKFLOW) and b'--expected-source-commit' in source.raw(WORKFLOW))
        for name,pin in expected['files'].items():
            raw=source.raw(ROOT+name)
            check('exact_expected_record:'+name,len(raw)==pin['bytes'] and sha(raw)==pin['sha256'])
            check('prepared_record_is_exact_committed_source:'+name,evidence.raw('preparation/0/'+name)==raw)
        for name,pin in expected['repository_records'].items():
            raw=source.raw(name);check('exact_upstream_record:'+name,len(raw)==pin['bytes'] and sha(raw)==pin['sha256'])
        check('expectation_exact_roles',set(expected['roles'])=={'final_result','independent_audit','report'} and all(n in expected['files'] for n in expected['roles'].values()))
        result=source.js(ROOT+expected['roles']['final_result']);screening=source.js(ROOT+expected['roles']['independent_audit'])
        check('scientific_unknowns_preserved',result['verdicts']==expected['retained_scientific_verdicts']==ci['retained_scientific_verdicts']==ci['verdicts']==UNKNOWN)
        check('comparison_not_executed_or_promoted',result['comparison']=='NOT_STARTED_NO_TIE_OR_ADVANTAGE')
        check('actual_independent_screening_status_retained',screening['status']==expected['retained_independent_audit_status']==ci['retained_independent_audit_status'])
        check('CI_archive_only_zero_native_model_query',ci['schema']=='UDM_V44_FINAL_ARCHIVE_INTEGRITY_RESULT_V1' and ci['status']=='PASS_ARCHIVE_INTEGRITY_ONLY_NO_NATIVE_REPLAY'
              and ci['source_commit']==SOURCE and ci['baseline_commit']==proof.BASE and ci['preserved_files']==2628 and ci['source_files']==len(tree)
              and ci['expectation_sha256']==EXPECTATION_SHA and ci['native_calls']==ci['model_calls']==ci['new_source_queries']==0 and ci['index_restoration'] is False)
        check('CI_binds_actual_full_archives',ci['full_source_archive']=={'path':'SOURCE.tar.gz','sha256':manifest['source_sha256']}
              and ci['full_evidence_archive']=={'path':'EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz','sha256':manifest['archive_sha256']})
        gates=expected['qualified_gate_references'];check('CI_binds_exact_retained_native_gates',ci['qualified_gate_references']==gates and {r['kind'] for r in gates}=={'environment_v42','interface_v43','bootstrap_v44'})
        for row in gates:
            descriptor=row['descriptor'];raw=source.raw(row['result_record'])
            check('retained_native_gate_bytes:'+row['kind'],descriptor['status']=='ADMISSION_ONLY_QUALIFIED' and sha(raw)==descriptor['qualification_result_sha256'])
        native=next(r['descriptor'] for r in gates if r['kind']=='bootstrap_v44')
        wrapper=source.raw(result['native_gate_independent_audit']['path'])
        check('previous_independent_native_warrant_exact',native==result['native_gate'] and sha(wrapper)==NATIVE_WRAPPER_SHA==result['native_gate_independent_audit']['sha256']
              and strict(wrapper)['bootstrap_gate']==native and strict(wrapper)['status']=='PASS_INDEPENDENT_NATIVE_BOOTSTRAP_AUDIT')
        cas=load(CAS,'trusted_original_independent_CAS_data_verifier',CAS_SHA)
        namespace=dict(vars(cas),SCHEMA='UDM_CONTENT_ADDRESSED_RAW_EVIDENCE_ARCHIVE_V44',SCOPE='RAW_SCREENING_AND_SCIENTIFIC_EVIDENCE_DATA_ONLY_NO_PROMOTION')
        for name,value in vars(cas).items():
            if isinstance(value,types.FunctionType) and value.__globals__ is vars(cas):
                reb=types.FunctionType(value.__code__,namespace,value.__name__,value.__defaults__,value.__closure__);reb.__kwdefaults__=value.__kwdefaults__;namespace[name]=reb
        readbacks=[]
        for declaration in expected['archives']:
            archive_path=Path(source.entries[ROOT+declaration['archive']]['cache']);manifest_path=Path(source.entries[ROOT+declaration['manifest']]['cache'])
            manifest_raw=source.raw(ROOT+declaration['manifest']);m=strict(manifest_raw)
            check('raw_CAS_original_scope_identity',m['source_root']==declaration['source_root']=='/workspace/qualification/native-frontier-v44-operator')
            verified=namespace['verify'](archive_path,manifest_path,None);retained=source.js(ROOT+declaration['readback'])
            keys=('archive_sha256','archive_bytes','external_manifest_sha256','source_counts','source_entries','unique_objects','source_regular_bytes','unique_object_bytes')
            check('raw_CAS_all_objects_bytes_modes_paths_links',verified['status']=='PASS' and verified['every_member_hash_size_mode_verified'] and verified['exact_member_inventory_no_extra'] and verified['original_path_map_preserved'])
            check('raw_CAS_retained_original_readback_equal',retained['schema']=='UDM_V44_DATA_ARCHIVE_READBACK_V1' and retained['original_verifier_sha256']==CAS_SHA
                  and retained['original_verdict']['source_lstat_and_bytes_verified'] is True and all(retained['original_verdict'][k]==verified[k] for k in keys))
            check('CI_raw_CAS_full_readback_binding',any(all(row[k]==verified[k] for k in keys) and row['source_lstat_and_bytes_verified'] is False for row in ci['raw_archives']))
            readbacks.append(verified)
        report['raw_CAS']=readbacks
        # Reuse precisely the original pure component tar/Git/blob predicates,
        # stopping before native-run loaded-authority checks in this archive-only job.
        text=inspect.getsource(old.audit_components);marker="    loaded_name = 'run/LOADED_AUTHORITIES.json'"
        if text.count(marker)!=1:raise ValueError('trusted component pure predicate boundary changed')
        scope=dict(vars(old));exec(compile(text.split(marker)[0]+'    return result\n',str(Path(__file__))+':original-component-byte-audit','exec'),scope)
        report['components']=scope['audit_components'](source,evidence,{},check)
        comp_sha=sha(evidence.raw('COMPONENT_SOURCE_MANIFEST.json'))
        check('CI_complete_components_bound',comp_sha==manifest['component_source_manifest_sha256']==ci['component_source_manifest_sha256']
              and manifest['component_source_status']==ci['component_source_status']=='PASS_EXACT_ORIGINAL_COMPONENT_SOURCES')
        # All archive interval snapshots are retained; runtime post-state is not
        # asserted by this separate zero-native archival workflow.
        text=inspect.getsource(old.audit_indexes);marker="    post = evidence.js('POST_CONTROL_RUNTIME_AUDIT.json')"
        if text.count(marker)!=1:raise ValueError('trusted archive index predicate boundary changed')
        scope=dict(vars(old));exec(compile(text.split(marker)[0]+"    check('archive_index_intervals_nonvacuous',bool(intervals))\n    return intervals\n",str(Path(__file__))+':original-index-byte-audit','exec'),scope)
        report['index_intervals']=scope['audit_indexes'](evidence,check)
        report['inventory']={'source_files':len(source.entries),'evidence_members':len(evidence.entries),'expected_files':len(expected['files']),'repository_records':len(expected['repository_records'])}
        report['retained_result']=result;report['retained_screening_status']=screening['status'];report['CI_archive_result_sha256']=sha(ci_raw)
    except BaseException as error:report['obstruction']=type(error).__name__+': '+str(error)
    finally:
        check('independent_auditor_root_index_unchanged',before==old.index_snapshot(args.repo,args.out,'root-index-after'))
        for key,snapshot in components.items():check('independent_auditor_component_index_unchanged:'+key,snapshot==old.index_snapshot(Path('/workspace/components')/key,args.out,'component-'+key+'-after'))
        report['seconds']=time.monotonic()-started;report['checks']=check.rows;report['failures']=[r for r in check.rows if not r['pass']]
        report['status']='PASS_INDEPENDENT_FINAL_ARCHIVE_ONLY_AUDIT' if not report.get('obstruction') and not report['failures'] else 'UNKNOWN_FINAL_ARCHIVE_AUDIT_OBSTRUCTION'
        (args.out/'REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
        print(json.dumps({'status':report['status'],'checks':len(check.rows),'failures':report['failures'],'obstruction':report.get('obstruction')},sort_keys=True))
    return int(report['status']!='PASS_INDEPENDENT_FINAL_ARCHIVE_ONLY_AUDIT')

if __name__=='__main__':raise SystemExit(main())
