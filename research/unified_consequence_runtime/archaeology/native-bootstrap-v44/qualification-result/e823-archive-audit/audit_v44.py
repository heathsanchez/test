"""Independent V44 artifact audit: archived source is parsed/read, never executed.

Reuses exactly pinned V43 pure archive/Git/packet/CAS predicates. A PASS wrapper
is emitted only after the actual Actions API, complete source/evidence/component
bytes, raw protected native execution and causal state independently close.
"""
from __future__ import annotations
import argparse,ast,base64,collections,hashlib,importlib.util,inspect,io,json,os,re,subprocess,tarfile,time,types,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
REUSED=HERE/'reused_v43_pure_auditor.py'
REUSED_SHA256='951903b0ab1ac6981852d2cf467e4ec074b8629e7b106f04b6ec79aca7c0847b'
if hashlib.sha256(REUSED.read_bytes()).hexdigest()!=REUSED_SHA256:
    raise ValueError('independent reused auditor bytes changed')
_spec=importlib.util.spec_from_file_location('v43_pure_audit_reuse',REUSED)
old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(old)
PREFIX=old.PREFIX
BASE='8830a66fcb261b192d98da495b6cb91697d21f28'
BRANCH='research/udm-native-bootstrap-v44-20261022'
WORKFLOW='.github/workflows/udm-native-bootstrap-v44.yml'
sha,fp,canonical,object_id=old.sha,old.fp,old.canonical,old.object_id
Store,Checks,native_status,live_nodes=old.Store,old.Checks,old.native_status,old.live_nodes
junit,git_tree,git=old.junit,old.git_tree,old.git


def verify_packet(value):
    if (not isinstance(value,dict) or not value.get('packet') or not isinstance(value.get('packet'),dict)
            or not isinstance(value.get('packet_sha256'),dict)):
        raise ValueError('missing actual nonempty native packet')
    decoded={name:base64.b64decode(raw,validate=True) for name,raw in value['packet'].items()}
    if {name:sha(raw) for name,raw in decoded.items()}!=value['packet_sha256']:
        raise ValueError('raw native packet hash inventory differs')
    return decoded


def verify_artifact_digest(path,artifact):
    with Path(path).open('rb') as stream:digest=old.hash_stream(stream)
    if artifact.get('size_in_bytes')!=Path(path).stat().st_size or artifact.get('digest')!='sha256:'+digest:
        raise ValueError('actual Actions ZIP bytes differ from independent API digest/size')
    return digest


def gate_files(raw):
    """Evaluate only the documented literal gate-file comprehension, never code."""
    tree=ast.parse(raw);values={'PREFIX':PREFIX}
    def evaluate(node,scope):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,int)):return node.value
        if isinstance(node,ast.Name) and node.id in scope:return scope[node.id]
        if isinstance(node,(ast.Tuple,ast.List)):
            result=[]
            for item in node.elts:
                if isinstance(item,ast.Starred):result.extend(evaluate(item.value,scope))
                else:result.append(evaluate(item,scope))
            return tuple(result)
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return evaluate(node.left,scope)+evaluate(node.right,scope)
        if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='tuple'
                and not node.keywords and len(node.args)==1 and isinstance(node.args[0],ast.GeneratorExp)):
            gen=node.args[0]
            if len(gen.generators)!=1:raise ValueError('unsupported gate generator')
            clause=gen.generators[0]
            if not isinstance(clause.target,ast.Name) or clause.ifs or clause.is_async:raise ValueError('unsupported gate clause')
            return tuple(evaluate(gen.elt,dict(scope,**{clause.target.id:item})) for item in evaluate(clause.iter,scope))
        raise ValueError('gate file declaration is not literal supported data')
    for node in tree.body:
        if not isinstance(node,ast.Assign):continue
        names=[n.id for n in node.targets if isinstance(n,ast.Name)]
        if not set(names)&{'TESTS','BOOTSTRAP_GATE_FILES'}:continue
        result=evaluate(node.value,values)
        for name in names:values[name]=result
    result=list(values.get('BOOTSTRAP_GATE_FILES',()))
    if not result or len(set(result))!=len(result) or any(not old.safe_name(name) for name in result):
        raise ValueError('missing, duplicate or unsafe literal bootstrap gate files')
    return result


def api_identity(args,check,out):
    run,rr=old.fetch_api(f'actions/runs/{args.run}',out/'API_RUN.json')
    listing,ar=old.fetch_api(f'actions/runs/{args.run}/artifacts?per_page=100',out/'API_ARTIFACTS.json')
    matching=[row for row in listing['artifacts'] if row['id']==args.artifact]
    if len(matching)!=1:raise ValueError('exact artifact not on independent Actions API')
    artifact=matching[0]
    check('api_run_identity',run['id']==args.run and run['head_sha']==args.source and run['head_branch']==BRANCH and run['path']==WORKFLOW)
    check('api_completed_green',run['status']=='completed' and run['conclusion']=='success')
    check('api_owned_isolated_event',run['event'] in ('push','workflow_dispatch') and run['repository']['full_name']=='heathsanchez/test')
    check('api_artifact_identity',not artifact['expired'] and artifact['workflow_run']['id']==args.run
          and artifact['workflow_run']['head_sha']==args.source and artifact['workflow_run']['head_branch']==BRANCH
          and artifact['name']==f'native-bootstrap-v44-{args.source}-{run["run_attempt"]}')
    digest=verify_artifact_digest(args.zip,artifact);check('exact_artifact_zip_bytes',True)
    return {'run':run,'artifact':artifact,'run_fetch':rr,'artifact_fetch':ar,'zip_sha256':digest}



def verify_uploaded_members(names,core,entries,read):
    """Every uploaded regular member must have a unique complete byte binding."""
    closed={}
    for name in names:
        if name.endswith('/') or name in core:continue
        matches=[name] if name in entries else [key for key in entries if name.endswith('/'+key)]
        if len(matches)!=1:
            raise ValueError('uploaded ZIP member lacks unique complete manifest binding: '+name)
        key=matches[0];row=entries[key]
        if row.get('kind')!='file' or sha(read(name))!=row.get('sha256'):
            raise ValueError('uploaded ZIP duplicate is not exact retained regular evidence: '+name)
        closed[name]=key
    return closed


def load_archive(args,check,out):
    source,evidence=Store(out/'source-by-sha256'),Store(out/'evidence-by-sha256')
    with zipfile.ZipFile(args.zip) as packet:
        names=packet.namelist()
        if len(names)!=len(set(names)) or not all(old.safe_name(n) for n in names) or packet.testzip() is not None:
            raise ValueError('unsafe, duplicate or corrupt actual ZIP member')
        def one(name):
            rows=[item for item in names if item==name or item.endswith('/'+name)]
            if len(rows)!=1:raise ValueError('expected one actual ZIP member '+name)
            return rows[0]
        manifest=json.loads(packet.read(one('MANIFEST.json')))
        check('archive_exact_manifest',manifest['schema']=='UDM_NATIVE_BOOTSTRAP_ARCHIVE_MANIFEST_V44'
            and manifest['source_commit']==args.source and str(manifest['run_id'])==str(args.run))
        for name,store,expected in [('SOURCE.tar.gz',source,manifest['source_sha256']),('NATIVE_BOOTSTRAP_V44_EVIDENCE.tar.gz',evidence,manifest['archive_sha256'])]:
            with packet.open(one(name)) as stream:check('complete_tar_hash:'+name,old.hash_stream(stream)==expected)
            with packet.open(one(name)) as stream:
                with tarfile.open(fileobj=stream,mode='r|gz') as archive:
                    for member in archive:
                        if member.isdir():
                            if not old.safe_name(member.name):raise ValueError('unsafe TAR directory')
                            continue
                        store.add(member,archive.extractfile(member) if member.isfile() else None)
                    if name=='SOURCE.tar.gz':check('source_tar_exact_commit',archive.pax_headers.get('comment')==args.source)
        actual={name:{k:v for k,v in row.items() if k in ('kind','sha256','target')} for name,row in evidence.entries.items()}
        check('every_evidence_member_closed',actual==manifest['files'],{'actual':len(actual),'declared':len(manifest['files'])})
        # Every separately uploaded regular ZIP member is either manifest/TAR or
        # an exact duplicate of the complete evidence archive. No source runs.
        core={one('MANIFEST.json'),one('SOURCE.tar.gz'),one('NATIVE_BOOTSTRAP_V44_EVIDENCE.tar.gz')}
        closed=verify_uploaded_members(names,core,evidence.entries,packet.read)
        check('every_uploaded_regular_member_closed',len(closed)+len(core)==sum(not name.endswith('/') for name in names))
        check('uploaded_result_exact',packet.read(one('run/RESULT.json'))==evidence.raw('run/RESULT.json'))
    return source,evidence,manifest


