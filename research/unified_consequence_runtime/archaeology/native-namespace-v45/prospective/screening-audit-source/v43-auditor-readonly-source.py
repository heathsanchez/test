"""Offline supplied-run V43 screening audit. No target interpreter or build runs.

This is an evidence auditor, not an oracle or reference monitor. The command
requires independently supplied authority, controller and actor pins. It writes
only a new external audit directory; a finalizer separately closes its dossier.
"""
import argparse
import ast
import base64
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

HERE = Path(__file__).resolve().parent
MODE = 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'
COVERAGE = ('V43 builder launches and generated-build verification attempts in this screening interval; '
    'parent wall time includes provisioning, host checks and independent oracle work. '
    'Original native counters and ceilings are unchanged; build seconds are included in parent wall time.')
HEX = re.compile(r'[0-9a-f]{64}')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def fp(value): return sha(canonical(value).encode())


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def require(ok, reason):
    if not ok: raise ValueError(reason)


def count(value):
    require(type(value) is int and value >= 0, 'invalid integer launch count')
    return value


def build_costs(report):
    before, after = (report['build_attempts'][key] for key in ('before', 'after'))
    result = {'coverage': COVERAGE, 'inclusive_parent_wall_seconds': report['total_wall_seconds']}
    for key in ('build_calls', 'build_seconds'):
        a,b = before['builder_attempts'][key], after['builder_attempts'][key]
        require(number(a) and number(b) and b >= a, 'build counter rollback or invalid count')
        if key == 'build_calls': count(a); count(b)
        result[key] = b-a
    a,b = before['verification_attempts'], after['verification_attempts']
    count(a);count(b);require(b >= a, 'verification counter rollback')
    result['verification_attempts'] = b-a
    require(number(result['inclusive_parent_wall_seconds']), 'invalid parent wall time')
    old,new = before['builder_attempts']['records'], after['builder_attempts']['records']
    require(isinstance(old,list) and isinstance(new,list) and new[:len(old)] == old,
            'build record prefix changed')
    return result


def public_fields(report):
    require(report['schema'] == 'UDM_ADMISSION_ONLY_CASE_V43', 'wrong screening report schema')
    require(report['screening_mode'] == MODE, 'candidate/search information in screening mode')
    require(report.get('accounting_complete') is True, 'incomplete native accounting')
    eligible = report['status'] in ('PASS_NATIVE', 'FAIL_NATIVE')
    require(report.get('eligible') is eligible, 'PASS/FAIL parity or UNKNOWN eligibility differs')
    require(number(report['total_wall_seconds']), 'invalid case wall time')
    costs = {key: count(report['controller_attempts'].get(key,0)) for key in ('native_calls','collection_calls')}
    for row in report.get('partial_native_reports', []):
        for key in costs: count(row.get('costs',{}).get(key,0))
    for key in costs:
        costs[key] = max(costs[key],sum(row.get('costs',{}).get(key,0) for row in report.get('partial_native_reports',[])))
    return {'schema':'UDM_SEALED_ADMISSION_ENVELOPE_V43', 'repository':report['repository'],
        'spec_sha256':report['spec_sha256'], 'status':'ADMITTED_NATIVE' if eligible else 'UNKNOWN_ADMISSION_SCREENING',
        'eligible':eligible, 'screening_mode':MODE, 'costs':costs,
        'build_costs':build_costs(report),'total_wall_seconds':report['total_wall_seconds']}


def validate_request(index, spec, request, authority_sha):
    require(request == {'pool_index':index,'spec':spec,'protocol_binding':authority_sha},
            'request source/order/trusted authority replay')


def validate_meter(pool, meter, authority_sha):
    require(meter['schema']=='UDM_ORDERED_SCREENING_METER_V43' and meter['authority_sha256']==authority_sha,
            'wrong original screening authority meter')
    require(meter.get('pending') is None and meter.get('accounting_complete') is True,
            'interrupted or incomplete screening meter')
    require(len(meter['cases'])==len(pool),'entire pool, including UNKNOWN, must be retained')
    sums={'native_calls':0,'collection_calls':0}
    for i,(spec,row) in enumerate(zip(pool,meter['cases'])):
        require(row['index']==i and row['spec_sha256']==fp(spec) and row['accounting_complete'] is True,
                'reordered, replaced or incomplete screening case')
        require(count(row['costs']['native_calls'])<=2,'per-case native ceiling exceeded')
        for key in sums:sums[key]+=count(row['costs'][key])
    require(all(count(meter[key])==value for key,value in sums.items()),'global native costs differ')


def validate_context_bytes(data, files, required):
    nodes,selected=data.get('collected_test_nodes',[]),data.get('selected_test_nodes',[])
    require(bool(nodes) and len(nodes)==len(set(nodes)) and len(selected)==len(set(selected))
            and set(nodes)==set(selected),'incomplete or duplicate selected suite')
    require(not any(data.get(key) for key in ('deselected_test_nodes','collection_errors','source_mutations',
        'unexpected_imports','external_project_imports','plugin_violations','changed_test_code')),
        'source/import/suite identity violation')
    for prefix in required:
        require(any(n==prefix or n.startswith(prefix+'[') or n.startswith(prefix+'::') for n in nodes),
                'missing complete protected assertion prefix: '+prefix)
    require(bool(data.get('test_items')),'no exact collected test-byte inventory')
    item_nodes=[row.get('nodeid') for row in data['test_items']]
    require(len(item_nodes)==len(set(item_nodes)) and set(item_nodes)==set(nodes),
        'test-byte inventory does not uniquely cover complete collected suite')
    for field in ('test_items','import_manifest'):
        for row in data.get(field,[]):
            require(row.get('path') in files and row.get('sha256')==sha(files[row['path']]),
                    'exact source/test/import bytes differ: '+str(row.get('path')))