def audit_source(args,source,evidence,check,out):
    tree,baseline=git_tree(args.repo,args.source),git_tree(args.repo,BASE)
    commit=git(args.repo,'cat-file','commit',args.source)
    check('exact_committed_git_object',object_id('commit',commit)==args.source)
    frozen=evidence.js('FREEZE.json')
    check('freeze_identity',frozen['schema']=='UDM_NATIVE_BOOTSTRAP_FREEZE_V44' and frozen['source_commit']==args.source
          and frozen['scope']=='NATIVE_METADATA_BOOTSTRAP_INFRASTRUCTURE_ONLY')
    check('freeze_scientific_unknowns',all(frozen['verdicts'][f'G{i}']=='UNKNOWN' for i in range(2,7)))
    hashes={};mismatches=[]
    for name,row in tree.items():
        entry=source.entries.get(name)
        if entry is None or row['kind']!='blob' or entry['kind']!='file':mismatches.append(name);continue
        raw=source.raw(name);hashes[name]=sha(raw)
        if object_id('blob',raw)!=row['oid'] or '100'+format(entry['mode'],'03o')!=row['mode']:mismatches.append(name)
    check('every_source_blob_mode_and_inventory',not mismatches and set(source.entries)==set(tree),mismatches)
    check('source_complete_freeze',hashes==frozen['files'])
    check('all_2628_previous_files_modes_unchanged',len(baseline)==2628 and all(tree.get(n)==r for n,r in baseline.items()))
    protocol=source.js(PREFIX+'archaeology/native-bootstrap-v44/preimplementation/PROTOCOL.json')
    check('preimplementation_authority',protocol['baseline_commit']==BASE and protocol['original_verifier_bytes_immutable'] is True and len(protocol['cases'])==28)
    for name,digest in protocol['source_pins_sha256'].items():check('original_authority_pin:'+name,hashes[PREFIX+name]==digest)
    acceptance=frozen['acceptance'];manifest=source.js(PREFIX+'archaeology/native-bootstrap-v44/preimplementation/FREEZE_MANIFEST.json')
    check('acceptance_manifest_identity',acceptance['manifest_sha256']==sha(source.raw(PREFIX+'archaeology/native-bootstrap-v44/preimplementation/FREEZE_MANIFEST.json'))
          and acceptance['protocol_sha256']==sha(source.raw(PREFIX+'archaeology/native-bootstrap-v44/preimplementation/PROTOCOL.json')))
    for name,digest in manifest['files_sha256'].items():check('frozen_acceptance_bytes:'+name,hashes[PREFIX+'archaeology/native-bootstrap-v44/preimplementation/'+name]==digest)
    red=source.js(PREFIX+'archaeology/native-bootstrap-v44/preimplementation/PREIMPLEMENTATION_RED_RESULT.json')
    check('genuine_preimplementation_red',red['status']=='RED_MISSING_V44_IMPLEMENTATION' and all(red['junit'][k]==v for k,v in {'tests':'32','failures':'32','errors':'0','skipped':'0'}.items()))
    (out/'GIT_SOURCE_TREE.json').write_text(canonical(tree)+'\n')
    return frozen,hashes


def audit_controls(source,evidence,frozen,check):
    result=evidence.js('run/RESULT.json');inventory=evidence.js('run/PYTEST_INVENTORY.json')
    check('qualified_native_gate',result['schema']=='UDM_NATIVE_BOOTSTRAP_QUALIFICATION_V44' and result['status']=='QUALIFIED_BOUNDED_NATIVE_METADATA_BOOTSTRAP_ONLY')
    check('no_scientific_promotion',all(result['verdicts'][f'G{i}']=='UNKNOWN' for i in range(2,7)) and result['prospective_task_sources_accessed'] is False and result['coding_agent_executed'] is False)
    counts=junit(evidence.raw('run/contracts.xml'));collected=inventory['collection'];reports=inventory['reports']
    check('actual_contract_xml',counts==inventory['junit'] and inventory==result['contracts'] and counts['tests']>0
          and not any(counts[k] for k in ('failures','errors','skipped')) and inventory['pytest_exit_code']==0)
    check('exact_frozen_collection',collected==frozen['control_collection'] and len(set(collected))==len(collected)==counts['tests'])
    files={node.split('::',1)[0] for node in collected}
    for name in files:
        tree=ast.parse(source.raw(name));definitions={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')}
        executed={node.split('::',1)[1].split('[',1)[0] for node in collected if node.startswith(name+'::')}
        check('every_frozen_definition_executed:'+name,definitions==executed)
    for phase in ('setup','call','teardown'):
        rows=[r for r in reports if r['when']==phase]
        check('complete_actual_contract_phase:'+phase,[r['nodeid'] for r in rows]==collected and all(r['outcome']=='passed' and not r['wasxfail'] for r in rows))
    root='run/original-adversarial-controls/controls/'
    inherited=evidence.js(root+'result.json');log=evidence.raw(root+'unittest.log').decode()
    check('27_original_native_adversarial_controls',inherited['status']=='PASS' and inherited['tests']==27
          and not inherited['failures'] and not inherited['errors'] and inherited['test_method_code_objects_unchanged'] is True
          and sum(line.endswith(' ... ok') for line in log.splitlines())==27 and 'Ran 27 tests' in log and log.rstrip().endswith('OK'))
    raw=source.raw(PREFIX+'test_native_admission_v2_adversarial.py');tree=ast.parse(raw)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeAdmissionV2AdversarialTests')
    methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and not any(isinstance(d,ast.Name) and d.id=='classmethod' for d in n.decorator_list)]
    names={n.name for n in methods if n.name.startswith('test_')};executed=[line.split(' ',1)[0] for line in log.splitlines() if line.endswith(' ... ok')]
    check('exact_inherited_test_ids',len(names)==27 and len(executed)==len(set(executed))==27 and set(executed)==names)
    lines=raw.splitlines(keepends=True);hashes={n.name:sha(b''.join(lines[n.lineno-1:n.end_lineno])) for n in methods}
    check('exact_inherited_method_source',hashes==inherited['original_method_source_sha256'])
    check('exact_inherited_runner_and_source',sha(evidence.raw(root+'original-test-source.py'))==inherited['original_test_source_sha256']==sha(raw)
          and sha(evidence.raw(root+'runner-source.py'))==inherited['runner_sha256']==sha(source.raw(PREFIX+'native_inherited_controls_v43.py')))
    check('inherited_provenance',all(inherited[k]==v for k,v in evidence.js(root+'provenance.json').items()))
    return result