def is_test(name):
    p=PurePosixPath(name)
    return name.endswith('.py') and (any(x in {'test','tests','testing'} for x in p.parts)
        or p.name.startswith('test_') or p.name.endswith('_test.py') or p.name=='conftest.py')


def validate_author_tests(spec, source):
    boundaries=source.get('source_boundaries')
    require(isinstance(boundaries,dict),'prepared source-boundaries receipt missing')
    require(boundaries.get('author_test_head_commit')==spec['head_commit'],'author-test head differs from frozen PR')
    expected={row['filename']:row['sha'] for row in spec['files'] if is_test(row['filename'])}
    listed=boundaries.get('author_tests',[]);transports=source.get('author_test_transports',[])
    require(expected and len(listed)==len(expected) and len(transports)==len(expected)
        and {row['path'] for row in listed}==set(expected)
        and {row['record']['path'] for row in transports}==set(expected),'complete changed author-test set missing or duplicated')
    require(all(row['git_blob']==expected[row['path']] for row in listed)
        and all(row['record'] in listed for row in transports),'author-test transport differs from exact frozen head blob')


def validate_native_disposition(report, receipts):
    statuses=[row['status'] for row in receipts]
    if len(statuses)==2 and statuses[0]==statuses[1] and statuses[0] in ('PASS_NATIVE','FAIL_NATIVE'):
        require(report['status']==statuses[0] and report['eligible'] is True,
            'completed authentic native outcome masked or swapped by screening report')
        validate_reexecution_pair(receipts)
    else:
        require(report['eligible'] is False and report['status'] not in ('PASS_NATIVE','FAIL_NATIVE'),
            'incomplete/mismatched native outcomes cannot license admission')


def validate_reexecution_pair(receipts):
    require(len(receipts)==2 and all(all(isinstance(row.get(key),str) and row[key] for row in receipts)
        and len({row[key] for row in receipts})==2
        for key in ('path','sha256','execution_packet_sha256')),
        'producer and independent reexecution lack distinct actual packet/receipt identities')


def validate_retained_build_sidecar(record, sidecar, verification, launches):
    require(record==sidecar and record['status']=='VERIFIED_GENERATED_BUILD'
        and record['receipt']==verification and fp(verification['build']) in launches,
        'nested build verification lacks exact sidecar/verification/actual launch links')


def validate_generated_link(evidence, preparation, verification, original_members, rebuilt_members):
    require(preparation['status']=='BUILT_NOT_SCIENTIFICALLY_VERIFIED'
        and preparation['binding']==evidence['binding']
        and preparation['generated_sha256']==evidence['generated_sha256'],
        'original generated evidence lacks exact successful preparation build')
    ignore_path=lambda row:{k:v for k,v in row.items() if k!='wheel_path'}
    require(ignore_path(preparation['generated_wheel_evidence'])==ignore_path(evidence['wheel_evidence']),
        'original preparation wheel evidence differs')
    require(verification['status']=='INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
        and verification['evidence_sha256']==fp(evidence) and verification['binding']==evidence['binding']
        and verification['build']['binding']==evidence['binding'],'independent verification uses another generated evidence')
    require(original_members==rebuilt_members,'complete original/independent native wheel members differ')


def validate_plugin_bytes(plugin, files, read):
    if plugin.get('kind')=='source':
        require(plugin['path'] in files and sha(files[plugin['path']])==plugin['sha256'],
            'original source plugin bytes differ')
    else:require(sha(read(plugin['path']))==plugin['sha256'],'actual runtime/pytest plugin bytes differ')