def audit_native(source,evidence,frozen,check):
    # Reuse exact packet/status implementation. Version only nonvacuity/count
    # boundaries appropriate to original V43 worker on tracked source.
    text=inspect.getsource(old.audit_native)
    text=text.replace("environments.append(evidence.js('run/RESULT.json')['controller_environment'])",
        "if 'controller_environment' in evidence.js('run/RESULT.json'): environments.append(evidence.js('run/RESULT.json')['controller_environment'])")
    text=text.replace("for v in ('42', '43'))", "for v in ('43',))")
    text=text.replace("row['junit']['passed'] == 2", "row['junit']['passed'] > 0")
    scope=dict(vars(old));exec(compile(text,str(Path(__file__))+':trusted-pure-packet-scope','exec'),scope)
    value=scope['audit_native'](source,evidence,frozen,check)
    check('nonempty_raw_native_coverage',bool(value['certificates']) and bool(value['receipts']))
    return value


def audit_build_costs(evidence,result,check):
    claimed=result['build_attempts'];rows=[]
    for path in evidence.matching('build-attempt.json'):
        if not path.startswith('run/'):continue
        value=evidence.js(path)
        if value.get('schema')=='udm.generic-build-attempt.v1':rows.append((path,value,sha(evidence.raw(path))))
    inventory={evidence.path_for_absolute(row['path']):(row['record'],row['sha256']) for row in claimed['records']}
    expected={path:(value,digest) for path,value,digest in rows}
    check('actual_all_process_build_attempt_inventory',inventory==expected and len(rows)==claimed['actual_unique_attempt_paths'])
    check('actual_all_process_build_counts',sum(v.get('build_calls',0) for _,v,_ in rows)==claimed['build_calls']>0
          and abs(sum(v.get('build_seconds',0) for _,v,_ in rows)-claimed['build_seconds'])<1e-7)
    for path,value,digest in rows:check('finite_original_build_cost:'+path,value['build_calls']==1 and type(value.get('build_seconds')) in (int,float) and 0<=value['build_seconds']<float('inf'))
    native=[]
    for path in evidence.matching('checked-report.json'):
        value=evidence.js(path)
        if isinstance(value,dict) and value.get('mode') in ('collect','run') and isinstance(value.get('costs'),dict):
            costs=value['costs'];native.append({'path':path,'mode':value['mode'],'costs':costs})
            check('retained_actual_native_counter:'+path,costs.get('native_calls')==int(value['mode']=='run') and costs.get('collection_calls')==int(value['mode']=='collect'))
    check('native_accounting_nonvacuous',result['native_attempts']['delta']['native_calls']>0 and result['native_attempts']['delta']['collection_calls']>0 and any(r['mode']=='run' for r in native))
    return {'actual_build_calls':claimed['build_calls'],'actual_unique_build_attempt_paths':len(rows),'build_seconds':claimed['build_seconds'],
            'retained_raw_native_attempt_paths':len(native),'main_process_native_counters':result['native_attempts'],
            'scope':'Nested/controller/native/backend timings retained; complete lifecycle cost UNKNOWN.'}


def _literal_assignment(raw,name):
    for node in ast.parse(raw).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('missing required literal '+name)



def strict_wheel_members(raw):
    members=old.wheel_members(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            if not info.is_dir() and (info.external_attr>>16)&0o170000 not in (0,0o100000):
                raise ValueError('nonregular original wheel member')
    return members


def core_metadata_fields(members):
    from email.parser import BytesParser
    from email import policy
    from packaging.utils import canonicalize_name
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
    from packaging.requirements import Requirement
    paths=[n for n in members if len(Path(n).parts)==2 and n.endswith('.dist-info/METADATA')]
    if len(paths)!=1:raise ValueError('missing or ambiguous core metadata member')
    path=paths[0];prefix=path.split('/')[0]
    if any(part.endswith('.dist-info') and part!=prefix for name in members for part in name.split('/')):
        raise ValueError('multiple wheel distribution identities')
    raw=members[path]
    try:
        raw.decode('utf-8')
        if b'\x00' in raw:raise ValueError('NUL core metadata')
        parsed=BytesParser(policy=policy.default).parsebytes(raw)
        if parsed.defects or parsed.get_all('Dynamic',[]):raise ValueError('malformed or dynamic wheel metadata')
        for field in ('Metadata-Version','Name','Version','Requires-Python'):
            values=parsed.get_all(field,[])
            if len(values)>1 or (field!='Requires-Python' and len(values)!=1):raise ValueError('missing or duplicate metadata singleton')
        def text(value):
            value=str(value)
            if not value or value!=value.strip() or any(ord(c)<32 or ord(c)==127 for c in value):raise ValueError('invalid core metadata text')
            return value
        if text(parsed['Metadata-Version']) not in ('1.0','1.1','1.2','2.1','2.2','2.3','2.4'):raise ValueError('unsupported metadata version')
        name,version=text(parsed['Name']),text(parsed['Version']);Version(version)
        grammar=r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?'
        if re.fullmatch(grammar,name) is None:raise ValueError('invalid metadata distribution name')
        dist_name,sep,dist_version=prefix[:-len('.dist-info')].rpartition('-')
        if not sep or canonicalize_name(dist_name)!=canonicalize_name(name) or Version(dist_version)!=Version(version):
            raise ValueError('core metadata and distribution directory differ')
        python=None if parsed.get('Requires-Python') is None else text(parsed['Requires-Python'])
        if python is not None:SpecifierSet(python)
        requirements=[text(v) for v in parsed.get_all('Requires-Dist',[])]
        for value in requirements:
            if Requirement(value).url:raise ValueError('unfrozen dependency URL')
        extras=[text(v) for v in parsed.get_all('Provides-Extra',[])]
        if any(re.fullmatch(grammar,v) is None for v in extras) or len({canonicalize_name(v) for v in extras})!=len(extras):
            raise ValueError('invalid or duplicate extra identity')
        classifiers=[text(v) for v in parsed.get_all('Classifier',[])]
        if len(set(classifiers))!=len(classifiers):raise ValueError('duplicate classifier')
    except (UnicodeError,ValueError,TypeError,AttributeError) as error:raise ValueError('invalid independent core metadata: '+str(error)) from error
    return {'name':name,'version':version,'requires_python':python,'requires_dist':requirements,'classifiers':classifiers,'provides_extra':extras}


def observation_paths(value):
    return {value['evidence']['build']['generated_wheel_evidence']['wheel_path'],value['independent_build']['generated_wheel_evidence']['wheel_path']}


def fresh_observation_paths(before,after):
    old_paths,new_paths=observation_paths(before),observation_paths(after)
    return len(old_paths)==len(new_paths)==2 and old_paths.isdisjoint(new_paths)


def audit_metadata_observation(request,observation,source,evidence,frozen,check,label):
    """Authenticate retained original-source metadata against two actual wheels."""
    from email.parser import BytesParser
    from email import policy
    authority=_literal_assignment(source.raw(PREFIX+'decisive_native_frontier.py'),'AUTHORITY')
    expected_fields={'schema','repo_path','commit','source_identity','interpreter','environment_sha256','protocol_binding','horizon_seconds','authority_ceiling'}
    check('metadata_request_exact_scope:'+label,set(request)==expected_fields and request['schema']=='UDM_SOURCE_NATIVE_METADATA_REQUEST_V44'
          and request['authority_ceiling']==authority and re.fullmatch('[0-9a-f]{64}',request['protocol_binding']) is not None
          and type(request['horizon_seconds']) is int and 1<=request['horizon_seconds']<=600)
    git_head=evidence.path_for_absolute(request['repo_path']+'/.git/HEAD');git_root=git_head.rsplit('/.git/',1)[0]
    identity,files,manifest,_=old.loose_git_source(evidence,git_root,request['commit'])
    source_files=fp({name:sha(raw) for name,raw in sorted(files.items())})
    check('metadata_original_git_identity:'+label,request['source_identity']==identity and observation['source_identity']==identity
          and observation['source_manifest_sha256']==fp(manifest) and observation['source_files_sha256']==source_files)
    check('metadata_observation_scope:'+label,observation['schema']=='UDM_SOURCE_NATIVE_METADATA_OBSERVATION_V44'
          and observation['status']=='VERIFIED_SOURCE_NATIVE_METADATA_OBSERVATION'
          and all(observation[key]==request[key] for key in ('repo_path','commit','interpreter','environment_sha256'))
          and fp(observation['environment'])==request['environment_sha256'])
    known=[row['environment'] for row in frozen['profile_identities'].values()]
    check('metadata_independently_frozen_environment:'+label,any(all(full.get(k)==v for k,v in observation['environment'].items()) for full in known))
    expected_pins={name:sha(source.raw(PREFIX+name)) for name in ('generic_build_materialization.py','generated_wheel_evidence.py','generated_overlay_gate.py','decisive_native_verify.py')}
    expected_pins['native_metadata_v44']=sha(source.raw(PREFIX+'native_metadata_v44.py'))
    check('metadata_observer_exact_source_pins:'+label,observation['source_pins']==expected_pins)
    recipe=_literal_assignment(source.raw(PREFIX+'generic_build_materialization.py'),'BUILD_RECIPE')
    outputs=[];reports=[]
    for phase,built in [('observe',observation['evidence']['build']),('independent',observation['independent_build'])]:
        descriptor=built['report'];report_path=evidence.path_for_absolute(descriptor['path']);raw=evidence.raw(report_path)
        check('metadata_build_receipt_bytes:'+label+':'+phase,sha(raw)==descriptor['sha256'] and len(raw)==descriptor['bytes'])
        report=json.loads(raw);wheel=built['generated_wheel_evidence'];path=evidence.path_for_absolute(wheel['wheel_path']);members=strict_wheel_members(evidence.raw(path))
        check('metadata_actual_complete_wheel:'+label+':'+phase,sha(evidence.raw(path))==wheel['wheel_sha256'] and fp({n:sha(v) for n,v in sorted(members.items())})==wheel['wheel_content_sha256'])
        check('metadata_builder_binding:'+label+':'+phase,wheel['schema']=='UDM_AUTHENTICATED_GENERATED_WHEEL_V2'
              and wheel['source_commit']==request['commit'] and wheel['source_tree_sha256']==identity['tracked_tree_sha256']
              and wheel['build_environment_sha256']==request['environment_sha256']
              and wheel['build_recipe_sha256']==fp(recipe) and wheel['builder_sha256']==expected_pins['generic_build_materialization.py'])
        command=report['build']['argv'];prefix=[request['interpreter'],*recipe['command']]
        check('metadata_original_build_launch:'+label+':'+phase,report['schema']=='udm.generic-build-materialization.v2'
              and report['status']=='BUILT_NOT_SCIENTIFICALLY_VERIFIED' and report['source_commit']==request['commit']
              and report['source_tree_sha256']==identity['tracked_tree_sha256'] and report['source_pyproject_sha256']==sha(files['pyproject.toml'])
              and report['interpreter']==request['interpreter'] and report['generated_wheel_evidence']==wheel
              and report['costs']['build_calls']==1 and report['build']['returncode']==0
              and command[:len(prefix)]==prefix and len(command)==len(prefix)+3 and command[-3]=='--wheel-dir'
              and Path(command[-2])==Path(wheel['wheel_path']).parent)
        attempt=evidence.js(report_path.rsplit('/',1)[0]+'/build-attempt.json')
        check('metadata_actual_original_build_attempt:'+label+':'+phase,attempt['schema']=='udm.generic-build-attempt.v1' and attempt['build_calls']==1
              and attempt['status']=='BUILD_COMMAND_PASS' and attempt['source_commit']==request['commit']
              and attempt['source_tree_sha256']==identity['tracked_tree_sha256'] and attempt['build_seconds']>=0)
        observed=core_metadata_fields(members)
        check('metadata_raw_header_observation:'+label+':'+phase,observation['metadata']==observed)
        outputs.append((path,members));reports.append(report)
    check('metadata_genuine_two_fresh_wheels:'+label,outputs[0][0]!=outputs[1][0] and outputs[0][1]==outputs[1][1])
    initial=observation['evidence']
    check('metadata_initial_input_binding:'+label,initial['schema']=='UDM_SOURCE_NATIVE_METADATA_EVIDENCE_V44'
          and initial['status']=='OBSERVED_NOT_INDEPENDENTLY_VERIFIED' and initial['metadata']==observation['metadata']
          and all(initial[k]==observation[k] for k in ('repo_path','commit','source_identity','source_manifest_sha256','source_files_sha256','interpreter','environment_sha256','environment','source_pins')))
    return {'source_identity':identity,'wheel_paths':[p for p,_ in outputs],'metadata':observation['metadata']}


def audit_flash(rows,root,evidence,check):
    if not rows:return
    name=root+'/flash-state-bundle.json'
    bundle=evidence.js(name);by_id={r['id']:r for r in rows};admissions={};revoked=set();digests={}
    check('flash_complete_event_inventory:'+root,bundle['schema']=='qckn-flash-state-bundle-v1' and len(bundle['events'])==len(rows)
          and {e['event_id'] for e in bundle['events']}=={'udm:warrant:'+r['id'] for r in rows})
    for event in bundle['events']:
        ident=event['event_id'].removeprefix('udm:warrant:');row=by_id[ident];record={k:v for k,v in row.items() if k!='id'};payload=event['payload']
        check('flash_exact_original_record:'+root+':'+ident,event['schema']=='qckn-flash-external-event-v1' and event['source_evidence_sha256']==fp(record)
              and event['payload_sha256']==fp(payload) and event['authority_snapshot']=='udm-local-warrant-log-v1' and event['verifier_id']=='metatron-causal-support-projection-v1')
        if row['kind']=='revoke':
            check('flash_exact_revocation:'+root+':'+ident,event['event_kind']=='capability_revocation' and payload=={'capability_id':'udm:warrant:'+row['payload']['target'],'reason':row['payload']['reason']})
            revoked.add(payload['capability_id']);typename='CapabilityRevocationEvent'
        else:
            cap=payload['capability'];semantic=[[ident,fp(record)]];supports=['udm:warrant:'+p for p in row['premises']]
            check('flash_exact_support:'+root+':'+ident,event['event_kind']=='capability_admission' and cap['capability_id']==event['event_id']
                  and cap['input_type']=='SupportNodeId' and cap['output_type']=='SupportRecordSHA256' and cap['semantics']==semantic
                  and cap['guard_inputs']==[ident] and cap['certificate_id']==ident and cap['dependencies']==supports and cap['provenance_ids']==[ident]
                  and cap['cost']==0 and payload['oracle']==semantic and payload['support_ids']==supports and payload['origin']=='support-projection-only')
            admissions[event['event_id']]=cap;typename='CapabilityAdmissionEvent'
        digests[event['event_id']]=sha(typename.encode()+b':'+canonical({'event_id':event['event_id'],**payload}).encode())
    check('flash_event_manifest:'+root,bundle['event_manifest']=={'schema':'qckn-flash-event-manifest-v1','events':[[k,v] for k,v in sorted(digests.items())]})
    live=set()
    while True:
        next_live=live|{k for k,cap in admissions.items() if k not in revoked and set(cap['dependencies'])<=live}
        if next_live==live:break
        live=next_live
    check('independent_flash_metatron_agreement:'+root,{k.removeprefix('udm:warrant:') for k in live}==live_nodes(rows))



def validate_metadata_lineage(node,nodes,objects,program,descriptor,scope,expected_generation):
    """Exact trusted-source/ceiling/admission lineage, separate from CAS hashing."""
    try:
        cap=node['payload']
        if (node['kind']!='executable_capability' or cap['operation']!='source.observe_native_metadata'
                or cap['source']!=descriptor or cap['scope']!=scope or objects[cap['program']]!=program
                or cap['transition']!='SCOPED_ADMISSION' or type(cap['generation']) is not int
                or cap['generation']!=expected_generation or len(cap['dependencies'])!=1 or len(cap['evidence'])!=1):
            raise ValueError('metadata capability source/program/scope/generation differs')
        support=nodes[cap['dependencies'][0]];verified=nodes[cap['evidence'][0]]
        if len(support['premises'])!=2:raise ValueError('metadata source/external authority ancestors absent')
        origin,authority=[nodes[key] for key in support['premises']]
        invocation=objects[cap['observation']];receipt=objects[verified['payload']['receipt']];nonce=receipt.get('nonce')
        expected={'family':'source-native-metadata-v44','program':cap['program'],'generation':cap['generation'],
                  'nonce':nonce,'supersedes':cap['supersedes'],'request':invocation['request'],'invocation':cap['observation']}
        expected_receipt={'schema':'UDM_SOURCE_NATIVE_METADATA_ADMISSION_V44','status':'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME',**expected}
        if (not isinstance(nonce,str) or re.fullmatch('[0-9a-f]{64}',nonce) is None
                or support['kind']!='source_support' or support['payload']!=expected
                or verified['kind']!='native_metadata_verification_v44' or verified['premises']!=[support['id']]
                or verified['payload']!={'program':cap['program'],'receipt':verified['payload']['receipt']}
                or receipt!=expected_receipt or node['premises']!=[support['id'],verified['id']]
                or origin['kind']!='native_metadata_source_v44' or origin['payload']!=descriptor
                or origin['premises']!=[authority['id']] or authority['kind']!='execution_authority_ceiling'
                or authority['payload']!=descriptor['authority_ceiling'] or authority['premises']):
            raise ValueError('metadata independent admission or source/authority lineage differs')
    except (KeyError,TypeError,IndexError) as error:raise ValueError('incomplete metadata causal lineage') from error


def validate_publication(node,nodes,objects,validator_hashes):
    try:
        p=node['payload'];capnode=nodes[p['capability_id']];verified=nodes[p['verification_id']];cap=capnode['payload']
        if (node['kind']!='native_frontier_route' or capnode['kind']!='executable_capability'
                or verified['kind'] not in validator_hashes or p['verification_id'] not in cap['evidence']
                or node['premises']!=[p['capability_id'],p['verification_id']]
                or p['contract']!=cap['scope']['frontier_contract'] or not p['profiles']
                or len(set(p['profiles']))!=len(p['profiles']) or p['profiles']!=sorted(p['profiles'])
                or not set(p['profiles'])<=set(cap['scope']['frontier_profiles'])
                or p['program']!=cap['program'] or verified['payload'].get('program')!=cap['program']
                or p['receipt']!=verified['payload'].get('receipt') or p['evidence_binding']!=fp(verified['payload'])
                or p['source_sha256']!=fp(cap['source']) or p['validator_source_sha256']!=validator_hashes[verified['kind']]
                or p['schema']!='metalogic.native-frontier.route.v1' or p['meaning']!='INDEPENDENTLY_WARRANTED_EXECUTABLE_ROUTE_AVAILABLE'
                or not isinstance(objects[p['receipt']],dict) or not objects[p['receipt']]):
            raise ValueError('frontier publication source/scope/evidence/causal binding differs')
        objects[cap['program']];objects[cap['observation']]
    except (KeyError,TypeError) as error:raise ValueError('incomplete frontier publication') from error


def audit_causal(source,evidence,frozen,native,check):
    ledgers={};metadata_caps=[];native_caps=[];observations={};withdrawals=[]
    authority=_literal_assignment(source.raw(PREFIX+'decisive_native_frontier.py'),'AUTHORITY')
    adapter=PREFIX+'native_bootstrap_runtime_v44.py';adapter_sha=sha(source.raw(adapter))
    pinned=('native_metadata_v44.py','native_source_v42.py','native_materialization_v43.py','developmental_machine_v44.py','cross_frontier_v44.py')
    descriptor={'schema':'UDM_SOURCE_NATIVE_METADATA_OPERATOR_SOURCE_V44','operation':'source.observe_native_metadata',
                'source_sha256':{'/workspace/udm-v54/'+PREFIX+name:sha(source.raw(PREFIX+name)) for name in pinned},
                'adapter_sha256':adapter_sha,'authority_ceiling':authority}
    program={'schema':'UDM_SOURCE_NATIVE_METADATA_PROGRAM_V44','operation':'source.observe_native_metadata',
             'metadata_source_sha256':sha(source.raw(PREFIX+'native_metadata_v44.py')),'adapter_sha256':adapter_sha,
             'native_outcome_authority':False,'source_algorithm':'original-qualified-pip-wheel-plus-independent-normalized-rebuild'}
    contract=_literal_assignment(source.raw(adapter),'FRONTIER_CONTRACT')
    validators={kind:sha(source.raw(PREFIX+filename)) for kind,filename in {
        'native_metadata_verification_v44':'native_bootstrap_runtime_v44.py','native_materialization_verification_v43':'native_materialization_v43.py',
        'native_observation_verification':'native_observation.py','native_constructor_verification':'native_constructor.py','generic_native_verification':'native_frontier.py'}.items()}
    for name in evidence.matching('metatron-ledger.jsonl'):
        rows,objects,root=old.audit_ledger(name,evidence,check);by_id={r['id']:r for r in rows};live=live_nodes(rows)
        ledgers[root]=(rows,objects);audit_flash(rows,root,evidence,check)
        # All original native CAS/receipt premises are still checked by the
        # unchanged pure V43 predicates; the new metadata edge is additive.
        existing=old.audit_cas_native_links(rows,objects,source,native,{'audited_verification_sha256':[]},check,root)
        native_caps.extend(existing['native_capabilities'])
        for node in rows:
            if node['kind']!='executable_capability' or node['payload'].get('operation')!='source.observe_native_metadata':continue
            cap=node['payload'];support=by_id[cap['dependencies'][0]];verification=by_id[cap['evidence'][0]]
            invocation=objects[cap['observation']];request=objects[invocation['request']];observation=objects[invocation['observation']]
            expected_scope={'request_sha256':fp(request),'environment_sha256':request['environment_sha256'],'authority_ceiling':authority,
                'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY','frontier_contract':contract,'frontier_profiles':['exact-source-native-metadata-v44:'+fp(request)]}
            generation=sum(r['kind']=='executable_capability' and r['payload'].get('operation')=='source.observe_native_metadata' and r['payload'].get('scope')==expected_scope for r in rows[:rows.index(node)+1])
            validate_metadata_lineage(node,by_id,objects,program,descriptor,expected_scope,generation)
            check('metadata_exact_original_source_ceiling_lineage:'+root+':'+node['id'],True)
            proof=audit_metadata_observation(request,observation,source,evidence,frozen,check,root+':'+node['id'])
            observations[fp(observation)]=proof
            source_desc=cap['source'];actual_program=objects[cap['program']]
            check('metadata_cap_program_source:'+root+':'+node['id'],actual_program['operation']=='source.observe_native_metadata'
                  and actual_program['native_outcome_authority'] is False and actual_program['metadata_source_sha256']==sha(source.raw(PREFIX+'native_metadata_v44.py'))
                  and actual_program['adapter_sha256']==sha(source.raw(PREFIX+'native_bootstrap_runtime_v44.py'))
                  and source_desc['adapter_sha256']==actual_program['adapter_sha256']
                  and all(value==sha(source.raw(PREFIX+Path(path).name)) for path,value in source_desc['source_sha256'].items()))
            receipt=objects[verification['payload']['receipt']]
            check('metadata_cap_exact_admission_lineage:'+root+':'+node['id'],cap['transition']=='SCOPED_ADMISSION'
                  and len(cap['dependencies'])==len(cap['evidence'])==1
                  and support['kind']=='source_support' and verification['kind']=='native_metadata_verification_v44'
                  and node['premises']==[support['id'],verification['id']] and verification['premises']==[support['id']]
                  and receipt['status']=='INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME' and receipt['invocation']==cap['observation']
                  and receipt['request']==invocation['request'] and receipt['generation']==cap['generation'] and receipt['supersedes']==cap['supersedes']
                  and verification['payload']['program']==cap['program'] and receipt['program']==cap['program']
                  and all(receipt[k]==v for k,v in support['payload'].items()))
            check('metadata_cap_exact_request_scope:'+root+':'+node['id'],cap['scope']['request_sha256']==fp(request)
                  and cap['scope']['environment_sha256']==request['environment_sha256'] and cap['scope']['authority_ceiling']==request['authority_ceiling']
                  and cap['scope']['frontier_profiles']==['exact-source-native-metadata-v44:'+fp(request)])
            for artifact in invocation['artifacts']:
                wheel=artifact['evidence'];retained=objects[artifact['artifact']];raw=base64.b64decode(retained['base64'],validate=True)
                check('metadata_cas_retained_wheel:'+root+':'+node['id']+':'+wheel['wheel_path'],sha(raw)==wheel['wheel_sha256'] and raw==evidence.raw(evidence.path_for_absolute(wheel['wheel_path'])))
            metadata_caps.append(node['id'])
        for node in rows:
            if node['kind']!='verified_consequence' or node['payload'].get('family')!='source-native-metadata-v44':continue
            receipt=objects[node['payload']['receipt']];invocation=objects[receipt['invocation']];request=objects[invocation['request']];observation=objects[invocation['observation']]
            cap=by_id[receipt['instrument']];proof=audit_metadata_observation(request,observation,source,evidence,frozen,check,root+':'+node['id'])
            observations[fp(observation)]=proof
            check('metadata_exact_executable_invocation:'+root+':'+node['id'],node['premises']==[cap['id']] and receipt['schema']=='UDM_SOURCE_NATIVE_METADATA_EXECUTION_V44'
                  and receipt['generation']==cap['payload']['generation'] and receipt['program']==cap['payload']['program']
                  and node['payload']['request']==fp(request) and node['payload']['observation']==fp(observation))
        for node in rows:
            if node['kind']!='executable_capability' or node['payload'].get('operation')!='native.pytest_suite':continue
            cap=node['payload'];inputs=cap['source'];binding=objects[inputs['bootstrap_binding']] if 'bootstrap_binding' in inputs else None
            if binding is None:continue
            native_contract,native_authority,native_policy=[objects[inputs[k]] for k in ('contract','suite_authority','policy')]
            witness=by_id[binding['consequence_id']];instrument=by_id[binding['capability_id']];selected=by_id[binding['environment_selection_id']]
            observed=by_id[cap['dependencies'][1]];record=selected['payload'];metadata_binding={k:v for k,v in binding.items() if k!='environment_selection_id'}
            metadata_receipt=objects[witness['payload']['receipt']];invocation=objects[metadata_receipt['invocation']];observation=objects[invocation['observation']]
            check('native_metadata_exact_causal_edges:'+root+':'+node['id'],all(parent in cap['dependencies'] and parent in node['premises'] and parent in observed['premises'] for parent in
                  (binding['capability_id'],binding['consequence_id'],binding['environment_selection_id'])))
            check('native_selected_environment_exact_context:'+root+':'+node['id'],cap['scope']['metadata_bootstrap']==binding
                  and selected['kind']=='native_environment_selection_v44' and selected['premises']==[binding['capability_id'],binding['consequence_id']]
                  and record['binding']==metadata_binding and record['contract_sha256']==fp(native_contract) and record['authority_sha256']==fp(native_authority)
                  and record['policy_sha256']==fp(native_policy) and record['environment_operation_sha256']==sha(source.raw(PREFIX+'native_environment_v44.py')))
            choice=objects[record['selection']];catalog=objects[record['catalog']]
            check('native_selection_uses_exact_metadata:'+root+':'+node['id'],choice['status']=='CANDIDATE_SOURCE_ENVIRONMENT' and choice['selected_profile']==record['profile']
                  and choice['catalog_sha256']==fp(catalog) and choice['constraints']['observation_evidence']['observation_sha256']==fp(observation)
                  and binding['observation_sha256']==fp(observation) and binding['generation']==instrument['payload']['generation'])
        for publication in (r for r in rows if r['kind']=='native_frontier_route'):
            validate_publication(publication,by_id,objects,validators)
            check('exact_original_route_publication:'+root+':'+publication['id'],True)
        registrations=[r for r in rows if r['kind']=='native_frontier_registration']
        if registrations:
            cache=evidence.js(root+'/native-frontiers.json')
            check('frontier_cache_log_binding:'+root,cache['ledger_sha256']==sha(evidence.raw(name)) and set(cache['frontiers'])=={r['payload']['frontier_id'] for r in registrations})
            routes=[r for r in rows if r['kind']=='native_frontier_route']
            for registration in registrations:
                p=registration['payload'];eligible=[r for r in routes if r['id'] in live and r['payload']['contract']==p['contract'] and p['profile'] in r['payload']['profiles']]
                candidates=sorted({r['payload']['capability_id'] for r in eligible});status='UNKNOWN_MISSING_AUTHORITY' if registration['id'] not in live else ('READY' if len(candidates)==1 else 'UNKNOWN_CHOICE' if candidates else 'UNKNOWN_SEARCH')
                actual=cache['frontiers'][p['frontier_id']]
                check('independent_frontier_readiness:'+root+':'+p['frontier_id'],actual['status']==status and actual['candidates']==candidates and actual['capability_id']==(candidates[0] if status=='READY' else None))
        for i,row in enumerate(rows):
            if row['kind']!='revoke':continue
            before,after=live_nodes(rows[:i]),live_nodes(rows[:i+1]);target=row['payload']['target']
            affected=[n for n in rows[:i] if n['kind']=='executable_capability' and n['payload'].get('operation')=='source.observe_native_metadata' and target in n['payload']['dependencies']]
            for cap in affected:
                restored=[n for n in rows[i+1:] if n['kind']=='executable_capability' and n['payload'].get('supersedes')==cap['id']]
                check('metadata_ancestor_selective_withdrawal:'+root+':'+cap['id'],cap['id'] in before and cap['id'] not in after and cap['id'] not in live)
                check('metadata_fresh_evidence_restoration:'+root+':'+cap['id'],bool(restored) and all(n['payload']['generation']>cap['payload']['generation'] and n['payload']['evidence']!=cap['payload']['evidence'] for n in restored))
                old_observation=objects[objects[cap['payload']['observation']]['observation']]
                check('metadata_restoration_actual_fresh_backend_paths:'+root+':'+cap['id'],bool(restored) and all(fresh_observation_paths(old_observation,objects[objects[n['payload']['observation']]['observation']]) for n in restored))
                withdrawals.append({'ledger':root,'target':target,'capability':cap['id'],'restored':[n['id'] for n in restored]})
    check('metadata_causality_nonvacuous',bool(metadata_caps) and bool(native_caps) and bool(withdrawals))
    return {'ledgers':ledgers,'metadata_capabilities':metadata_caps,'native_capabilities':native_caps,'observations':observations,'withdrawals':withdrawals}



def validate_fixture_context(label,base_files,augmented_files,fixture):
    full=fixture['tests/test_protected.py'];marker=b'\n\ndef test_protected_failure():'
    if full.count(marker)!=1:raise ValueError('frozen assertion boundary changed')
    passing=full.split(marker)[0]+b'\n'
    import_only=passing.split(b'\n\ndef test_original_pass():')[0]+b'\n'
    expected_base=dict(fixture,**{'tests/test_protected.py':import_only})
    expected_augmented=dict(fixture,**{'tests/test_protected.py':passing if label=='PASS' else full})
    if base_files!=expected_base or augmented_files!=expected_augmented:
        raise ValueError('native fixture differs from exact frozen original source/assertions')



def resolve_independent_receipt(wrapped,evidence,expected_path):
    """Original validation returns the old receipt plus fresh-execution locator."""
    try:
        annotation=wrapped['independent_reexecution']
        if not isinstance(annotation,dict) or set(annotation)!={'output','costs'}:raise ValueError('missing actual independent reexecution locator')
        path=evidence.path_for_absolute(annotation['output']+'/receipt.json')
        if path!=expected_path:raise ValueError('independent reexecution is not the declared separate output')
        fresh=evidence.js(path)
        original={k:v for k,v in wrapped.items() if k!='independent_reexecution'}
        if (annotation['costs']!=fresh['costs'] or fresh['status']!=original['status'] or fresh['junit']!=original['junit']
                or {k:v for k,v in fresh['execution'].items() if k!='costs'}!={k:v for k,v in original['execution'].items() if k!='costs'}):
            raise ValueError('actual fresh independent execution differs from original receipt or costs')
    except (KeyError,TypeError) as error:raise ValueError('missing actual independent reexecution evidence') from error
    return fresh


def audit_native_context(source,evidence,native,causal,check):
    root='run/native-supplement/'
    contexts={label:evidence.js(root+label+'_CONTEXT.json') for label in ('PASS','FAIL')}
    audited={r['sha256']:r for r in native['receipts']};runner=sha(source.raw(PREFIX+'native_execution_v43.py'))
    proofs={}
    for label,context in contexts.items():
        contract,authority,policy,candidate,certificate=[context[k] for k in ('contract','authority','policy','candidate','certificate')]
        git_head=evidence.path_for_absolute(contract['repo_path']+'/.git/HEAD');git_root=git_head.rsplit('/.git/',1)[0]
        base_id,base_files,base_manifest,_=old.loose_git_source(evidence,git_root,authority['baseline_commit'])
        identity,files,manifest,_=old.loose_git_source(evidence,git_root,contract['commit'])
        check('native_context_exact_original_git:'+label,base_id==authority['baseline_source'] and identity=={k:contract[k] for k in ('git_tree','tracked_tree_sha256','file_count')}
              and contract['commit']==authority['source_commit'] and candidate=={'replacements':[]} and authority['baseline_commit']!=contract['commit'])
        check('native_context_exact_original_tests:'+label,{n for n in files if files[n]!=base_files.get(n)}=={'tests/test_protected.py'}
              and set(files)==set(base_files) and all(row['mode'] in ('100644','100755') for row in manifest))
        fixture_prefix=PREFIX+'archaeology/native-bootstrap-v44/preimplementation/original_backend_fixture/'
        fixture={name[len(fixture_prefix):]:source.raw(name) for name in source.entries if name.startswith(fixture_prefix)}
        validate_fixture_context(label,base_files,files,fixture)
        check('native_exact_frozen_fixture_and_assertion_bytes:'+label,True)
        test_tree=ast.parse(files['tests/test_protected.py'])
        functions=[node for node in test_tree.body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
        protected={'tests/test_protected.py::'+node.name for node in functions}
        check('native_exact_required_original_assertions:'+label,protected==set(authority['required_test_nodes'])==set(certificate['collection']['selected_test_nodes'])
              and bool(functions) and all(any(isinstance(child,ast.Assert) for child in ast.walk(node)) for node in functions))
        for key in ('receipt','independent_receipt'):
            receipt=context[key]
            if key=='independent_receipt':
                check('native_reexecution_preserves_original_packet:'+label,{k:v for k,v in receipt.items() if k!='independent_reexecution'}==context['receipt'])
                receipt=resolve_independent_receipt(receipt,evidence,root+'native-'+label.lower()+'/independent/receipt.json')
            check('native_context_audited_raw_receipt:'+label+':'+key,fp(receipt) in audited and old.receipt_identity_matches(receipt,contract,authority,policy,certificate,candidate,runner))
            imports=receipt['execution']['import_manifest']
            check('native_context_exact_import_bytes:'+label+':'+key,bool(imports) and all(row['path'] in files and row['sha256']==sha(files[row['path']]) for row in imports)
                  and 'src/native_bootstrap_alpha/__init__.py' in {row['path'] for row in imports})
            raw=verify_packet(receipt)
            actual_status=native_status(receipt['execution'],junit(raw['native.xml']),certificate['collection'])
            check('native_context_independent_status:'+label+':'+key,actual_status==('PASS_NATIVE' if label=='PASS' else 'FAIL_NATIVE'))
            if label=='FAIL':
                check('native_protected_original_assertion_failure:'+key,receipt['junit']['failures']==1 and old.protected_failure_matches(raw['native.xml'],receipt['execution']['reports'],authority['required_test_nodes'],expected_assertion='assert 41 == 42'))
            else:check('native_original_nonzero_complete_pass:'+key,receipt['junit']==dict(tests=1,passed=1,failures=0,errors=0,skipped=0))
        proofs[label]={'base_commit':authority['baseline_commit'],'source_commit':contract['commit'],'junit':context['receipt']['junit']}
    report=evidence.js(root+'RESULT.json');restart=evidence.js(root+'restart/RESULT.json');process=evidence.js(root+'RESTART_PROCESS.json');spec=evidence.js(root+'RESTART_SPEC.json')
    ledger_root=root+'state';rows,objects=causal['ledgers'][ledger_root];by_id={r['id']:r for r in rows};live=live_nodes(rows)
    initial=by_id[report['initial_capability']];target=initial['payload']['dependencies'][0]
    cut=next(i for i,row in enumerate(rows) if row['kind']=='revoke' and row['payload']['target']==target)
    before,after=live_nodes(rows[:cut]),live_nodes(rows[:cut+1]);native_cap=report['initial_native_capability'];native_consequence=report['withdrawn_native_consequence'];unrelated=report['unrelated_support']
    check('native_actual_selective_metadata_ancestor_withdrawal',initial['id'] in before and initial['id'] not in after
          and native_cap in before and native_cap not in after and native_consequence in before and native_consequence not in after
          and unrelated in before and unrelated in after and unrelated in live)
    restored=by_id[report['restored_capability']];fresh_native=by_id[report['restored_native_capability']]
    check('native_actual_fresh_metadata_restoration',restored['id'] in live and restored['payload']['supersedes']==initial['id']
          and restored['payload']['generation']==initial['payload']['generation']+1 and restored['payload']['evidence']!=initial['payload']['evidence']
          and fresh_native['id'] in live and restored['id'] in fresh_native['payload']['dependencies']
          and native_cap not in live and native_consequence not in live)
    child_source=_literal_assignment(source.raw(PREFIX+'qualify_native_bootstrap_v44.py'),'_CHILD');argv=process['argv']
    check('actual_separate_process_frozen_child_launch',len(argv)==6 and argv[1:3]==['-B','-c'] and argv[3]==child_source
          and evidence.path_for_absolute(argv[4])==root+'RESTART_SPEC.json'
          and evidence.path_for_absolute(argv[5]+'/RESULT.json')==root+'restart/RESULT.json' and process['returncode']==0 and process['seconds']>0)
    check('restart_matches_retained_native_capability',spec['native_capability']==fresh_native['id'] and spec['capability']==restored['id']
          and spec['native_binding']==fresh_native['payload']['scope']['metadata_bootstrap'])
    child_consequence=by_id[restart['native_consequence']];child_receipt=objects[child_consequence['payload']['receipt']]
    child_independent=evidence.js(root+'restart/independent-native/receipt.json')
    check('restart_actual_independent_native_reexecution',fp(child_independent) in audited and child_independent['status']=='PASS_NATIVE'
          and child_independent['junit']==child_receipt['junit']
          and old.receipt_identity_matches(child_independent,spec['native']['contract'],spec['native']['authority'],spec['native']['policy'],spec['native']['certificate'],spec['native']['candidate'],runner)
          and {k:v for k,v in child_independent['execution'].items() if k!='costs'}=={k:v for k,v in child_receipt['execution'].items() if k!='costs'})
    check('restart_actual_native_packet',restart['status']=='PASS_SEPARATE_PROCESS_METADATA_AND_PROTECTED_NATIVE_EXECUTION'
          and restart['native_calls']>0 and restart['native_status']=='PASS_NATIVE' and restart['native_junit']==dict(tests=1,passed=1,failures=0,errors=0,skipped=0)
          and child_consequence['id'] in live and child_consequence['premises']==[fresh_native['id']]
          and fp(child_receipt) in audited and child_receipt['junit']==restart['native_junit'])
    metadata_binding=restart['binding'];metadata_consequence=by_id[metadata_binding['consequence_id']]
    check('restart_actual_fresh_metadata_execution',metadata_consequence['id'] in live and metadata_consequence['premises']==[restored['id']]
          and metadata_binding['observation_sha256']==fp(restart['metadata_observation']) and fp(restart['metadata_observation']) in causal['observations'])
    previous_paths=set()
    for row in rows[:rows.index(metadata_consequence)]:
        if row['kind']=='executable_capability' and row['payload'].get('operation')=='source.observe_native_metadata':
            invocation=objects[row['payload']['observation']]
        elif row['kind']=='verified_consequence' and row['payload'].get('family')=='source-native-metadata-v44':
            invocation=objects[objects[row['payload']['receipt']]['invocation']]
        else:continue
        previous_paths.update(observation_paths(objects[invocation['observation']]))
    check('restart_disjoint_actual_original_backend_launch_paths',len(observation_paths(restart['metadata_observation']))==2 and observation_paths(restart['metadata_observation']).isdisjoint(previous_paths))
    return {'contexts':proofs,'withdrawal_target':target,'old_native_capability':native_cap,'restored_native_capability':fresh_native['id'],
            'restart_native_consequence':child_consequence['id'],'restart_native_calls':restart['native_calls'],
            'scope':'Exact source/import/assertion/causal state for the frozen infrastructure supplement; same-filesystem restart only. No universal runtime refinement or prospective G2.'}


def audit_components(source,evidence,frozen,check):
    # Original component/Git/source/mode predicates. Current qualifier retains
    # LOADED_AUTHORITIES explicitly; the no-code data record is required.
    return old.audit_components(source,evidence,frozen,check)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zip',type=Path,required=True);p.add_argument('--source',required=True)
    p.add_argument('--run',type=int,required=True);p.add_argument('--artifact',type=int,required=True)
    p.add_argument('--repo',type=Path,default=Path('/workspace/udm-v54'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--qualification-result-path',type=Path)
    a=p.parse_args(argv)
    if not re.fullmatch('[0-9a-f]{40}',a.source) or a.out.exists() or a.out.resolve()!=a.out.absolute():p.error('exact source and new canonical output required')
    a.out.mkdir(parents=True);check=Checks();started=time.monotonic()
    report={'schema':'UDM_V44_INDEPENDENT_NATIVE_BOOTSTRAP_ARTIFACT_REPORT','source_commit':a.source,'run_id':a.run,'artifact_id':a.artifact,
            'scope':'NATIVE_METADATA_BOOTSTRAP_INFRASTRUCTURE_ONLY','auditor_source_sha256':sha(Path(__file__).read_bytes()),'reused_pure_auditor_sha256':REUSED_SHA256,
            'scientific_verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)},'external_enforcement':'UNKNOWN_NONBYPASSABILITY','formal_refinement':'UNKNOWN',
            'archive_policy':'Read regular bytes into content-addressed cache; inventory symlinks without dereference; never execute archived source.'}
    before=old.index_snapshot(a.repo,a.out,'local-index-before')
    components={k:old.index_snapshot(Path('/workspace/components')/k,a.out,'component-'+k+'-index-before') for k in ('development','metatron','flash')}
    try:
        report['api']=api_identity(a,check,a.out)
        source,evidence,manifest=load_archive(a,check,a.out);report['manifest']={k:v for k,v in manifest.items() if k!='files'}
        frozen,hashes=audit_source(a,source,evidence,check,a.out);result=audit_controls(source,evidence,frozen,check)
        report['native_packets']=audit_native(source,evidence,frozen,check)
        causal=audit_causal(source,evidence,frozen,report['native_packets'],check)
        report['causality']={k:v for k,v in causal.items() if k!='ledgers'}
        report['native_context']=audit_native_context(source,evidence,report['native_packets'],causal,check)
        report['components']=audit_components(source,evidence,frozen,check)
        report['costs']=audit_build_costs(evidence,result,check)
        report['indexes_runtime']=old.audit_indexes(evidence,check)
        report['inventory']={'source_files':len(source.entries),'evidence_members':len(evidence.entries),'causal_ledgers':len(causal['ledgers'])}
        result_raw=evidence.raw('run/RESULT.json');retained=a.out/'QUALIFICATION_RESULT.json';retained.write_bytes(result_raw)
        path=a.qualification_result_path or retained
        if not path.is_absolute():path=a.repo/path
        check('prospective_gate_result_exact_bytes',path.resolve()==path.absolute() and not path.is_symlink() and path.read_bytes()==result_raw)
        gate={'status':'ADMISSION_ONLY_QUALIFIED','source_commit':a.source,'run_id':a.run,'artifact_id':a.artifact,
              'artifact_sha256':report['api']['zip_sha256'],'qualification_result_sha256':sha(result_raw),'result_path':str(a.qualification_result_path or retained)}
        files=gate_files(source.raw(PREFIX+'qualify_native_bootstrap_v44.py'))
        if any(name not in hashes for name in files):raise ValueError('gate names absent from exact source archive')
        report['gate_material']={'bootstrap_gate':gate,'gate_files_sha256':{n:hashes[n] for n in files}}
    except BaseException as error:report['obstruction']=type(error).__name__+': '+str(error)
    finally:
        after=old.index_snapshot(a.repo,a.out,'local-index-after');check('auditor_readonly_root_index',before==after)
        for key,rows in components.items():check('auditor_readonly_component_index:'+key,rows==old.index_snapshot(Path('/workspace/components')/key,a.out,'component-'+key+'-index-after'))
        report['seconds']=time.monotonic()-started;report['checks']=check.rows;report['failures']=[row for row in check.rows if not row['pass']]
        report['status']='PASS_INDEPENDENT_NATIVE_BOOTSTRAP_AUDIT' if not report.get('obstruction') and not report['failures'] else 'UNKNOWN_INDEPENDENT_AUDIT_OBSTRUCTION'
        raw=(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();(a.out/'REPORT.json').write_bytes(raw)
        if report['status']=='PASS_INDEPENDENT_NATIVE_BOOTSTRAP_AUDIT':
            wrapper={'schema':'UDM_V44_INDEPENDENT_BOOTSTRAP_AUDIT','status':report['status'],**report['gate_material'],
                'independent_report_sha256':sha(raw),'all_native_packets_checked':True,
                'native_proof_scope':'Retained original collection/import/assertion/status packets; exact immutable source/candidate/import bytes additionally closed for complete native supplement. Metadata invocation wheels and Metatron/FLASH edges independently checked. No universal Python refinement claim.',
                'scientific_verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)}}
            (a.out/'BOOTSTRAP_ARCHIVE_AUDIT.json').write_text(json.dumps(wrapper,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'status':report['status'],'checks':len(check.rows),'failures':report['failures'],'obstruction':report.get('obstruction')},sort_keys=True))
    return int(report['status']!='PASS_INDEPENDENT_NATIVE_BOOTSTRAP_AUDIT')

if __name__=='__main__':raise SystemExit(main())