def audit_metadata(plan, pre, metadata, pool):
    universe=plan['repository_universe_fixed_before_github_queries']
    require(universe==pre['repository_universe_fixed_before_github_queries']
        and universe==sorted(set(universe)) and len(universe)<=9,'fixed sorted metadata universe differs')
    require([r['repo'] for r in metadata['repositories']]==universe,'missing/reordered repository metadata dispositions')
    require(not set(universe)&set(plan['historically_touched_repository_exclusions']),'previous exposure not excluded')
    chosen=[];queries=[]
    for row in metadata['repositories']:
        queries.extend(row['query_coverage']);qualifiers=[]
        if row['status']=='UNAVAILABLE':
            require(not row['candidates'] and row.get('reasons'),'metadata API refusal not retained');continue
        require(len(row['candidates'])==row['closed_pr_count']<=100,'closed PR metadata window differs')
        for rank,c in enumerate(row['candidates'],1):
            reasons=[]
            if not c['merged_at']:reasons.append('NOT_MERGED')
            if not(re.match(r'^fix',c['title'],re.I) or any('bug' in v.lower() for v in c['labels'])):
                reasons.append('TITLE_NOT_FIX_AND_NO_BUG_LABEL')
            if not reasons:
                files=c['files'];tests=[f for f in files if is_test(f['filename'])]
                production=[f for f in files if f['filename'].endswith('.py') and not is_test(f['filename'])]
                adds=sum(f['additions'] for f in production);dels=sum(f['deletions'] for f in production)
                require(c['metadata_stats']=={'test_py_files':len(tests),'production_py_files':len(production),
                    'production_additions':adds,'production_deletions':dels},'metadata predicate statistics differ')
                if any(f['status'] in ('renamed','removed') for f in files):reasons.append('RENAMED_OR_REMOVED_CHANGED_FILE')
                if not tests:reasons.append('NO_CHANGED_TEST_PY')
                if not production:reasons.append('NO_CHANGED_PRODUCTION_PY')
                if not 1<=dels<=4:reasons.append('PRODUCTION_DELETIONS_OUTSIDE_1_TO_4')
                if adds>6:reasons.append('PRODUCTION_ADDITIONS_ABOVE_6')
                if not reasons and any(f['status']!='modified' for f in production):reasons.append('PRODUCTION_PY_NOT_ALL_PREEXISTING_MODIFIED')
            extras=[v for v in c['reasons'] if v not in reasons]
            require(not extras or any(q.get('status')!='OK' for q in row['query_coverage'])
                or extras==['FILES_API_3000_FILE_LIMIT_PAGINATION_NOT_CLOSED'],'unsupported metadata rejection reason')
            require(all(v in c['reasons'] for v in reasons) and c['rank_within_repository']==rank
                and c['status']==('REJECTED_METADATA_PREDICATES' if c['reasons'] else 'QUALIFIES_METADATA_ONLY'),
                'original fixed metadata predicate decision differs')
            if not c['reasons']:qualifiers.append(c)
        require(row['qualifying_prs']==[c['number'] for c in qualifiers]
            and row.get('first_qualifying_pr')==(qualifiers[0]['number'] if qualifiers else None),
            'first qualifying PR replaced or filtered')
        if qualifiers:chosen.append((row['repo'],qualifiers[0]))
    require(len(chosen)==len(pool['pool']) and metadata['pool']==pool['pool'],'entire metadata pool differs')
    for spec,(repo,c) in zip(pool['pool'],chosen):
        require(spec['repo']==repo and spec['pr']==c['number'] and spec['base_commit']==c['base']['sha']
            and spec['head_commit']==c['head']['sha'] and spec['files']==c['files'],'frozen first metadata qualifier retargeted')
        queries.extend(spec.get('tree_query_coverage',[]))
    allowed=[(r'repos/[^/]+/[^/]+/pulls\?state=closed&sort=updated&direction=desc&per_page=100&page=1','closed_pr_list'),
        (r'repos/[^/]+/[^/]+/pulls/[1-9][0-9]*/files\?per_page=100&page=[1-9][0-9]*','changed_file_pages'),
        (r'repos/[^/]+/[^/]+/git/commits/[0-9a-f]{40}','git_commit_metadata'),
        (r'repos/[^/]+/[^/]+/git/trees/[0-9a-f]{40}\?recursive=1','git_tree_metadata')]
    for q in queries:
        require('/'.join(q['endpoint'].split('/')[1:3]) in universe
            and any(re.fullmatch(pattern,q['endpoint']) and q['projection']==plan['api_allowlist'][key] for pattern,key in allowed)
            and q['requested_at_utc']>=pre['committed_bytes_verified_at_utc'],'nonallowlist or precommit query')
    require(len(queries)==metadata['costs']['metadata_api_calls'] and metadata['costs']['native_calls']==metadata['costs']['collection_calls']==0,
        'all metadata query counts/refusals must be retained')
    return {'repositories':len(universe),'pool_members':len(chosen),'retained_query_count':len(queries)}


def require_closed_dossier(value):
    require(value.get('status')=='PASS_RETAINED_SCREENING_BINDINGS' and value.get('checks')
            and all(row.get('pass') is True for row in value['checks']), 'unclosed audit dossier')


class Audit:
    def __init__(self):self.checks=[];self.inputs={};self.native=[];self.builds=[];self.cases=[]
    def check(self,name,ok,detail=None):
        self.checks.append({'check':name,'pass':bool(ok),**({'detail':detail} if detail is not None else {})})
        return bool(ok)
    def read(self,path):
        path=Path(path);require(path.is_absolute() and path.resolve()==path and path.is_file()
            and not path.is_symlink(),'canonical regular retained file required: '+str(path))
        raw=path.read_bytes();self.inputs[str(path)]={'sha256':sha(raw),'bytes':len(raw)};return raw
    def js(self,path):return json.loads(self.read(path))
    def bound(self,desc,root=None):
        path=Path(desc['path']);path=(Path(root)/path) if not path.is_absolute() and root else path
        require(sha(self.read(path))==desc['sha256'],'retained external/input digest differs: '+str(path))
        return self.js(path)


def load_helper(name):
    p=HERE/name;spec=importlib.util.spec_from_file_location('_v43_screening_'+p.stem,p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def packet(a, value, folder, execution=False):
    raw={key:base64.b64decode(item,validate=True) for key,item in value['packet'].items()}
    require(value['packet_sha256']=={key:sha(item) for key,item in raw.items()},'packet hashes differ')
    required={'stdout.log','stderr.log','report.json','checked-report.json','tracked-source-manifest.json'}
    require(required<=set(raw) and not set(raw)-required-{'native.xml'},'packet membership differs')
    for name,item in raw.items():require(a.read(Path(folder)/name)==item,'packet not exact retained bytes')
    data=json.loads(raw['checked-report.json']);producer=json.loads(raw['report.json'])
    controller={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
    require(producer=={k:v for k,v in data.items() if k not in controller},'producer/checked packet differs')
    return data,raw


def generated_files(a, evidence, contract, authority, policy, source, archive, builder, recipe):
    if evidence is None:return {}
    b=evidence['binding'];base=source['base_files'];decl=builder.declared_outputs(base)
    expected={'contract_sha256':fp(dict(contract,generated_build=None)),'authority_sha256':fp(authority),
        'policy_sha256':fp(policy),'repository':contract['repository'],'protocol_binding':contract['protocol_binding'],
        'base_commit':authority['baseline_commit'],'base_source':source['base_identity'],
        'augmented_commit':contract['commit'],'augmented_source':source['identity'],
        'pyproject_sha256':sha(base['pyproject.toml']),'declared_outputs':list(decl),
        'environment':source.get('environment',b['environment']),'scm':source['scm']}
    require(all(b.get(k)==v for k,v in expected.items()),'generated evidence source/environment/SCM binding differs')
    wheel=evidence['wheel_evidence'];raw=a.read(wheel['wheel_path']);members=archive.wheel_members(raw)
    require(sha(raw)==wheel['wheel_sha256'] and fp({k:sha(v) for k,v in sorted(members.items())})==wheel['wheel_content_sha256'],
            'retained generated wheel bytes differ')
    output={p:members[p[4:] if p.startswith('src/') else p] for p in decl}
    require(evidence['generated_sha256']=={k:sha(v) for k,v in sorted(output.items())}
            and not set(output)&set(source['files']),'declared generated bytes overwrite source or differ')
    require(wheel['builder_sha256']==recipe['builder_sha256'] and wheel['build_recipe_sha256']==recipe['recipe_sha256'],
            'wheel builder/recipe differs')
    return output


def audit_native(a, case, setup, source, archive, runner):
    from research.unified_consequence_runtime import native_execution_v43 as worker
    contract,authority,policy=setup['contract'],setup['authority'],setup['policy']
    files=dict(source['files'],**source.get('generated',{}));manifest=source['manifest'];certificates={}
    for p in sorted(case.rglob('admission-certificate.json')):
        cert=a.js(p);require(cert['schema']=='UDM_NATIVE_ADMISSION_CERTIFICATE_V43','wrong certificate schema')
        expected={'contract_sha256':fp(contract),'authority_sha256':fp(authority),'policy_sha256':fp(policy),
            'runner_sha256':runner,'admission_revision':'4.3','status':'ADMITTED_NATIVE_COLLECTION'}
        require(all(cert.get(k)==v for k,v in expected.items()) and fp(cert['environment'])==contract['environment_sha256'],
                'certificate exact task/environment/policy replay')
        data,raw=packet(a,cert,p.parent);validate_context_bytes(data,files,authority['required_test_nodes'])
        for plugin in data['plugin_manifest']:
            validate_plugin_bytes(plugin,files,a.read)
        require(json.loads(raw['tracked-source-manifest.json'])==manifest,'certificate typed source manifest differs')
        require(data['mode']=='collect' and data['process_exit_code']==data['exit_code']==0 and not data['timeout']
            and data['costs']['native_calls']==0 and data['costs']['collection_calls']==1,'not authentic complete collection')
        require({k:data[k] for k in cert['collection']}==cert['collection'] and data['pytest_import']==cert['environment']['pytest_import'],
                'certificate actual collection or pytest bytes differ')
        require({k:cert['costs'][k] for k in data['costs']}==data['costs']
            and cert['costs']['horizon_seconds']==policy['collection_seconds']
            and number(cert['costs']['total_seconds']) and cert['costs']['total_seconds']>=data['costs']['seconds'],
            'certificate collection costs or horizon differ')
        certificates[fp(cert)]=cert
    receipts=[]
    for p in sorted(case.rglob('receipt.json')):
        value=a.js(p)
        if value.get('schema')!='UDM_GENERIC_NATIVE_PYTEST_V43':continue
        cert=certificates.get(value['certificate_sha256']);require(cert is not None,'native receipt lacks exact retained certificate')
        # This original helper is static accounting only: it does not call
        # _context, a target interpreter, a backend, collection or native replay.
        worker._validate_build_accounting(contract,value['independent_collection'])
        require(archive.receipt_identity_matches(value,contract,authority,policy,cert,{'replacements':[]},runner),
                'screening native receipt candidate/source/context differs')
        data,raw=packet(a,value,p.parent/'execution',True)
        try:validate_context_bytes(data,files,authority['required_test_nodes'])
        except ValueError:
            require(value['status'].startswith('UNKNOWN') and not setup.get('_eligible'),
                'identity/protected-suite violation cannot license admission')
        require(json.loads(raw['tracked-source-manifest.json'])==manifest,'run source manifest differs')
        counts=archive.junit(raw.get('native.xml'));status=archive.native_status(data,counts,cert['collection'])
        require(value['execution']==data and value['junit']==counts and value['status']==status,'raw native outcome differs')
        require(data['mode']=='run' and data['costs']['native_calls']==1 and data['costs']['collection_calls']==0,
                'native invocation/counters differ')
        recollect=Path(value['independent_collection']['output']);require(recollect.is_relative_to(case),'external recollection path')
        observed=a.js(recollect/'checked-report.json');validate_context_bytes(observed,files,authority['required_test_nodes'])
        require(observed['mode']=='collect' and observed['process_exit_code']==0
            and {k:observed[k] for k in cert['collection']}==cert['collection'],'independent exact collection differs')
        require(value['costs']['native_calls']==1 and value['costs']['collection_calls']==1
            and value['costs']['native_seconds']==data['costs']['seconds']
            and value['independent_collection']['costs']==observed['costs']
            and number(value['costs']['total_seconds']),'native receipt inclusive cost differs')
        receipts.append({'path':str(p),'status':status,'sha256':fp(value),'junit':counts,
            'execution_packet_sha256':sha(raw['checked-report.json'])})
        a.native.append(receipts[-1])
    if setup.get('_eligible'):
        require(len(certificates)==1 and len(receipts)==2,'admitted case needs retained producer and independent execution')
        require({row['path'] for row in receipts}=={str(case/'baseline/receipt.json'),str(case/'independent-baseline/receipt.json')},
            'admitted producer/reexecution are not the exact retained screening directories')
        require(receipts[0]['status']==receipts[1]['status'] in ('PASS_NATIVE','FAIL_NATIVE'),
                'producer/independent native verdict mismatch')
        validate_reexecution_pair(receipts)
    return certificates,receipts


def audit_partial_packets(a, case, report, source, archive):
    rows=[];totals={'native_calls':0,'collection_calls':0}
    expected=dict(source['files'],**source.get('generated',{})) if source else None
    for p in sorted(case.rglob('checked-report.json')):
        data=a.js(p);producer=a.js(p.with_name('report.json'))
        removed={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
        require(producer=={k:v for k,v in data.items() if k not in removed},'partial producer/checked report differs')
        costs=data['costs'];mode=data['mode'];require(mode in ('collect','run'),'unknown raw native phase')
        require(count(costs['native_calls'])==int(mode=='run') and count(costs['collection_calls'])==int(mode=='collect')
            and number(costs['seconds']),'partial raw launch costs differ')
        for key in totals:totals[key]+=costs[key]
        if expected is not None:
            require(a.js(p.with_name('tracked-source-manifest.json'))==source['manifest'],'partial packet source manifest differs')
            mismatch=[row for row in data.get('import_manifest',[]) if row.get('path') not in expected
                or row.get('sha256')!=sha(expected[row['path']])]
            require(not mismatch or data.get('unexpected_imports') or data.get('source_mutations'),
                'unreported wrong-byte partial import')
        xml=p.with_name('native.xml');counts=archive.junit(a.read(xml)) if xml.is_file() else None
        rows.append({'path':str(p),'sha256':sha(a.read(p)),'mode':mode,'costs':costs,
            'process_exit_code':data.get('process_exit_code'),'collection_errors':data.get('collection_errors'),
            'identity_violation_observed':bool(data.get('unexpected_imports') or data.get('source_mutations')
                or data.get('external_project_imports') or data.get('plugin_violations')),'junit':counts})
    require(all(totals[k]<=report['controller_attempts'][k] for k in totals),'raw launches exceed controller costs')
    return {'packets':rows,'raw_totals':totals,
        'controller_attempt_counts':report['controller_attempts'],
        'coverage':'Retained completed packets plus original controller launch-attempt counters; interrupted attempts may have no final packet. No missing packet licenses admission.'}


def audit_builds(a, case, report, archive, recipe, identity):
    before,after=(report['build_attempts'][k] for k in ('before','after'))
    paths=after['builder_attempts']['records'][len(before['builder_attempts']['records']):]
    calls=0;seconds=0;fingerprints=set()
    for name in paths:
        value=a.js(name);cost=value['costs'];calls+=count(cost['build_calls']);require(number(cost['build_seconds']),'invalid build time');seconds+=cost['build_seconds']
        require(cost['command_calls']==len(value['commands']),'build command cost count differs')
        if value['status']=='BUILT_NOT_SCIENTIFICALLY_VERIFIED':
            require(archive.authenticated_build_launch(value,recipe['builder_sha256'],recipe['recipe_sha256']),
                    'failed/forged build cannot warrant independent verification')
            wheel=value['generated_wheel_evidence'];raw=a.read(wheel['wheel_path']);members=archive.wheel_members(raw)
            require(sha(raw)==wheel['wheel_sha256'] and fp({k:sha(v) for k,v in sorted(members.items())})==wheel['wheel_content_sha256'],
                    'successful build wheel digest differs')
            native=next(row['argv'] for row in value['commands'] if row['phase']=='base-native-wheel')
            build_root=Path(native[-1]);base=identity.raw_snapshot(build_root,value['binding']['base_commit'])
            require(base['identity']==value['binding']['base_source'],'actual backend source commit/tree differs')
            for row in base['manifest']:
                path=build_root/row['path']
                if row['mode']=='120000':
                    require(path.is_symlink() and os.readlink(path)==row['target'],'backend changed original source alias')
                else:require(path.is_file() and not path.is_symlink() and path.read_bytes()==base['files'][row['path']]
                    and path.stat().st_mode&0o777==int(row['mode'],8)&0o777,'backend changed tracked original source/config/test bytes')
            fingerprints.add(fp(value))
        a.builds.append({'path':name,'sha256':fp(value),'status':value['status'],'costs':cost})
    require(calls==after['builder_attempts']['build_calls']-before['builder_attempts']['build_calls']
        and math.isclose(seconds,after['builder_attempts']['build_seconds']-before['builder_attempts']['build_seconds'],abs_tol=1e-8),
        'all successful/refused build launch costs must be retained')
    for p in case.rglob('verification.json'):
        v=a.js(p)
        if v.get('schema')!='UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43':continue
        if v['status']=='INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME':
            require(fp(v['build']) in fingerprints,'build verification lacks successful concrete launched build')
            expected=(report.get('setup',{}).get('contract') or {}).get('generated_build')
            require(v['binding']==v['build']['binding'] and (not expected or v['binding']==expected['binding']),
                'independent build binding differs')
    evidence=(report.get('setup',{}).get('contract') or {}).get('generated_build')
    if evidence:
        preparation=a.js(Path(evidence['preparation']['output'])/'build-receipt.json')
        require(fp(preparation) in fingerprints,'original generated preparation was not an actual successful measured launch')
        original=archive.wheel_members(a.read(evidence['wheel_evidence']['wheel_path']))
        for packet_path in case.rglob('checked-report.json'):
            sidecar=packet_path.parent/'generated-build-verification.json'
            require(sidecar.is_file() and a.js(sidecar)['status']=='VERIFIED_GENERATED_BUILD',
                'completed native packet lacks concrete generated-build sidecar')
        for p in case.rglob('generated-build-verification.json'):
            record=a.js(p)
            if record['status']=='VERIFIED_GENERATED_BUILD':
                require(record['native_output']==str(p.parent),'generated sidecar native output replay')
                verification=a.js(p.parent/'generated-build-verification/verification.json')
                validate_retained_build_sidecar(record,a.js(p),verification,fingerprints)
                rebuilt=archive.wheel_members(a.read(verification['build']['generated_wheel_evidence']['wheel_path']))
                validate_generated_link(evidence,preparation,verification,original,rebuilt)


def audit_ledger(a, case, spec, report, authority_sha):
    path=case/'machine-state/metatron-ledger.jsonl';require(path.is_file(),'screening lacks original Machine ledger')
    rows=[json.loads(line) for line in a.read(path).splitlines() if line.strip()];seen=set()
    for row in rows:
        body={k:row[k] for k in ('kind','payload','premises')}
        encoded=json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
        require(sha(encoded)==row['id'] and row['id'] not in seen,'Machine immutable ledger hash/duplicate differs');seen.add(row['id'])
    requests=[r for r in rows if r['kind']=='native_admission_request_v43' and r['payload'].get('spec_sha256')==fp(spec)
        and r['payload'].get('protocol_binding')==authority_sha]
    require(len(requests)==1,'external source obligation missing or duplicated')
    if report.get('setup',{}).get('materialization_binding'):
        binding=report['setup']['materialization_binding'];nodes={r['id']:r for r in rows}
        require(binding['capability_id'] in nodes and binding['consequence_id'] in nodes,'exact materialization witness absent')
    return {'records':len(rows),'admission_request':requests[0]['id']}


def raw_inventory(a, case):
    result=[]
    for path in sorted(case.rglob('*')):
        if path.is_symlink():
            result.append({'path':str(path),'kind':'symlink','target':os.readlink(path)})
        elif path.is_file():
            raw=path.read_bytes();result.append({'path':str(path),'kind':'file','bytes':len(raw),
                'sha256':sha(raw),'mode':path.stat().st_mode&0o777})
    return result


def check_cost_rows(a, value):
    if isinstance(value,list):
        for item in value:check_cost_rows(a,item)
    elif isinstance(value,dict):
        if 'seconds' in value:require(number(value['seconds']),'nonfinite/negative retained phase seconds')
        if 'log' in value and 'log_sha256' in value:
            require(sha(a.read(value['log']))==value['log_sha256'],'phase raw command log differs')
        for item in value.values():
            if isinstance(item,(dict,list)):check_cost_rows(a,item)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','records','requests','sealed','controller-manifest','attestation','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('authority-sha256','controller-manifest-sha256','attestation-sha256','source-commit','prequery-commit'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args();out=args.out.absolute();out.mkdir(parents=True,exist_ok=False)
    a=Audit();result=None
    try:
        for name,expected in json.loads((HERE/'AUDITOR_FREEZE.json').read_text())['source_files_sha256'].items():
            require(sha(Path(name).read_bytes())==expected,'frozen auditor/dependency source differs: '+name)
        for name,expected in json.loads((HERE/'TRUSTED_SOURCE_PINS.json').read_text()).items():
            require(sha(Path(name).read_bytes())==expected,'frozen audit/control source differs: '+name)
        archive=load_helper('original/archive_audit_v43.py');identity=load_helper('raw_identity.py')
        import sys
        sys.path.insert(0,str(args.repo.resolve()))
        from research.unified_consequence_runtime import native_build_v43 as builder
        runner=sha((args.repo/'research/unified_consequence_runtime/native_execution_v43.py').read_bytes())
        recipe={'builder_sha256':sha(Path(builder.__file__).read_bytes()),'recipe_sha256':fp(builder.BUILD_RECIPE)}
        rec=args.records.resolve();authority_path=rec/'SCREENING_AUTHORITY.json'
        require(HEX.fullmatch(args.authority_sha256) and sha(a.read(authority_path))==args.authority_sha256,'trusted screening authority pin differs')
        authority=a.js(authority_path);protocol=a.js(rec/'FRONTIER_PROTOCOL.json');pool=a.bound(authority['pool'],args.repo);pre=a.bound(authority['prequery'],args.repo)
        catalog=a.bound(protocol['catalog'],args.repo)
        require(authority['schema']=='UDM_NATIVE_CLI_AUTHORITY_V43' and authority['operation']=='screen'
            and authority['repo']==str(args.repo.resolve()) and authority['output_root']==str(args.sealed.resolve()),'wrong canonical screening authority')
        require(authority['pool']==protocol['pool'] and authority['prequery']==protocol['prequery'],'authority/protocol input chain differs')
        require(pre['source_commit']==args.prequery_commit,'wrong independently supplied prequery commit')
        plan=a.bound(pre['plan'],args.repo);metadata=a.js(rec/'METADATA_CURATION.json')
        metadata_summary=audit_metadata(plan,pre,metadata,pool)
        for key in ('environment_gate','interface_gate','interface_archive_audit'):
            require(authority[key]==protocol[key]==pre[key],'screening gate chain differs')
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1')
        p=subprocess.run(['git','--no-replace-objects','-C',str(args.repo),'rev-parse','HEAD'],env=env,capture_output=True)
        require(p.returncode==0 and p.stdout.decode().strip()==args.source_commit,'owned screening source commit differs')
        for path in (rec/'SCREENING_AUTHORITY.json',rec/'FRONTIER_PROTOCOL.json',rec/'FROZEN_POOL.json',rec/'PREQUERY_EXECUTION.json'):
            p=subprocess.run(['git','--no-replace-objects','-C',str(args.repo),'show',args.source_commit+':'+path.relative_to(args.repo).as_posix()],env=env,capture_output=True)
            require(p.returncode==0 and p.stdout==a.read(path),'screening input not exact committed bytes')
        for key in ('plan','code','gate_descriptor'):
            row=pre[key];p=subprocess.run(['git','--no-replace-objects','-C',str(args.repo),'show',args.prequery_commit+':'+row['path']],env=env,capture_output=True)
            require(row['source_commit']==args.prequery_commit and p.returncode==0 and sha(p.stdout)==row['sha256']
                and p.stdout==a.read(args.repo/row['path']),'generic committed prequery descriptor differs: '+key)
        controller=a.bound({'path':str(args.controller_manifest.resolve()),'sha256':args.controller_manifest_sha256})
        snapshot=a.bound(controller['source_snapshot'])
        require(snapshot['source_commit']==args.source_commit,'wrong controller source snapshot commit')
        p=subprocess.run(['git','--no-replace-objects','-C',str(args.repo),'ls-tree','-rz','--full-tree',args.source_commit],
            env=env,capture_output=True)
        require(p.returncode==0,'cannot read exact committed source inventory')
        committed={}
        for item in p.stdout.split(b'\0'):
            if not item:continue
            left,name=item.split(b'\t',1);mode,kind,oid=left.decode().split()
            require(kind=='blob','unsupported committed source topology')
            committed[name.decode()]={'mode':mode,'blob':oid}
        require(len(snapshot['files'])==len(committed) and {r['path'] for r in snapshot['files']}==set(committed),
            'source snapshot omits/duplicates committed tracked inputs')
        for row in snapshot['files']:
            path=args.repo/row['path']
            raw=os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
            mode='120000' if path.is_symlink() else '100755' if path.stat().st_mode&0o111 else '100644'
            oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            require(sha(raw)==row['sha256'] and mode==row['mode']==committed[row['path']]['mode']
                and oid==committed[row['path']]['blob'],'controller source bytes/mode changed: '+row['path'])
        attestation=a.bound({'path':str(args.attestation.resolve()),'sha256':args.attestation_sha256})
        require(attestation.get('independent_screener') is True and attestation.get('search_or_policy_outcomes_accessed') is False
            and attestation.get('learner_future_source_accessed') is False and attestation.get('native_test_reruns_or_case_retries_performed') is False,
            'bounded original screening actor exposure/once-only attestation missing')
        require(attestation['source_commit']==args.source_commit and attestation['authority_sha256']==args.authority_sha256,
            'screener exposure attestation is from another supplied run')
        require(controller['authority_sha256']==args.authority_sha256 and controller['source_commit']==args.source_commit
            and controller['completed'] is True and controller['retries_performed'] is False,'controller transport authority/incomplete/retry differs')
        specs=pool['pool'];meter=a.js(args.sealed/'SCREENING_METER.json');validate_meter(specs,meter,args.authority_sha256)
        require(not(args.sealed/'SCREENING_METER.lock').exists(),'active/abandoned screening lock')
        require(len(controller['cases'])==len(specs),'controller dropped fixed pool members')
        envelopes=[]
        for i,spec in enumerate(specs):
            case=args.sealed/('case-'+format(i,'03d'))
            try:
                inventory=raw_inventory(a,case)
                inventory_path=out/('case-'+format(i,'03d')+'-RAW_MANIFEST.json')
                inventory_path.write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
                request=a.js(args.requests/('request-'+format(i,'03d')+'.json'));validate_request(i,spec,request,args.authority_sha256)
                report=a.js(case/'SCREENING_CASE.json');envelope=a.js(case/'SCREENING_ENVELOPE.json');expected=public_fields(report)
                inventory_runtime=a.js(case.with_name(case.name+'.RUNTIME_INVENTORY.json'))
                require(fp(inventory_runtime)==meter['runtime_inventory_sha256'],'case runtime inventory differs from original meter')
                check_cost_rows(a,report.get('setup',{}).get('costs',[]));check_cost_rows(a,report.get('machine_costs',[]))
                expected['sealed_report']={'path':str(case/'SCREENING_CASE.json'),'sha256':sha(a.read(case/'SCREENING_CASE.json'))}
                require(envelope==expected,'sealed envelope/cost/status identity differs')
                require(report['repository']==spec['repo'] and report['spec_sha256']==fp(spec),'report task differs')
                require(meter['cases'][i]['report']==expected['sealed_report']
                    and meter['cases'][i]['costs']==report['controller_attempts'],'meter/report differs')
                entry=controller['cases'][i];require(entry['index']==i and entry['returncode']==0,'controller case order/exit differs')
                argv=entry['command'];require('--authority-sha256' in argv and argv[argv.index('--authority-sha256')+1]==args.authority_sha256
                    and '--out' in argv and argv[argv.index('--out')+1]==str(case),'controller launched different authority/output')
                if i:require(datetime.datetime.fromisoformat(entry['started_at_utc']).timestamp()>=datetime.datetime.fromisoformat(controller['cases'][i-1]['started_at_utc']).timestamp()+controller['cases'][i-1]['wall_seconds'],'overlapping/out-of-order screening launches')
                ledger=audit_ledger(a,case,spec,report,args.authority_sha256)
                audit_builds(a,case,report,archive,recipe,identity)
                setup=report.get('setup',{});closed={'source':'NOT_PREPARED','runtime':'NOT_PREPARED'}
                if setup.get('contract'):
                    require(setup['contract']['protocol_binding']==setup['authority']['protocol_binding']==args.authority_sha256,
                        'prepared native contract/authority replays another protocol invocation')
                    source=identity.audit_source(setup['contract'],setup['authority'],report.get('certificate'),case,include_scm=(setup['contract']['generated_build'] is not None))
                    require(source['coverage_complete'] and all(row['passed'] for row in source['checks']),'raw source identity audit incomplete')
                    require(setup['authority']['baseline_commit']==spec['base_commit'] and setup['contract']['repository']==spec['repo'],
                        'prepared source is not exact frozen PR base')
                    require(spec['head_commit'] not in source['object_ids'],'repaired author head present in native source object store')
                    transports=source['author_test_transports'];by_path={row['filename']:row for row in spec['files']}
                    validate_author_tests(spec,source)
                    for transport in transports:
                        row=transport['record'];require(row['path'] in by_path and row['git_blob']==by_path[row['path']]['sha'],
                            'author-test transport differs from frozen PR head blob')
                    runtime=identity.audit_runtime(setup['contract'],setup['policy'],setup['authority'],certificate=report.get('certificate'),case_dir=case)
                    require(runtime['coverage_complete'] and all(row['passed'] for row in runtime['checks']),'offline runtime identity audit incomplete')
                    profile=setup['selection']['selected_profile'];ident=profile['id']
                    require(profile in catalog['profiles'] and setup['runtime']==inventory_runtime['runtimes'][ident]
                        and runtime['environment']['runtime_identity']==setup['runtime']['identity'],
                        'actual prepared interpreter/stdlib differs from externally frozen selected profile')
                    pinned=a.js(case/'source-environment/pinned-package-files.json')
                    require(fp(pinned)==setup['pinned_packages_sha256'],'retained pinned package file inventory differs')
                    normalize=lambda name:re.sub(r'[-_.]+','-',name).lower()
                    pins={normalize(p.split('==')[0]):p.split('==')[1] for p in profile['packages']}
                    observed=sorted([[normalize(n),v,rows] for n,v,rows in runtime['distribution_files'] if normalize(n) in pins])
                    require(observed==pinned and {n:v for n,v,_ in observed}==pins,'actual installed original pinned package closure differs')
                    source['environment']=runtime['environment']
                    source['generated']=generated_files(a,setup['contract']['generated_build'],setup['contract'],setup['authority'],setup['policy'],source,archive,builder,recipe)
                    certificates,receipts=audit_native(a,case,dict(setup,_eligible=report['eligible']),source,archive,runner)
                    validate_native_disposition(report,receipts)
                    partial=audit_partial_packets(a,case,report,source,archive)
                    detail={'source':{k:v for k,v in source.items() if k not in ('files','base_files','generated')},
                        'runtime':runtime,'partial_packets':partial}
                    def json_safe(value):
                        if isinstance(value,bytes):return {'sha256':sha(value),'bytes':len(value)}
                        if isinstance(value,Path):return str(value)
                        if isinstance(value,dict):return {str(k):json_safe(v) for k,v in value.items()}
                        if isinstance(value,(tuple,list)):return [json_safe(v) for v in value]
                        return value
                    sidecar=out/('case-'+format(i,'03d')+'-RAW_IDENTITY.json');sidecar.write_text(json.dumps(json_safe(detail),indent=2,sort_keys=True,allow_nan=False)+'\n')
                    closed={'source':source['status'],'runtime':runtime['status'],'certificates':len(certificates),
                        'native_receipts':receipts,'raw_identity':{'path':str(sidecar),'sha256':sha(sidecar.read_bytes())}}
                else:
                    require(not report['eligible'],'admitted native case lacks prepared source contract')
                    closed['partial_packets']=audit_partial_packets(a,case,report,None,archive)
                    partial_sources=[]
                    for source_path in (case/'source-environment/metadata-source',case/'source-environment/native/source'):
                        if source_path.is_dir() and (source_path/'.git/HEAD').is_file():
                            head=(source_path/'.git/HEAD').read_text().strip()
                            if re.fullmatch('[0-9a-f]{40}',head):
                                snap=identity.raw_snapshot(source_path,head,filesystem=True)
                                require(snap['coverage_complete'] and all(r['passed'] for r in snap['checks']),
                                    'partial source raw identity differs')
                                partial_sources.append({'path':str(source_path),'commit':head,'identity':snap['identity']})
                    closed['partial_sources']=partial_sources
                envelopes.append(envelope);a.cases.append({'index':i,'eligible':report['eligible'],'status':report['status'],'identity':closed,'ledger':ledger,
                    'raw_manifest':{'path':str(inventory_path),'sha256':sha(inventory_path.read_bytes())}})
                a.check('case_complete:'+str(i),True)
            except Exception as error:
                a.check('case_complete:'+str(i),False,type(error).__name__+': '+str(error))
        require(len(envelopes)==len(specs),'one or more fixed screening cases unclosed')
        require(number(controller['wall_seconds']) and controller['wall_seconds']<=pool['screening_budget']['total_screening_wall_seconds']
            and sum(e['total_wall_seconds'] for e in envelopes)<=controller['wall_seconds'],
            'screening parent wall budget or inclusive nesting differs')
        a.check('all_pool_members_and_unknowns_closed',True)
        result={'status':'PASS_RETAINED_SCREENING_BINDINGS' if all(r['pass'] for r in a.checks) else 'UNKNOWN_RETAINED_SCREENING_BINDINGS',
            'pool_sha256':sha(a.read(args.repo/authority['pool']['path'])),'reports_sha256':fp(envelopes),'reports':envelopes,
            'cases':a.cases,'native':a.native,'builds':a.builds,'metadata_summary':metadata_summary,'source_commit':args.source_commit,
            'authority':{'path':str(authority_path),'sha256':args.authority_sha256},'controller':{'path':str(args.controller_manifest.resolve()),'sha256':args.controller_manifest_sha256},
            'attestation':{'path':str(args.attestation.resolve()),'sha256':args.attestation_sha256},
            'costs':{'native_calls':meter['native_calls'],'collection_calls':meter['collection_calls'],
                'build_calls':sum(e['build_costs']['build_calls'] for e in envelopes),'build_seconds':sum(e['build_costs']['build_seconds'] for e in envelopes),
                'verification_attempts':sum(e['build_costs']['verification_attempts'] for e in envelopes),
                'sum_case_inclusive_wall_seconds':sum(e['total_wall_seconds'] for e in envelopes),'controller_wall_seconds':controller['wall_seconds']}}
    except Exception as error:
        a.check('supplied_run_complete',False,type(error).__name__+': '+str(error));result={'status':'UNKNOWN_RETAINED_SCREENING_BINDINGS'}
    result.update(schema='UDM_V43_OFFLINE_RETAINED_SCREENING_DOSSIER_V1',checks=a.checks,inputs=a.inputs,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        limitations=['Bounded supplied-run/actor attestation; no global absence-of-unrelated-processes or hostile-host isolation proof.',
            'No target interpreter, backend, pytest or native verifier executed by this audit. Runtime implementation/version claims retain offline evidence limits.',
            'Inclusive parent and nested phase wall intervals are nonadditive. All successful/refused launches retained; unmeasured tool/model/engineering/lifecycle cost remains UNKNOWN.'],
        scientific_verdicts={'G'+str(i):'UNKNOWN' for i in range(2,7)})
    (out/'RETAINED_CHECKS.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(canonical({'status':result['status'],'output':str(out/'RETAINED_CHECKS.json')}))


if __name__=='__main__':main()
